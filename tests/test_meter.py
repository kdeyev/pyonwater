"""Tests for pyonwater meter reader"""

import json
from typing import Any

from aiohttp import web
import pytest

from pyonwater import (
    Account,
    Client,
    EyeOnWaterAPIError,
    EyeOnWaterException,
    Meter,
    MeterReader,
)
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


def mock_historical_data(request):
    """Mock for historical datas request"""
    with open("tests//mock/historical_data_mock_anonymized.json") as f:
        return web.Response(text=f.read())


def mock_historical_nodata(request):
    """Mock for historical datas request"""
    with open("tests//mock/historical_data_mock_anonymized_nodata.json") as f:
        return web.Response(text=f.read())


def mock_historical_newerdata(request):
    """Mock for historical datas request"""
    with open("tests//mock/historical_data_mock_anonymized_newer_data.json") as f:
        return web.Response(text=f.read())


def mock_historical_newerdata_moredata(request):
    """Mock for historical datas request"""
    with open(
        "tests//mock/historical_data_mock_anonymized_newer_data_moredata.json"
    ) as f:
        return web.Response(text=f.read())


def mock_read_meter_custom_units(new_unit):
    def mock_read_meter(request):
        """Mock for read meter request"""
        with open("tests//mock/read_meter_mock_anonymized.json") as f:
            data = json.load(f)
            data = replace_units(data, new_unit)
            return web.Response(text=json.dumps(data))

    return mock_read_meter


def mock_historical_data_custom_units(new_unit):
    def mock_read_meter(request):
        """Mock for read meter request"""
        with open("tests//mock/historical_data_mock_anonymized.json") as f:
            data = json.load(f)
            data = replace_units(data, new_unit)
            return web.Response(text=json.dumps(data))

    return mock_read_meter


@pytest.mark.parametrize(
    "metric,expected_units",
    [
        (False, "gal"),
        (True, "m\u00b3"),
    ],
)
async def test_meter_expected_units(aiohttp_client, loop, metric, expected_units):
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
        metric_measurement_system=metric,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)

    assert meter.meter_id is not None
    assert meter.meter_uuid is not None

    assert meter.native_unit_of_measurement == expected_units


async def build_client(websession, metric):
    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=metric,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()
    return client


async def test_meter(aiohttp_client, loop):
    """Basic pyonwater meter reader test"""
    metric = False

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post("/api/2/residential/consumption", mock_historical_nodata)

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=metric,
    )

    meter = Meter(meter_reader)

    with pytest.raises(EyeOnWaterException):
        assert meter.reading

    with pytest.raises(EyeOnWaterException):
        assert meter.meter_info

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data)

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post("/api/2/residential/consumption", mock_historical_newerdata)

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_newerdata_moredata
    )

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None


@pytest.mark.parametrize(
    "metric,units",
    [
        (False, "GAL"),
        (False, "100 GAL"),
        (False, "10 GAL"),
        (False, "CF"),
        (False, "CCF"),
        (False, "KGAL"),
        (False, "CUBIC_FEET"),
        (True, "CM"),
        (True, "CUBIC_METER"),
    ],
)
async def test_meter_units(aiohttp_client, loop, metric, units):
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_custom_units(units)
    )
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_custom_units(units)
    )

    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=metric,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)
    await meter.read_meter(client=client)

    assert meter.reading != 0
    assert meter.meter_id is not None
    assert meter.meter_uuid is not None
    assert meter.meter_info is not None


@pytest.mark.parametrize(
    "metric,units",
    [
        (True, "GAL"),
        (True, "100 GAL"),
        (True, "10 GAL"),
        (True, "CF"),
        (True, "CCF"),
        (True, "KGAL"),
        (True, "CUBIC_FEET"),
        (False, "CM"),
        (False, "CUBIC_METER"),
    ],
)
async def test_meter_wrong_unit_historical_data(aiohttp_client, loop, metric, units):
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_custom_units(units)
    )

    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=metric,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)
    with pytest.raises(EyeOnWaterAPIError):
        await meter.read_meter(client=client)


@pytest.mark.parametrize(
    "metric,units",
    [
        (True, "GAL"),
        (True, "100 GAL"),
        (True, "10 GAL"),
        (True, "CF"),
        (True, "CCF"),
        (True, "KGAL"),
        (True, "CUBIC_FEET"),
        (False, "CM"),
        (False, "CUBIC_METER"),
    ],
)
async def test_meter_wrong_unit_reading(aiohttp_client, loop, metric, units):
    """Basic pyonwater meter reader test"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_custom_units(units)
    )
    app.router.add_post("/api/2/residential/consumption", mock_historical_data)

    websession = await aiohttp_client(app)

    account = Account(
        eow_hostname="",
        username="user",
        password="",
        metric_measurement_system=metric,
    )

    client = Client(websession=websession, account=account)
    await client.authenticate()

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)
    with pytest.raises(EyeOnWaterAPIError):
        await meter.read_meter(client=client)
        assert meter.reading != 0
