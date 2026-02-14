"""Tests for pyonwater client."""

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


async def test_client(aiohttp_client, loop):
    """Basic client test."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/dashboard/user", mock_get_meters_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    meters = await account.fetch_meters(client=client)
    assert len(meters) == 1


async def test_client_403(aiohttp_client, loop):
    """Test handling rate limit errors during authentication."""
    app = web.Application()
    app.router.add_post(
        "/account/signin",
        add_error_decorator(mock_signin_endpoint, 403),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterRateLimitError):
        await client.authenticate()

    assert client.authenticated is False


async def test_client_400(aiohttp_client, loop):
    """Test handling Auth errors during authentication."""
    app = web.Application()
    app.router.add_post(
        "/account/signin",
        add_error_decorator(mock_signin_endpoint, 400),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterAuthError):
        await client.authenticate()

    assert client.authenticated is False


async def test_client_data_403(aiohttp_client, loop):
    """Test handling rate limit errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 403),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    with pytest.raises(EyeOnWaterRateLimitError):
        await account.fetch_meters(client=client)


async def test_client_data_401(aiohttp_client, loop):
    """Test handling token expiration errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 401),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    # fetch will reauthenticate and retry
    await account.fetch_meters(client=client)


async def test_client_data_404(aiohttp_client, loop):
    """Test handling 404 errors."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get(
        "/dashboard/user",
        add_error_decorator(mock_get_meters_endpoint, 404),
    )
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    with pytest.raises(EyeOnWaterException):
        await account.fetch_meters(client=client)


async def test_client_missing_meter_uuid(aiohttp_client, loop):
    """Test handling response with missing meter_uuid field."""

    def mock_get_meters_no_uuid(request):
        data = """  AQ.Views.MeterPicker.meters = [{"display_address": "", "meter_id": "456", "city": "", "location_name": "", "has_leak": false, "state": "", "serial_number": "789", "utility_uuid": "123", "page": 1, "zip_code": ""}];
            junk"""
        return web.Response(text=data)

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/dashboard/user", mock_get_meters_no_uuid)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    with pytest.raises(EyeOnWaterAPIError):
        await account.fetch_meter_readers(client=client)
