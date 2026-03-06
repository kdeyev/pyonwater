"""Tests for pyonwater meter reader."""  # nosec: B101, B106

import json
import logging
from typing import Any
from unittest.mock import patch

from aiohttp import web
from conftest import (
    build_client,
    change_units_decorator,
    mock_historical_data_endpoint,
    mock_historical_data_no_data_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
import pytest

from pyonwater import EyeOnWaterAPIError, MeterReader


@pytest.mark.asyncio()
async def test_meter_reader(aiohttp_client: Any) -> None:
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0  # nosec: B101

    await meter_reader.read_historical_data(client=client, days_to_load=1)


@pytest.mark.asyncio()
async def test_meter_reader_nodata(aiohttp_client: Any) -> None:
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_no_data_endpoint,
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0  # nosec: B101

    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert data == []  # nosec: B101


@pytest.mark.asyncio()
async def test_meter_reader_wrong_units(aiohttp_client: Any) -> None:
    """Test reading date with unknown units."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, "hey"),
    )

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):
        await meter_reader.read_meter_info(client=client)


@pytest.mark.asyncio()
async def test_meter_reader_empty_response(aiohttp_client: Any) -> None:
    """Test handling of empty API responses.

    Real API behavior when params are invalid.
    """
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)

    async def mock_empty_response(_request: web.Request) -> web.Response:
        """Mock endpoint that returns empty response like real API does.

        Simulates real API behavior with invalid params.
        """
        return web.Response(text="")

    app.router.add_post("/api/2/residential/consumption", mock_empty_response)

    websession = await aiohttp_client(app)

    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Empty responses should be handled gracefully (not crash)
    # The read_historical_data method catches EyeOnWaterResponseIsEmpty and continues
    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert data == []  # nosec: B101  # Empty response results in no data points


@pytest.mark.asyncio()
async def test_meter_reader_raises_for_multiple_meters(aiohttp_client: Any) -> None:
    """Verify EyeOnWaterAPIError raised when new_search returns multiple hits."""
    with open("tests/mock_data/read_meter_mock_anonymized.json", encoding="utf-8") as f:
        single_hit_data = json.load(f)

    hit = single_hit_data["elastic_results"]["hits"]["hits"][0]
    single_hit_data["elastic_results"]["hits"]["hits"] = [hit, hit]

    async def mock_two_meters(_request: web.Request) -> web.Response:
        return web.Response(text=json.dumps(single_hit_data))

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_two_meters)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError, match="More than one meter reading found"):
        await meter_reader.read_meter_info(client=client)


@pytest.mark.asyncio()
async def test_meter_reader_historical_debug_logging(aiohttp_client: Any) -> None:
    """With DEBUG logging enabled, the raw-response branch executes."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    logger = logging.getLogger("pyonwater.meter_reader")
    original_level = logger.level
    try:
        logger.setLevel(logging.DEBUG)
        data = await reader.read_historical_data(client=client, days_to_load=1)
    finally:
        logger.setLevel(original_level)

    assert len(data) > 0  # nosec: B101


@pytest.mark.asyncio()
async def test_meter_reader_historical_invalid_json_raises(aiohttp_client: Any) -> None:
    """Verify EyeOnWaterAPIError raised when consumption returns malformed JSON."""

    async def mock_bad_json(_request: web.Request) -> web.Response:
        return web.Response(text="{this is not: valid json!!!}")

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_bad_json)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):  # nosec: B101
        await reader.read_historical_data(client=client, days_to_load=1)


@pytest.mark.asyncio()
async def test_meter_reader_range_export(aiohttp_client: Any) -> None:
    """Verify export-range polling and CSV parsing."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_export_initiate(request: web.Request) -> web.Response:
        assert request.query["meter_uuid"] == "meter_uuid"  # nosec: B101
        assert request.query["row-format"] == "range"  # nosec: B101
        return web.Response(text='{"task_id":"task-123"}')

    poll_count = 0

    async def mock_export_status(_request: web.Request) -> web.Response:
        nonlocal poll_count
        poll_count += 1
        if poll_count == 1:
            return web.Response(text='{"state":"queued"}')
        return web.Response(
            text=json.dumps(
                {
                    "state": "done",
                    "result": {
                        "url": "https://eyeonwater.com/export/download.csv?token=abc"
                    },
                }
            )
        )

    async def mock_export_csv(_request: web.Request) -> web.Response:
        return web.Response(
            text=(
                "Read_Time,Read,Read_Unit,Flow,Timezone\n"
                "03/01/2026 1:15 PM,101.5,GAL,1.25,US/Pacific\n"
                "03/01/2026 12:15 PM,100.0,GAL,,US/Pacific\n"
            )
        )

    app.router.add_get("/reports/export_initiate", mock_export_initiate)
    app.router.add_get(
        "/reports/export_check_status/task-123",
        mock_export_status,
    )
    app.router.add_get("/export/download.csv", mock_export_csv)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with patch("pyonwater.meter_reader.asyncio.sleep") as sleep_mock:
        data = await reader.read_historical_data_range_export(client=client, days_to_load=2)

    assert len(data) == 2  # nosec: B101
    assert [point.reading for point in data] == [100.0, 101.5]  # nosec: B101
    assert data[0].flow_value is None  # nosec: B101
    assert data[1].flow_value == 1.25  # nosec: B101
    assert data[0].dt.tzinfo is not None  # nosec: B101
    sleep_mock.assert_awaited_once_with(0.1)


def test_normalize_export_path() -> None:
    """Verify export URLs are converted into client request paths."""
    assert (  # nosec: B101
        MeterReader._normalize_export_path(
            "https://eyeonwater.com/export/download.csv?token=abc"
        )
        == "/export/download.csv?token=abc"
    )
    assert MeterReader._normalize_export_path("/export/download.csv") == "/export/download.csv"  # nosec: B101


def test_parse_export_datetime_invalid() -> None:
    """Verify invalid export timestamps raise a clear error."""
    with pytest.raises(EyeOnWaterAPIError, match="Unrecognized export datetime"):
        MeterReader._parse_export_datetime("not-a-date")
