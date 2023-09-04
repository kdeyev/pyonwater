"""Tests for pyonwater meter reader"""

from aiohttp import web

from pyonwater import Account, Client, MeterReader


async def mock_signin(request):
    """Mock for sign in HTTP call"""
    resp = web.Response(text="Hello, world", headers={"cookies": "key=val"})
    return resp


def mock_read_meter(request):
    """Mock for read meter request"""
    with open("tests//mock/read_meter_mock.json") as f:
        return web.Response(text=f.read())


# @pytest.mark.asyncio
async def test_meter_reader(aiohttp_client, loop):
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)

    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=False,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=True,
    )

    meter_info = await meter_reader.read_meter(client=client)
    assert meter_info.reading.latest_read.full_read != 0
