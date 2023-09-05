"""Tests for pyonwater meter"""


from aiohttp import web
from conftest import (
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_historical_data_newer_data_endpoint,
    mock_historical_data_newerdata_moredata_endpoint,
    mock_historical_data_nodata_endpoint,
    mock_read_meter_endpont,
    mock_signin_enpoint,
)
import pytest

from pyonwater import (
    Account,
    Client,
    EyeOnWaterAPIError,
    EyeOnWaterException,
    Meter,
    MeterReader,
)


@pytest.mark.parametrize(
    "metric,expected_units",
    [
        (False, "gal"),
        (True, "m\u00b3"),
    ],
)
async def test_meter_expected_units(aiohttp_client, loop, metric, expected_units):
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

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
    metric = False

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_nodata_endpoint
    )

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

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_newer_data_endpoint
    )

    websession = await aiohttp_client(app)

    client = await build_client(websession, metric)

    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_newerdata_moredata_endpoint,
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
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpont, units),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, units),
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
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpont)
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, units),
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
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_enpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpont, units),
    )
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

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
