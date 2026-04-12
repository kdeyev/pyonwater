"""Tests for pyonwater meter reader."""  # nosec: B101, B106

import datetime
import json
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

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

from pyonwater import EyeOnWaterAPIError, EyeOnWaterResponseIsEmpty, MeterReader
from pyonwater.models.units import AggregationLevel, RequestUnits


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
        data = await reader.read_historical_data_range_export(
            client=client,
            days_to_load=2,
            poll_interval=0.1,
        )

    assert len(data) == 2  # nosec: B101
    assert [point.reading for point in data] == [100.0, 101.5]  # nosec: B101
    assert data[0].flow_value is None  # nosec: B101
    assert data[1].flow_value == 1.25  # nosec: B101
    assert data[0].dt.tzinfo is not None  # nosec: B101
    sleep_mock.assert_awaited_once_with(0.1)


def test_normalize_export_path() -> None:
    """Verify export URLs are converted into client request paths."""
    assert (  # nosec: B101
        MeterReader.normalize_export_path(
            "https://eyeonwater.com/export/download.csv?token=abc"
        )
        == "/export/download.csv?token=abc"
    )
    assert (
        MeterReader.normalize_export_path("/export/download.csv")
        == "/export/download.csv"
    )  # nosec: B101


def test_parse_export_datetime_invalid() -> None:
    """Verify invalid export timestamps raise a clear error."""
    with pytest.raises(ValueError, match="Unrecognized export datetime"):
        MeterReader.parse_export_datetime("not-a-date")


def test_parse_export_csv_skips_invalid_rows_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify malformed export rows are skipped with a warning."""
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    raw_csv = (
        "Read_Time,Read,Read_Unit,Flow,Timezone\n"
        "03/01/2026 12:15 PM,100.0,GAL,,US/Pacific\n"
        "not-a-date,101.5,GAL,1.25,US/Pacific\n"
    )

    with caplog.at_level(logging.WARNING, logger="pyonwater.meter_reader"):
        points = reader.parse_export_csv(raw_csv)

    assert len(points) == 1  # nosec: B101
    assert points[0].reading == 100.0  # nosec: B101
    assert "Skipping unparsable CSV row" in caplog.text  # nosec: B101


# ---------------------------------------------------------------------------
# Phase 1: Export validation, poll error/timeout, normalize_export_path edge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio()
async def test_export_range_invalid_days_to_load() -> None:
    """ValueError raised when days_to_load=0."""
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    client_mock = AsyncMock()
    with pytest.raises(ValueError, match="days_to_load must be at least 1, got 0"):
        await reader.read_historical_data_range_export(client_mock, days_to_load=0)


@pytest.mark.asyncio()
async def test_export_range_invalid_max_retries() -> None:
    """ValueError raised when max_retries=0."""
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    client_mock = AsyncMock()
    with pytest.raises(ValueError, match="max_retries must be at least 1, got 0"):
        await reader.read_historical_data_range_export(
            client_mock, days_to_load=1, max_retries=0
        )


@pytest.mark.asyncio()
async def test_export_range_invalid_poll_interval() -> None:
    """ValueError raised when poll_interval is negative."""
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    client_mock = AsyncMock()
    with pytest.raises(ValueError, match="poll_interval must be non-negative, got -1"):
        await reader.read_historical_data_range_export(
            client_mock, days_to_load=1, max_retries=1, poll_interval=-1
        )


@pytest.mark.asyncio()
async def test_export_range_bad_initiate_json(aiohttp_client: Any) -> None:
    """EyeOnWaterAPIError raised when initiate endpoint returns non-JSON."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_bad_json(_request: web.Request) -> web.Response:
        return web.Response(text="not json")

    app.router.add_get("/reports/export_initiate", mock_bad_json)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):
        await reader.read_historical_data_range_export(client, days_to_load=1)


