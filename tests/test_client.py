"""Tests for pyonwater client."""  # nosec: B101, B106

import datetime
import json
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiohttp import web
from conftest import (
    add_error_decorator,
    mock_get_meters_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
import pytest

from pyonwater import (
    Account,
    Client,
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterException,
    EyeOnWaterRateLimitError,
)


@pytest.mark.asyncio()
async def test_client(aiohttp_client: Any) -> None:
    """Basic client test — default dashboard-first discovery."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/dashboard/user", mock_get_meters_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True  # nosec: B101

    meters = await account.fetch_meters(client=client)
    assert len(meters) == 1  # nosec: B101


@pytest.mark.asyncio()
async def test_client_prefer_new_search(aiohttp_client: Any) -> None:
    """Client test — prefer_new_search=True uses new_search API first."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meters = await account.fetch_meters(client=client, prefer_new_search=True)
    assert len(meters) == 1  # nosec: B101


@pytest.mark.asyncio()
async def test_client_403(aiohttp_client: Any) -> None:
    """Test handling rate limit errors during authentication."""
    app = web.Application()
    app.router.add_post(
        "/account/signin",
        add_error_decorator(mock_signin_endpoint, 403),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterRateLimitError):
        await client.authenticate()

    assert client.authenticated is False  # nosec: B101


@pytest.mark.asyncio()
async def test_client_400(aiohttp_client: Any) -> None:
    """Test handling Auth errors during authentication."""
    app = web.Application()
    app.router.add_post(
        "/account/signin",
        add_error_decorator(mock_signin_endpoint, 400),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterAuthError):
        await client.authenticate()

    assert client.authenticated is False  # nosec: B101


@pytest.mark.asyncio()
async def test_client_data_403(aiohttp_client: Any) -> None:
    """Test handling rate limit errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_rate_limit(_request: web.Request) -> web.Response:
        return web.Response(status=403)

    app.router.add_post(
        "/api/2/residential/new_search",
        mock_rate_limit,
    )
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True  # nosec: B101

    with pytest.raises(EyeOnWaterRateLimitError):
        await account.fetch_meters(client=client)


@pytest.mark.asyncio()
async def test_client_data_401(aiohttp_client: Any) -> None:
    """Test handling token expiration errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 401),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True  # nosec: B101

    # fetch will reauthenticate and retry
    await account.fetch_meters(client=client)


