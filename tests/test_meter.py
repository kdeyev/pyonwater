"""Tests for pyonwater meter"""


from aiohttp import web
from conftest import (
    build_client,
    build_data_endpoint,
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
import pytest

from pyonwater import EyeOnWaterAPIError, EyeOnWaterException, Meter, MeterReader

"""Mock for historical data request, but no actual data"""
mock_historical_data_nodata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_nodata"
)

"""Mock for historical data request, but newer data"""
mock_historical_data_newer_data_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data"
)

"""Mock for historical data request, but newer and more data"""
mock_historical_data_newerdata_moredata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data_moredata"
)


@pytest.mark.parametrize(
    "metric,expected_units",
    [
        (False, "gal"),
        (True, "m\u00b3"),
    ],
)
async def test_meter_expected_units(aiohttp_client, loop, metric, expected_units):
    """Test meter returns expected units"""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession, metric=metric)

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)

    assert meter.meter_id is not None
    assert meter.meter_uuid is not None

    assert meter.native_unit_of_measurement == expected_units


async def test_meter(aiohttp_client, loop):
    """Basic meter test"""
    metric = False

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_nodata_endpoint
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession, metric=metric)
    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=metric,
    )
    meter = Meter(meter_reader)

    # Access meter before reading
    with pytest.raises(EyeOnWaterException):
        assert meter.reading
    with pytest.raises(EyeOnWaterException):
        assert meter.meter_info

    # Read meter with no historical data
    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)
    account, client = await build_client(websession, metric=metric)

    # Read meter with some historical
    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_newer_data_endpoint
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession, metric=metric)

    # Read meter with newer historical
    await meter.read_meter(client=client, days_to_load=1)
    assert meter.reading != 0
    assert meter.meter_info is not None

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_newerdata_moredata_endpoint,
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession, metric=metric)

    # Read meter with more historical
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
    """Test handling data with different units"""

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, units),
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession, metric=metric)

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
    """Test handling data with different units of historical data"""

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, units),
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession, metric=metric)

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
    """Test handling data with different units of reading"""

    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession, metric=metric)

    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=account.metric_measurement_system,
    )

    meter = Meter(meter_reader)
    with pytest.raises(EyeOnWaterAPIError):
        await meter.read_meter(client=client)
        assert meter.reading != 0
