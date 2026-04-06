"""Tests for pyonwater client."""  # nosec: B101, B106

from typing import Any

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