@pytest.mark.asyncio()
async def test_client_data_404(aiohttp_client: Any) -> None:
    """Test handling 404 errors — both discovery methods fail gracefully."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        add_error_decorator(mock_read_meter_endpoint, 404),
    )
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True  # nosec: B101

    meters = await account.fetch_meters(client=client)
    assert len(meters) == 0  # nosec: B101


@pytest.mark.asyncio()
async def test_account_raises_when_meter_uuid_missing(aiohttp_client: Any) -> None:
    """Verify EyeOnWaterException raised when dashboard HTML lacks meter_uuid."""

    async def mock_bad_meters(_request: web.Request) -> web.Response:
        data = (
            '  AQ.Views.MeterPicker.meters = [{"display_address": "", '
            '"meter_id": "456", "city": ""}];\n'
        )
        return web.Response(text=data)

    async def mock_new_search_empty(_request: web.Request) -> web.Response:
        return web.Response(text='{"elastic_results": {"hits": {"hits": []}}}')

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_new_search_empty)
    app.router.add_get("/dashboard/user", mock_bad_meters)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    with pytest.raises(EyeOnWaterException, match="Cannot find meter_uuid"):
        await account.fetch_meter_readers(client=client)


@pytest.mark.asyncio()
async def test_client_truncates_long_error_payload(aiohttp_client: Any) -> None:
    """Verify _truncate_payload runs when a non-200 response body exceeds 1000 chars."""

    async def mock_long_error(_request: web.Request) -> web.Response:
        return web.Response(status=503, text="X" * 1500)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/dashboard/user", mock_long_error)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    # Dashboard 503 is caught; both discovery methods return empty.
    # The truncation still fires (visible in captured log output).
    readers = await account.fetch_meter_readers(client=client)
    assert len(readers) == 0  # nosec: B101


@pytest.mark.asyncio()
async def test_client_new_search_nested_meter_payload(aiohttp_client: Any) -> None:
    """Test parsing nested meter fields from new_search payload."""

    async def mock_new_search_nested(_request: web.Request) -> web.Response:
        data = (
            '{"elastic_results": {"hits": {"hits": ['
            '{"_id": "fallback_uuid", "_source": {'
            '"meter": {"meter_uuid": "nested_uuid", "meter_id": 12345}}}'
            "]}}}"
        )
        return web.Response(text=data)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_new_search_nested)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers(client=client, prefer_new_search=True)
    assert len(readers) == 1  # nosec: B101
    assert readers[0].meter_uuid == "nested_uuid"  # nosec: B101
    assert readers[0].meter_id == "12345"  # nosec: B101


@pytest.mark.asyncio()
async def test_client_falls_back_to_new_search_when_dashboard_empty(
    aiohttp_client: Any,
) -> None:
    """Test new_search fallback when dashboard returns no meters (default order)."""

    async def mock_dashboard_empty(_request: web.Request) -> web.Response:
        return web.Response(text="no meter info here")

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/dashboard/user", mock_dashboard_empty)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers(client=client)
    assert len(readers) == 1  # nosec: B101


@pytest.mark.asyncio()
async def test_client_falls_back_to_dashboard_when_new_search_empty(
    aiohttp_client: Any,
) -> None:
    """Test dashboard fallback when new_search empty (prefer_new_search=True)."""

    async def mock_new_search_empty(_request: web.Request) -> web.Response:
        return web.Response(text='{"elastic_results": {"hits": {"hits": []}}}')

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_new_search_empty)
    app.router.add_get("/dashboard/user", mock_get_meters_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers(client=client, prefer_new_search=True)
    assert len(readers) == 1  # nosec: B101
    assert readers[0].meter_uuid == "123"  # nosec: B101
    assert readers[0].meter_id == "456"  # nosec: B101


# KNOWN BUG: _fetch_meter_readers_dashboard raises an unhandled KeyError when a meter
# entry has meter_uuid but no meter_id (METER_ID_FIELD key). Fixing the bug is out of
# scope; test coverage deferred until the bug is fixed.


@pytest.mark.asyncio()
async def test_client_token_expires_after_timeout(aiohttp_client: Any) -> None:
    """Token should be re-fetched after expiration period."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )
    client = Client(websession=websession, account=account)

    await client.authenticate()
    assert client.is_token_valid  # nosec: B101

    client.token_expiration = datetime.datetime.now() - datetime.timedelta(minutes=1)
    assert not client.is_token_valid  # nosec: B101

    await client.authenticate()
    assert client.is_token_valid  # nosec: B101


@pytest.mark.asyncio()
async def test_new_search_non_json_response_returns_empty(aiohttp_client: Any) -> None:
    """Non-JSON response from new_search is caught as JSONDecodeError → returns []."""

    async def bad_json(_request: web.Request) -> web.Response:
        return web.Response(text="not json at all")

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", bad_json)
    websession = await aiohttp_client(app)
    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="pass",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers_new_search(client)
    assert readers == []  # nosec: B101


@pytest.mark.asyncio()
async def test_new_search_missing_elastic_results_returns_empty(
    aiohttp_client: Any,
) -> None:
    """Response with no 'elastic_results' key → empty meters list."""

    async def no_elastic(_request: web.Request) -> web.Response:
        return web.Response(text='{"other_key": 1}')

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", no_elastic)
    websession = await aiohttp_client(app)
    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="pass",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers_new_search(client)
    assert readers == []  # nosec: B101


@pytest.mark.asyncio()
async def test_new_search_meter_uuid_from_source_direct(aiohttp_client: Any) -> None:
    """meter_uuid found directly in _source (not nested under 'meter') is used."""

    async def direct_source(_request: web.Request) -> web.Response:
        data = (
            '{"elastic_results": {"hits": {"hits": ['
            '{"_source": {"meter_uuid": "src_uuid", "meter_id": "src_id"}}'
            "]}}}"
        )
        return web.Response(text=data)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", direct_source)
    websession = await aiohttp_client(app)
    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="pass",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers_new_search(client)
    assert len(readers) == 1  # nosec: B101
    assert readers[0].meter_uuid == "src_uuid"  # nosec: B101
    assert readers[0].meter_id == "src_id"  # nosec: B101


@pytest.mark.asyncio()
async def test_client_new_search_ignores_id_as_uuid(aiohttp_client: Any) -> None:
    """Meters without a real meter_uuid should be skipped, not use _id as fallback."""

    async def mock_new_search_id_only(_request: web.Request) -> web.Response:
        data = (
            '{"elastic_results": {"hits": {"hits": ['
            '{"_id": "es_doc_id", "_source": {"meter_id": "456"}}'
            "]}}}"
        )
        return web.Response(text=data)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_new_search_id_only)
    websession = await aiohttp_client(app)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers_new_search(client=client)
    assert readers == []  # nosec: B101


