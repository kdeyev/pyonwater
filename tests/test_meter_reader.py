"""Tests for pyonwater meter reader."""

import json

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


async def test_meter_reader(aiohttp_client, loop):
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0

    await meter_reader.read_historical_data(client=client, days_to_load=1)


async def test_meter_reader_nodata(aiohttp_client, loop):
    """Basic meter reader test."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption", mock_historical_data_no_data_endpoint
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    meter_info = await meter_reader.read_meter_info(client=client)
    assert meter_info.reading.latest_read.full_read != 0

    data = await meter_reader.read_historical_data(client=client, days_to_load=1)
    assert data == []


async def test_meter_reader_wrong_units(aiohttp_client, loop):
    """Test reading date with unknown units."""
    app = web.Application()

    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, "hey"),
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):
        await meter_reader.read_meter_info(client=client)


async def test_meter_reader_multiple_meters(aiohttp_client, loop):
    """Test that multiple meter readings raises an exception."""

    def mock_multiple_meters_endpoint(request):
        with open("tests//mock_data/read_meter_mock_anonymized.json") as f:
            data = json.load(f)
            # Duplicate the meter entry to simulate multiple meters
            hits = data["elastic_results"]["hits"]["hits"]
            hits.append(hits[0])
            return web.Response(text=json.dumps(data))

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_multiple_meters_endpoint)

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(Exception, match="More than one meter reading found"):
        await meter_reader.read_meter_info(client=client)


async def test_meter_reader_invalid_historical_response(aiohttp_client, loop):
    """Test that invalid historical data response raises EyeOnWaterAPIError."""

    def mock_invalid_historical_endpoint(request):
        return web.Response(text='{"invalid": "data"}')

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post(
        "/api/2/residential/consumption", mock_invalid_historical_endpoint
    )

    websession = await aiohttp_client(app)

    account, client = await build_client(websession)

    meter_reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    with pytest.raises(EyeOnWaterAPIError):
        await meter_reader.read_historical_data(client=client, days_to_load=1)
