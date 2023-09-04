"""Tests for pyonwater meter reader"""

import json
from typing import Any

from aiohttp import web
import pytest

from pyonwater import Account, Client, EyeOnWaterAPIError, MeterReader
from pyonwater.models import EOWUnits


def is_unit(string: str) -> bool:
    """Verify is the string is pyonwater supported measurement unit"""
    try:
        EOWUnits(string)
        return True
    except ValueError:
        return False


def replace_units(data: Any, new_unit: str) -> Any:
    """Anonymize an entity"""
    if isinstance(data, dict):
        for k in data:
            data[k] = replace_units(data[k], new_unit)
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = replace_units(data[i], new_unit)
        return data
    elif is_unit(data):
        return new_unit
    else:
        return data


async def mock_signin(request):
    """Mock for sign in HTTP call"""
    resp = web.Response(text="Hello, world", headers={"cookies": "key=val"})
    return resp


def mock_read_meter(request):
    """Mock for read meter request"""
    with open("tests//mock/read_meter_mock_anonymized.json") as f:
        return web.Response(text=f.read())


def mock_read_meter_custom_units(new_unit):
    def mock_read_meter(request):
        """Mock for read meter request"""
        with open("tests//mock/read_meter_mock_anonymized.json") as f:
            data = json.load(f)
            data = replace_units(data, new_unit)
            return web.Response(text=json.dumps(data))

    return mock_read_meter


def mock_historical_data(request):
    """Mock for historical datas request"""
    with open("tests//mock/historical_data_mock_anonymized.json") as f:
        return web.Response(text=f.read())


async def test_meter_reader(aiohttp_client, loop):
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data)

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
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_custom_units("hey")
    )
    # app.router.add_post("/api/2/residential/consumption", mock_historical_data)

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
