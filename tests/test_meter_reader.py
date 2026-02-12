"""Tests for pyonwater meter reader."""  # nosec: B101, B106

from typing import Any

from aiohttp import web
import pytest

from conftest import (
    build_client,
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_historical_data_no_data_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
from pyonwater import EyeOnWaterAPIError, MeterReader


async def test_meter_reader(aiohttp_client: Any) -> None:
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_endpoint  # type: ignore
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0  # nosec: B101

    await meter_reader.read_historical_data(client=client, days_to_load=1)


async def test_meter_reader_nodata(aiohttp_client: Any) -> None:
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_no_data_endpoint,  # type: ignore
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0  # nosec: B101

    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert data == []  # nosec: B101


async def test_meter_reader_wrong_units(aiohttp_client: Any) -> None:
    """Test reading date with unknown units."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, "hey"),  # type: ignore
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):
        await meter_reader.read_meter_info(client=client)


async def test_meter_reader_empty_response(aiohttp_client: Any) -> None:
    """Test handling of empty API responses.

    Real API behavior when params are invalid.
    """
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)  # type: ignore
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )

    async def mock_empty_response(_request: web.Request) -> web.Response:
        """Mock endpoint that returns empty response like real API does.

        Simulates real API behavior with invalid params.
        """
        return web.Response(text="")

    app.router.add_post(
        "/api/2/residential/consumption", mock_empty_response  # type: ignore
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Empty responses should be handled gracefully (not crash)
    # The read_historical_data method catches EyeOnWaterResponseIsEmpty and continues
    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert data == []  # nosec: B101  # Empty response results in no data points