@pytest.mark.asyncio()
async def test_export_range_missing_task_id(aiohttp_client: Any) -> None:
    """EyeOnWaterAPIError raised when initiate response has no task_id."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_no_task_id(_request: web.Request) -> web.Response:
        return web.Response(text='{"status": "ok"}')

    app.router.add_get("/reports/export_initiate", mock_no_task_id)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError, match="Export task id not found"):
        await reader.read_historical_data_range_export(client, days_to_load=1)


@pytest.mark.asyncio()
async def test_export_range_missing_url(aiohttp_client: Any) -> None:
    """EyeOnWaterAPIError raised when poll result has no url key."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_initiate(_request: web.Request) -> web.Response:
        return web.Response(text='{"task_id": "task-abc"}')

    async def mock_status(_request: web.Request) -> web.Response:
        return web.Response(text='{"state": "done", "result": {"no_url_here": 1}}')

    app.router.add_get("/reports/export_initiate", mock_initiate)
    app.router.add_get("/reports/export_check_status/task-abc", mock_status)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with patch("pyonwater.meter_reader.asyncio.sleep"):
        with pytest.raises(EyeOnWaterAPIError, match="Export result missing URL"):
            await reader.read_historical_data_range_export(
                client, days_to_load=1, poll_interval=0.0
            )


@pytest.mark.asyncio()
async def test_poll_export_task_error_state(aiohttp_client: Any) -> None:
    """EyeOnWaterAPIError raised when poll returns error state with message."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_initiate(_request: web.Request) -> web.Response:
        return web.Response(text='{"task_id": "task-err"}')

    async def mock_status(_request: web.Request) -> web.Response:
        return web.Response(
            text='{"state": "error", "message": "Something went wrong"}'
        )

    app.router.add_get("/reports/export_initiate", mock_initiate)
    app.router.add_get("/reports/export_check_status/task-err", mock_status)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with patch("pyonwater.meter_reader.asyncio.sleep"):
        with pytest.raises(EyeOnWaterAPIError, match="Something went wrong"):
            await reader.read_historical_data_range_export(
                client, days_to_load=1, poll_interval=0.0
            )


@pytest.mark.asyncio()
async def test_poll_export_task_timeout(aiohttp_client: Any) -> None:
    """EyeOnWaterAPIError raised when poll exhausts max_retries."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_initiate(_request: web.Request) -> web.Response:
        return web.Response(text='{"task_id": "task-timeout"}')

    async def mock_status(_request: web.Request) -> web.Response:
        return web.Response(text='{"state": "pending"}')

    app.router.add_get("/reports/export_initiate", mock_initiate)
    app.router.add_get("/reports/export_check_status/task-timeout", mock_status)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with patch("pyonwater.meter_reader.asyncio.sleep"):
        with pytest.raises(EyeOnWaterAPIError, match="did not complete"):
            await reader.read_historical_data_range_export(
                client, days_to_load=1, max_retries=2, poll_interval=0.0
            )


def test_normalize_export_path_invalid() -> None:
    """EyeOnWaterAPIError raised for unsupported URL schemes."""
    with pytest.raises(EyeOnWaterAPIError, match="Unsupported export url format"):
        MeterReader.normalize_export_path("ftp://weird.com/file")


# ---------------------------------------------------------------------------
# Phase 2: parse_export_csv column variants + one_day empty response forms
# ---------------------------------------------------------------------------


def test_parse_export_csv_space_column_names() -> None:
    """parse_export_csv handles space-separated column name variants.

    The real API sometimes uses "Read Time" and "Unit" instead of
    "Read_Time" and "Read_Unit". Both must be recognised.
    """
    reader = MeterReader(meter_uuid="x", meter_id="x")
    raw_csv = (
        "Read Time,Read,Unit,Flow,Timezone\n03/01/2026 12:15,100.0,GAL,,US/Pacific\n"
    )

    points = reader.parse_export_csv(raw_csv)

    assert len(points) == 1  # nosec: B101
    assert points[0].reading == 100.0  # nosec: B101
    assert points[0].unit == "GAL"  # nosec: B101
    assert points[0].flow_value is None  # nosec: B101


def test_parse_export_csv_empty_string() -> None:
    """parse_export_csv returns an empty list for an empty string input."""
    reader = MeterReader(meter_uuid="x", meter_id="x")

    points = reader.parse_export_csv("")

    assert not points  # nosec: B101


def test_parse_export_csv_no_flow_column() -> None:
    """parse_export_csv sets flow_value to None when the Flow column is absent."""
    reader = MeterReader(meter_uuid="x", meter_id="x")
    raw_csv = (
        "Read_Time,Read,Read_Unit,Timezone\n03/01/2026 12:15,100.0,GAL,US/Pacific\n"
    )

    points = reader.parse_export_csv(raw_csv)

    assert len(points) == 1  # nosec: B101
    assert points[0].reading == 100.0  # nosec: B101
    assert points[0].flow_value is None  # nosec: B101


