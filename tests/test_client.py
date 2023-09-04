"""Tests for pyonwater client"""

from aiohttp import web

from pyonwater import Account, Client


async def mock_signin(request):  # type: ignore
    """Mock for sign in HTTP call"""
    resp = web.Response(text="Hello, world", headers={"cookies": "key=val"})
    return resp


def mock_get_meters(request):  # type: ignore
    """Mock for get dashboard request"""
    data = """  AQ.Views.MeterPicker.meters = [{"display_address": "", "": "", "meter_uuid": "123", "meter_id": "456", "city": "", "location_name": "", "has_leak": false, "state": "", "serial_number": "789", "utility_uuid": "123", "page": 1, "zip_code": ""}];
            junk"""

    return web.Response(text=data)


# @pytest.mark.asyncio
async def test_client(aiohttp_client, loop):  # type: ignore
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
    meters = await account.fetch_meters(client=client)
    assert len(meters) == 1
