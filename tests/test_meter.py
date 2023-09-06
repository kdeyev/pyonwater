"""Tests for pyonwater meter."""


from aiohttp import web
from conftest import (
    build_client,
    build_data_endpoint,
    build_meter,
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
import pytest

from pyonwater import EOWUnits, EyeOnWaterUnitError, NativeUnits

"""Mock for historical data request, but no actual data"""
mock_historical_data_nodata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_nodata",
)

"""Mock for historical data request, but newer data"""
mock_historical_data_newer_data_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data",
)

"""Mock for historical data request, but newer and more data"""
mock_historical_data_newerdata_moredata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data_moredata",
)


@pytest.mark.parametrize(
    "units,expected_native_unit,expected_factor",
    [
        (EOWUnits.UNIT_GAL, NativeUnits.gal, 1),
        (EOWUnits.UNIT_100_GAL, NativeUnits.gal, 100),
        (EOWUnits.UNIT_10_GAL, NativeUnits.gal, 10),
        (EOWUnits.UNIT_CF, NativeUnits.cf, 1),
        (EOWUnits.UNIT_CCF, NativeUnits.cf, 100),
        (EOWUnits.UNIT_KGAL, NativeUnits.gal, 1000),
        (EOWUnits.UNIT_CUBIC_FEET, NativeUnits.cf, 1),
        (EOWUnits.UNIT_CM, NativeUnits.cm, 1),
        (EOWUnits.UNIT_CUBIC_METER, NativeUnits.cm, 1),
    ],
)
async def test_meter_info(
    aiohttp_client, loop, units, expected_native_unit, expected_factor
):
    """Test meter returns expected units."""
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

    account, client = await build_client(websession)
    meter = await build_meter(client)

    # Read meter info
    assert meter.reading.reading == 42.0 * expected_factor
    assert meter.reading.unit == expected_native_unit
    assert meter.meter_info is not None
    assert meter.native_unit_of_measurement == expected_native_unit

    # Read meter with some historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1
    assert meter.last_historical_data[0].reading == 42.0 * expected_factor
    assert meter.last_historical_data[0].unit == expected_native_unit


@pytest.mark.parametrize(
    "units,expected_native_unit,expected_factor",
    [
        (EOWUnits.UNIT_GAL, NativeUnits.gal, 1),
        (EOWUnits.UNIT_100_GAL, NativeUnits.gal, 100),
        (EOWUnits.UNIT_10_GAL, NativeUnits.gal, 10),
        (EOWUnits.UNIT_CF, NativeUnits.cf, 1),
        (EOWUnits.UNIT_CCF, NativeUnits.cf, 100),
        (EOWUnits.UNIT_KGAL, NativeUnits.gal, 1000),
        (EOWUnits.UNIT_CUBIC_FEET, NativeUnits.cf, 1),
        (EOWUnits.UNIT_CM, NativeUnits.cm, 1),
        (EOWUnits.UNIT_CUBIC_METER, NativeUnits.cm, 1),
    ],
)
async def test_meter_historical_data(
    aiohttp_client, loop, units, expected_native_unit, expected_factor
):
    """Basic meter test."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_nodata_endpoint,
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)
    meter = await build_meter(client)

    # fetch meter info
    assert meter.native_unit_of_measurement == expected_native_unit

    # Read historical data with no data
    await meter.read_historical_data(client=client, days_to_load=1)
    assert meter.last_historical_data == []

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
    account, client = await build_client(websession)

    # Read meter with some historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1
    assert meter.last_historical_data[0].reading == 42.0 * expected_factor
    assert meter.last_historical_data[0].unit == expected_native_unit

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_newer_data_endpoint, units),
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)

    # Read meter with newer historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1
    assert meter.last_historical_data[0].reading == 42.42 * expected_factor
    assert meter.last_historical_data[0].unit == expected_native_unit

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_newerdata_moredata_endpoint, units),
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)

    # Read meter with more historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 2
    assert meter.last_historical_data[0].reading == 42.42 * expected_factor
    assert meter.last_historical_data[0].unit == expected_native_unit
    assert meter.last_historical_data[1].reading == 42.42 * expected_factor
    assert meter.last_historical_data[1].unit == expected_native_unit


async def test_meter_info_mismatch(aiohttp_client, loop):
    """Test meter handling units mismatch."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, EOWUnits.UNIT_GAL),
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, EOWUnits.UNIT_CM),
    )
    websession = await aiohttp_client(app)

    account, client = await build_client(websession)
    meter = await build_meter(client)

    with pytest.raises(EyeOnWaterUnitError):
        await meter.read_historical_data(client=client, days_to_load=1)

    # New meter reading in CM
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, EOWUnits.UNIT_CM),
    )
    websession = await aiohttp_client(app)

    account, client = await build_client(websession)
    await meter.read_meter_info(client)

    with pytest.raises(EyeOnWaterUnitError):
        assert meter.reading