@pytest.mark.asyncio()
async def test_read_historical_data_one_day_quoted_empty(
    aiohttp_client: Any,
) -> None:
    """EyeOnWaterResponseIsEmpty raised when consumption returns '""'.

    The real API returns the JSON-encoded empty string '""' to signal no data.
    """
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_quoted_empty(_request: web.Request) -> web.Response:
        return web.Response(text='""')

    app.router.add_post("/api/2/residential/consumption", mock_quoted_empty)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterResponseIsEmpty):
        await reader.read_historical_data_one_day(
            client=client,
            date=datetime.datetime(2026, 3, 1),
        )


@pytest.mark.asyncio()
async def test_read_historical_data_one_day_null_response(
    aiohttp_client: Any,
) -> None:
    """EyeOnWaterResponseIsEmpty raised when consumption returns 'null'.

    The real API returns the string 'null' to signal no data.
    """
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_null(_request: web.Request) -> web.Response:
        return web.Response(text="null")

    app.router.add_post("/api/2/residential/consumption", mock_null)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterResponseIsEmpty):
        await reader.read_historical_data_one_day(
            client=client,
            date=datetime.datetime(2026, 3, 1),
        )


@pytest.mark.asyncio()
async def test_read_historical_data_one_day_missing_timeseries_key(
    aiohttp_client: Any,
) -> None:
    """EyeOnWaterResponseIsEmpty raised when the meter_uuid key is absent.

    The historical data fixture uses key "meter_uuid,0". When the MeterReader
    has uuid "test_meter" it looks for "test_meter,0", which is not present,
    triggering the missing-key path.
    """
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_wrong_key(_request: web.Request) -> web.Response:
        with open(
            "tests/mock_data/historical_data_mock_anonymized.json", encoding="utf-8"
        ) as f:
            return web.Response(text=f.read())

    app.router.add_post("/api/2/residential/consumption", mock_wrong_key)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    # Reader uuid "test_meter" → looks for "test_meter,0"; fixture has "meter_uuid,0"
    reader = MeterReader(meter_uuid="test_meter", meter_id="test_id")

    with pytest.raises(EyeOnWaterResponseIsEmpty):
        await reader.read_historical_data_one_day(
            client=client,
            date=datetime.datetime(2026, 3, 1),
        )


# ---------------------------------------------------------------------------
# Phase 3: AggregationLevel parametrize + RequestUnits forwarding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level", list(AggregationLevel))
@pytest.mark.asyncio()
async def test_read_historical_data_one_day_all_aggregation_levels(
    aiohttp_client: Any, level: AggregationLevel
) -> None:
    """All AggregationLevel values produce a successful consumption request.

    For each enum member the aggregate field in the POST body must match the
    enum's wire value and the endpoint must return valid data.
    """
    captured_body: dict[str, Any] = {}

    async def mock_consumption(request: web.Request) -> web.Response:
        captured_body.update(await request.json())
        with open(
            "tests/mock_data/historical_data_mock_anonymized.json", encoding="utf-8"
        ) as f:
            return web.Response(text=f.read())

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_consumption)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    await reader.read_historical_data_one_day(
        client=client,
        date=datetime.datetime(2026, 3, 1),
        aggregation=level,
    )

    assert captured_body["params"]["aggregate"] == level.value  # nosec: B101


@pytest.mark.asyncio()
async def test_read_historical_data_one_day_units_forwarded(
    aiohttp_client: Any,
) -> None:
    """The units parameter is forwarded verbatim in the POST body.

    Verifies that passing RequestUnits.GALLONS results in the string "gallons"
    appearing in the params.units field of the consumption request.
    """
    captured_body: dict[str, Any] = {}

    async def mock_consumption(request: web.Request) -> web.Response:
        captured_body.update(await request.json())
        with open(
            "tests/mock_data/historical_data_mock_anonymized.json", encoding="utf-8"
        ) as f:
            return web.Response(text=f.read())

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_consumption)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    await reader.read_historical_data_one_day(
        client=client,
        date=datetime.datetime(2026, 3, 1),
        units=RequestUnits.GALLONS,
    )

    assert captured_body["params"]["units"] == RequestUnits.GALLONS.value  # nosec: B101
