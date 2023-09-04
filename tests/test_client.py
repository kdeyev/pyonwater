"""Tests for pyonwater client"""

from aiohttp import web
import pytest

from pyonwater import (
    Account,
    Client,
    EyeOnWaterAuthError,
    EyeOnWaterException,
    EyeOnWaterRateLimitError,
)


async def mock_signin(request):
    """Mock for sign in HTTP call"""
    resp = web.Response(text="Hello, world", headers={"cookies": "key=val"})
    return resp


def mock_get_meters(request):
    """Mock for get dashboard request"""
    data = """  AQ.Views.MeterPicker.meters = [{"display_address": "", "": "", "meter_uuid": "123", "meter_id": "456", "city": "", "location_name": "", "has_leak": false, "state": "", "serial_number": "789", "utility_uuid": "123", "page": 1, "zip_code": ""}];
            junk"""

    return web.Response(text=data)


def mock_error_response(code: int, func):
    """Mock error response"""

    counter = 0

    def mock(request):
        nonlocal counter
        if counter == 0:
            counter += 1
            return web.Response(status=code)
        else:
            return func(request)

    return mock


async def test_client(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin)
    app.router.add_get("/dashboard/user", mock_get_meters)
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    meters = await account.fetch_meters(client=client)
    assert len(meters) == 1


async def test_client_403(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_error_response(403, mock_signin))
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterRateLimitError):
        await client.authenticate()

    assert client.authenticated is False


async def test_client_400(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_error_response(400, mock_signin))
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    with pytest.raises(EyeOnWaterAuthError):
        await client.authenticate()

    assert client.authenticated is False


async def test_client_data_403(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin)
    app.router.add_get("/dashboard/user", mock_error_response(403, mock_get_meters))
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    with pytest.raises(EyeOnWaterRateLimitError):
        await account.fetch_meters(client=client)


async def test_client_data_401(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin)
    app.router.add_get("/dashboard/user", mock_error_response(401, mock_get_meters))
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    await account.fetch_meters(client=client)


async def test_client_data_404(aiohttp_client, loop):
    """Basic pyonwater client test"""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin)
    app.router.add_get("/dashboard/user", mock_error_response(404, mock_get_meters))
    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    assert client.authenticated is True

    with pytest.raises(EyeOnWaterException):
        await account.fetch_meters(client=client)
