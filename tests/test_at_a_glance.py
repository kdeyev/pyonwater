"""Tests for at_a_glance endpoint and Meter timing properties."""  # nosec: B101

import datetime
import json
import math
from typing import Any

from aiohttp import web
import pytest

from conftest import (
    build_at_a_glance_endpoint,
    build_client,
    build_meter,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
from pyonwater import (
    AtAGlanceData,
    DailyUsagePoint,
    EyeOnWaterAPIError,
    Meter,
    MeterReader,
)
from pyonwater.models.eow_models import MeterInfo
from pyonwater.models.units import EOWUnits


# ---------------------------------------------------------------------------
# AtAGlanceData model tests
# ---------------------------------------------------------------------------


def test_at_a_glance_model_parse_real_shape() -> None:
    """Verify AtAGlanceData parses the real API response shape."""
    raw = """{
        "this_week": {"null": [
            {"value": 95.8, "meter_count": 1, "date": "2026-02-16"},
            {"value": 75.0, "meter_count": 1, "date": "2026-02-17"}
        ]},
        "last_week": {"null": [
            {"value": 62.4, "meter_count": 1, "date": "2026-02-09"},
            {"value": 166.1, "meter_count": 1, "date": "2026-02-10"}
        ]},
        "average": 126.26,
        "days_in_average": 30.0,
        "in_units": "GAL",
        "display_units": "GAL"
    }"""
    data = AtAGlanceData.model_validate_json(raw)

    assert data.average is not None  # nosec: B101
    assert math.isclose(data.average, 126.26)  # nosec: B101
    assert data.days_in_average == 30.0  # nosec: B101
    assert data.in_units == EOWUnits.UNIT_GAL  # nosec: B101
    assert data.display_units == EOWUnits.UNIT_GAL  # nosec: B101


def test_at_a_glance_this_week_points() -> None:
    """Verify this_week_points returns a sorted flat list."""
    raw = """{
        "this_week": {"null": [
            {"value": 75.0, "meter_count": 1, "date": "2026-02-17"},
            {"value": 95.8, "meter_count": 1, "date": "2026-02-16"}
        ]},
        "average": 85.4,
        "days_in_average": 30.0
    }"""
    data = AtAGlanceData.model_validate_json(raw)
    pts = data.this_week_points

    assert len(pts) == 2  # nosec: B101
    # Should be sorted by date ascending
    assert pts[0].date == "2026-02-16"  # nosec: B101
    assert pts[1].date == "2026-02-17"  # nosec: B101
    assert isinstance(pts[0], DailyUsagePoint)  # nosec: B101


def test_at_a_glance_week_totals() -> None:
    """Verify this_week_total and last_week_total sum daily values."""
    raw = """{
        "this_week": {"null": [
            {"value": 100.0, "meter_count": 1, "date": "2026-02-16"},
            {"value": 200.0, "meter_count": 1, "date": "2026-02-17"}
        ]},
        "last_week": {"null": [
            {"value": 50.0, "meter_count": 1, "date": "2026-02-09"},
            {"value": 150.0, "meter_count": 1, "date": "2026-02-10"}
        ]},
        "average": 125.0,
        "days_in_average": 30.0
    }"""
    data = AtAGlanceData.model_validate_json(raw)

    assert data.this_week_total is not None  # nosec: B101
    assert math.isclose(data.this_week_total, 300.0)  # nosec: B101
    assert data.last_week_total is not None  # nosec: B101
    assert math.isclose(data.last_week_total, 200.0)  # nosec: B101


def test_at_a_glance_empty_weeks() -> None:
    """Verify helpers return None/empty list when week data is absent."""
    data = AtAGlanceData(average=50.0, days_in_average=7.0)

    assert not data.this_week_points  # nosec: B101
    assert not data.last_week_points  # nosec: B101
    assert data.this_week_total is None  # nosec: B101
    assert data.last_week_total is None  # nosec: B101


def test_at_a_glance_null_values_ignored_in_total() -> None:
    """Verify None value entries are skipped in totals."""
    raw = """{
        "this_week": {"null": [
            {"value": 100.0, "meter_count": 1, "date": "2026-02-16"},
            {"value": null, "meter_count": 0, "date": "2026-02-17"}
        ]},
        "average": 100.0,
        "days_in_average": 7.0
    }"""
    data = AtAGlanceData.model_validate_json(raw)

    assert data.this_week_total is not None  # nosec: B101
    assert math.isclose(data.this_week_total, 100.0)  # nosec: B101


# ---------------------------------------------------------------------------
# API contract test — request body format
# ---------------------------------------------------------------------------


@pytest.mark.asyncio()
async def test_at_a_glance_request_body_format(aiohttp_client: Any) -> None:
    """Verify read_at_a_glance sends {"meter_uuid": "..."} not params/query."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/at_a_glance",
        build_at_a_glance_endpoint(validate_body=True),
    )

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    result = await meter.read_at_a_glance(client=client)

    assert isinstance(result, AtAGlanceData)  # nosec: B101
    assert result.average is not None  # nosec: B101


@pytest.mark.asyncio()
async def test_at_a_glance_response_parsing(aiohttp_client: Any) -> None:
    """Verify read_at_a_glance returns correctly parsed AtAGlanceData."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/at_a_glance",
        build_at_a_glance_endpoint(),
    )

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    result = await meter.read_at_a_glance(client=client)

    assert result.average is not None  # nosec: B101
    assert math.isclose(result.average, 126.26)  # nosec: B101
    assert result.days_in_average == 30.0  # nosec: B101
    assert result.in_units == EOWUnits.UNIT_GAL  # nosec: B101
    assert len(result.this_week_points) == 7  # nosec: B101
    assert len(result.last_week_points) == 7  # nosec: B101
    # Total for this week from mock file: 95.8+75.0+121.3+92.1+70.7+208.3+57.5
    assert result.this_week_total is not None  # nosec: B101
    assert math.isclose(result.this_week_total, 720.7)  # nosec: B101


