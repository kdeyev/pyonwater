"""Tests for pyonwater meter."""


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

from pyonwater import EyeOnWaterException, Meter, MeterReader

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


# @pytest.mark.parametrize(
#     (", "expected_units"),
#     [
#         (False, "gal"),
#         (True, "m\u00b3"),
#     ],
# )
async def test_meter_info(aiohttp_client, loop):
    """Test meter returns expected units."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter = Meter(meter_reader)

    assert meter.meter_id is not None
    assert meter.meter_uuid is not None

    # Access meter before reading
    with pytest.raises(EyeOnWaterException):
        assert meter.reading
    with pytest.raises(EyeOnWaterException):
        assert meter.meter_info

    # Read meter info
    await meter.read_meter_info(client=client)
    assert meter.reading != 0
    assert meter.meter_info is not None


async def test_meter_historical_data(aiohttp_client, loop):
    """Basic meter test."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_nodata_endpoint,
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)
    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    meter = Meter(meter_reader)

    # Read historical data with no data
    await meter.read_historical_data(client=client, days_to_load=1)
    assert meter.last_historical_data == []

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)

    # Read meter with some historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1
    assert meter.last_historical_data[0].reading == 42.0

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_newer_data_endpoint,
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)

    # Read meter with newer historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1
    assert meter.last_historical_data[0].reading == 42.42

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_newerdata_moredata_endpoint,
    )
    websession = await aiohttp_client(app)
    account, client = await build_client(websession)

    # Read meter with more historical
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 2
    assert meter.last_historical_data[0].reading == 42.42
    assert meter.last_historical_data[1].reading == 42.42


@pytest.mark.parametrize(
    "units",
    [
        "GAL",
        "100 GAL",
        "10 GAL",
        "CF",
        "CCF",
        "KGAL",
        "CUBIC_FEET",
        "CM",
        "CUBIC_METER",
    ],
)
async def test_meter_units(aiohttp_client, loop, units):
    """Test handling data with different units."""
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

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter = Meter(meter_reader)
    await meter.read_meter_info(client=client)

    assert meter.reading != 0
    assert meter.meter_id is not None
    assert meter.meter_uuid is not None
    assert meter.meter_info is not None


@pytest.mark.parametrize(
    "units",
    [
        "GAL",
        "100 GAL",
        "10 GAL",
        "CF",
        "CCF",
        "KGAL",
        "CUBIC_FEET",
        "CM",
        "CUBIC_METER",
    ],
)
async def test_meter_wrong_unit_historical_data(aiohttp_client, loop, units):
    """Test handling data with different units of historical data."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        change_units_decorator(mock_historical_data_endpoint, units),
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter = Meter(meter_reader)
    await meter.read_historical_data(client=client, days_to_load=1)
    assert meter.last_historical_data

    # Meter info is not available
    with pytest.raises(EyeOnWaterException):
        assert meter.reading
    with pytest.raises(EyeOnWaterException):
        assert meter.meter_info


@pytest.mark.parametrize(
    "units",
    [
        "GAL",
        "100 GAL",
        "10 GAL",
        "CF",
        "CCF",
        "KGAL",
        "CUBIC_FEET",
        "CM",
        "CUBIC_METER",
    ],
)
async def test_meter_wrong_unit_reading(aiohttp_client, loop, units):
    """Test handling data with different units of reading."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, units),
    )
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter = Meter(meter_reader)
    await meter.read_meter_info(client=client)
    assert meter.reading != 0

    # No historical data
    assert meter.last_historical_data == []
