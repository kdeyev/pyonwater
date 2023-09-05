"""Tests for pyonwater meter reader"""


from aiohttp import web
from conftest import (
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_read_meter_endpont,
    mock_signin_enpoint,
)
import pytest

from pyonwater import Account, Client, EyeOnWaterAPIError, MeterReader


async def test_meter_reader(aiohttp_client, loop):
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

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
        metric_measurement_system=account.metric_measurement_system,
    )

    meter_info = await meter_reader.read_meter(client=client)
    assert meter_info.reading.latest_read.full_read != 0

    await meter_reader.read_historical_data(client=client, days_to_load=1)


async def test_meter_reader_wrong_units(aiohttp_client, loop):
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpont, "hey"),
    )
    # app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

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
        metric_measurement_system=account.metric_measurement_system,
    )

    with pytest.raises(EyeOnWaterAPIError):
        await meter_reader.read_meter(client=client)