# ---------------------------------------------------------------------------
# Meter timing property tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio()
async def test_meter_last_read_time(aiohttp_client: Any) -> None:
    """Verify last_read_time is read from meter.last_read_time in new_search."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    # Mock data has last_read_time = "1990-01-27T00:00:00"
    assert meter.last_read_time is not None  # nosec: B101
    assert meter.last_read_time == datetime.datetime(
        1990, 1, 27, 0, 0, 0
    )  # nosec: B101


@pytest.mark.asyncio()
async def test_meter_communication_seconds(aiohttp_client: Any) -> None:
    """Verify communication_seconds is read from meter.communication_seconds."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    # Mock data has communication_seconds = 11111
    assert meter.communication_seconds == 11111  # nosec: B101


@pytest.mark.asyncio()
async def test_meter_next_update(aiohttp_client: Any) -> None:
    """Verify next_update = last_read_time + communication_seconds."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    # last_read_time=1990-01-27T00:00:00 + 11111s = 1990-01-27T03:05:11
    expected = datetime.datetime(1990, 1, 27, 3, 5, 11)
    assert meter.next_update == expected  # nosec: B101


def test_meter_next_update_none_when_no_meter_data() -> None:
    """Verify next_update returns None when meter info has no meter sub-object."""
    with open("tests/mock_data/read_meter_mock_anonymized.json", encoding="utf-8") as f:
        raw = json.load(f)
    src = raw["elastic_results"]["hits"]["hits"][0]["_source"]
    src_no_meter = {k: v for k, v in src.items() if k != "meter"}

    meter_info = MeterInfo.model_validate(src_no_meter)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    m = Meter(reader, meter_info)

    assert m.last_read_time is None  # nosec: B101
    assert m.communication_seconds is None  # nosec: B101
    assert m.next_update is None  # nosec: B101


@pytest.mark.asyncio()
async def test_at_a_glance_invalid_response_raises(aiohttp_client: Any) -> None:
    """Verify EyeOnWaterAPIError raised when at_a_glance returns malformed JSON."""

    async def mock_bad_json(_request: web.Request) -> web.Response:
        return web.Response(text="{this is not: valid json at all}")

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/at_a_glance", mock_bad_json)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    with pytest.raises(EyeOnWaterAPIError):  # nosec: B101
        await meter.read_at_a_glance(client=client)