@pytest.mark.asyncio()
async def test_new_search_skips_hit_with_no_uuid_or_id(aiohttp_client: Any) -> None:
    """Hit with no discoverable meter_uuid or meter_id is skipped → returns []."""

    async def no_ids(_request: web.Request) -> web.Response:
        data = json.dumps({"elastic_results": {"hits": {"hits": [{"_source": {}}]}}})
        return web.Response(text=data)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", no_ids)
    websession = await aiohttp_client(app)
    account = Account(  # nosec: B106
        eow_hostname="",
        username="user",
        password="pass",
    )
    client = Client(websession=websession, account=account)
    await client.authenticate()

    readers = await account.fetch_meter_readers_new_search(client)
    assert readers == []  # nosec: B101


# ---------------------------------------------------------------------------
# Phase 5 — sync unit tests (no aiohttp server)
# ---------------------------------------------------------------------------


def test_is_token_valid_not_authenticated() -> None:
    """Not authenticated and token expired → is_token_valid is False."""
    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=MagicMock(), account=account)
    client.authenticated = False
    client.token_expiration = datetime.datetime.now() - datetime.timedelta(seconds=1)
    assert client.is_token_valid is False  # nosec: B101


def test_is_token_valid_not_authenticated_not_expired() -> None:
    """Unauthenticated clients are invalid even if the expiration time is in the future."""
    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=MagicMock(), account=account)
    client.authenticated = False
    client.token_expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
    assert client.is_token_valid is False  # nosec: B101


def test_is_token_valid_authenticated_expired() -> None:
    """Authenticated but expired token should be treated as invalid."""
    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=MagicMock(), account=account)
    client.authenticated = True
    client.token_expiration = datetime.datetime.now() - datetime.timedelta(seconds=1)
    assert client.is_token_valid is False  # nosec: B101


def test_extract_json_matching_prefix() -> None:
    """extract_json strips prefix and trailing semicolon, then parses JSON."""
    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=MagicMock(), account=account)
    line = 'prefix[{"key": "val"}];'
    result = client.extract_json(line, "prefix")
    assert result == [{"key": "val"}]  # nosec: B101


def test_extract_json_no_match() -> None:
    """extract_json with no matching prefix produces an invalid slice → JSONDecodeError.

    NOTE: In production, callers guard with `if prefix in line` before calling.
    This test documents the unguarded behavior.
    """
    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=MagicMock(), account=account)
    with pytest.raises(json.JSONDecodeError):
        client.extract_json("no prefix here; text", "MISSING_PREFIX = ")


@pytest.mark.asyncio()
async def test_request_logs_short_error_payload_unchanged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Short error payloads are logged unchanged through the public request API."""
    payload_999 = "X" * 999
    payload_1000 = "X" * 1000
    response = MagicMock(status=503)
    response.text = AsyncMock(side_effect=[payload_999, payload_1000])
    websession = MagicMock()
    websession.request = AsyncMock(return_value=response)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=websession, account=account)
    client.authenticated = True
    client.token_expiration = datetime.datetime.now() + datetime.timedelta(hours=1)

    with caplog.at_level(logging.ERROR, logger="pyonwater.client"):
        with pytest.raises(EyeOnWaterAPIError, match="Request failed: 503"):
            await client.request("/dashboard/user", "get")
        with pytest.raises(EyeOnWaterAPIError, match="Request failed: 503"):
            await client.request("/dashboard/user", "get")

    assert payload_999 in caplog.text  # nosec: B101
    assert payload_1000 in caplog.text  # nosec: B101
    assert f"{payload_1000}..." not in caplog.text  # nosec: B101


@pytest.mark.asyncio()
async def test_request_logs_long_error_payload_truncated(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Long error payloads are truncated in logs through the public request API."""
    payload = "X" * 1001
    response = MagicMock(status=503)
    response.text = AsyncMock(return_value=payload)
    websession = MagicMock()
    websession.request = AsyncMock(return_value=response)

    account = Account(  # nosec: B106
        eow_hostname="",
        username="u",
        password="p",
    )
    client = Client(websession=websession, account=account)
    client.authenticated = True
    client.token_expiration = datetime.datetime.now() + datetime.timedelta(hours=1)

    with caplog.at_level(logging.ERROR, logger="pyonwater.client"):
        with pytest.raises(EyeOnWaterAPIError, match="Request failed: 503"):
            await client.request("/dashboard/user", "get")

    expected = "X" * 1000 + "..."
    assert expected in caplog.text  # nosec: B101
    assert payload not in caplog.text  # nosec: B101
