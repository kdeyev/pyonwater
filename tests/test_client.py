"""Tests for pyonwater client."""  # nosec: B101, B106

from typing import Any

from aiohttp import web
import pytest

from conftest import (
    add_error_decorator,
    mock_get_meters_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)

from pyonwater import (
    Account,
    Client,
    EyeOnWaterAuthError,
    EyeOnWaterException,
    EyeOnWaterRateLimitError,
)


@pytest.mark.asyncio()
async def test_client(aiohttp_client: Any) -> None:
    """Basic client test."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_get("/dashboard/user", mock_get_meters_endpoint)  # type: ignore
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
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
    assert len(meters) == 1  # nosec: B101


@pytest.mark.asyncio()
async def test_client_403(aiohttp_client: Any) -> None:
    """Test handling rate limit errors during authentication."""
    app = web.Application()
    app.router.add_post(
        "/account/signin",
        add_error_decorator(mock_signin_endpoint, 403),  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
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
        add_error_decorator(mock_signin_endpoint, 400),  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
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
    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 403),  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
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
    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 401),  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
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

    # fetch will reauthenticate and retry
    await account.fetch_meters(client=client)


@pytest.mark.asyncio()
async def test_client_data_404(aiohttp_client: Any) -> None:
    """Test handling 404 errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 404),  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
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

    with pytest.raises(EyeOnWaterException):
        await account.fetch_meters(client=client)
