"""Tests for API contract assumptions."""  # nosec: B101, B106

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from aiohttp import web

import pytest

from conftest import (
    build_client,
    mock_historical_data_endpoint,
    mock_read_meter_endpoint,
    mock_signin_endpoint,
)
from pyonwater import MeterReader


@pytest.mark.asyncio()
async def test_new_search_request_payload(aiohttp_client: Any) -> None:
    """Validate new_search request shape."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_new_search(request: web.Request) -> web.Response:
        payload = await request.json()
        terms = payload["query"]["terms"]
        print(f"DEBUG: terms = {terms}")  # Add this to see actual structure
        assert terms["meter.meter_uuid"] == ["meter_uuid"]  # nosec: B101

        data_path = Path("tests/mock_data/read_meter_mock_anonymized.json")
        return web.Response(text=data_path.read_text(encoding="utf-8"))

    app.router.add_post("/api/2/residential/new_search", mock_new_search)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    await meter_reader.read_meter_info(client=client)


@pytest.mark.asyncio()
async def test_consumption_request_payload(aiohttp_client: Any) -> None:
    """Validate consumption request params and query string."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)

    async def mock_consumption(request: web.Request) -> web.Response:
        assert request.rel_url.query.get("eow") == "True"  # nosec: B101
        payload = await request.json()
        params = payload["params"]

        # Validate all required parameters are present
        assert params["aggregate"] == "hourly"  # nosec: B101
        assert params["perspective"] == "billing"  # nosec: B101
        assert params["date"] == "01/02/2024"  # nosec: B101
        assert (
            "units" in params
        )  # nosec: B101  # Critical: API returns empty without this
        assert params["source"] == "barnacle"  # nosec: B101
        assert params["combine"] == "true"  # nosec: B101

        terms = payload["query"]["query"]["terms"]
        assert terms["meter.meter_uuid"] == ["meter_uuid"]  # nosec: B101

        data_path = Path("tests/mock_data/historical_data_mock_anonymized.json")
        return web.Response(text=data_path.read_text(encoding="utf-8"))

    app.router.add_post("/api/2/residential/consumption", mock_consumption)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")
    test_date = datetime.datetime(2024, 1, 2)
    await meter_reader.read_historical_data_one_day(client=client, date=test_date)


@pytest.mark.asyncio()
async def test_consumption_validates_required_params(aiohttp_client: Any) -> None:
    """Verify that validating mock endpoint mimics real API behavior.

    The improved mock_historical_data_endpoint validates required parameters
    and returns empty responses when they're missing, just like the real API.
    This test ensures our code always sends required params.
    """
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search", mock_read_meter_endpoint  # type: ignore
    )
    # Use the improved validating mock that checks for required params
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_endpoint  # type: ignore
    )

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Should succeed because our code now always includes units parameter
    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert len(data) > 0  # nosec: B101
