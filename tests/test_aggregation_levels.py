"""Tests for aggregation level support in meter reader."""  # nosec: B101, B106

from datetime import datetime, timedelta
from typing import Any

from aiohttp import web
import pytest

from conftest import (
    build_client,
    build_consumption_endpoint_with_aggregation,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
from pyonwater import MeterReader
from pyonwater.models.units import AggregationLevel, RequestUnits


# Get yesterday's date for testing
TEST_DATE = (datetime.now() - timedelta(days=1)).replace(
    hour=0, minute=0, second=0, microsecond=0
)


@pytest.mark.parametrize(
    "aggregation",
    [
        AggregationLevel.QUARTER_HOURLY,
        AggregationLevel.HOURLY,
        AggregationLevel.DAILY,
        AggregationLevel.WEEKLY,
        AggregationLevel.MONTHLY,
        AggregationLevel.YEARLY,
    ],
)
async def test_aggregation_levels(
    aiohttp_client: Any, aggregation: AggregationLevel
) -> None:
    """Test that all aggregation levels are supported."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/consumption",
        build_consumption_endpoint_with_aggregation(aggregation.value),  # type: ignore
    )

    websession = await aiohttp_client(app)
    _account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0  # nosec: B101

    # Test reading with each aggregation level
    data = await meter_reader.read_historical_data_one_day(
        client=client, date=TEST_DATE, aggregation=aggregation
    )
    # Should return a list (even if empty)
    assert isinstance(data, list)  # nosec: B101


@pytest.mark.parametrize(
    "units",
    [
        RequestUnits.GALLONS,
        RequestUnits.CUBIC_FEET,
        RequestUnits.CCF,
        RequestUnits.LITERS,
        RequestUnits.CUBIC_METERS,
        RequestUnits.IMPERIAL_GALLONS,
        RequestUnits.OIL_BARRELS,
        RequestUnits.FLUID_BARRELS,
    ],
)
async def test_request_units(aiohttp_client: Any, units: RequestUnits) -> None:
    """Test that all request units are supported."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/consumption",
        build_consumption_endpoint_with_aggregation("hourly"),  # type: ignore
    )

    websession = await aiohttp_client(app)
    _account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Test reading with each unit type
    data = await meter_reader.read_historical_data_one_day(
        client=client, date=TEST_DATE, aggregation=AggregationLevel.HOURLY, units=units
    )
    # Should return a list
    assert isinstance(data, list)  # nosec: B101


async def test_default_aggregation(aiohttp_client: Any) -> None:
    """Test that default aggregation level (HOURLY) works without explicit param."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    app.router.add_post(  # type: ignore
        "/api/2/residential/consumption",
        build_consumption_endpoint_with_aggregation("hourly"),  # type: ignore
    )

    websession = await aiohttp_client(app)
    _account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Read without specifying aggregation (should use default)
    data = await meter_reader.read_historical_data_one_day(
        client=client, date=TEST_DATE
    )
    assert isinstance(data, list)  # nosec: B101
