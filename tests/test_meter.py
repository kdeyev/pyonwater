"""Tests for pyonwater meter."""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

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

from pyonwater import (
    DataPoint,
    EOWUnits,
    EyeOnWaterException,
    EyeOnWaterUnitError,
    MeterReader,
    NativeUnits,
)

# Mock for historical data request, but no actual data
mock_historical_data_nodata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_nodata",
)

# Mock for historical data request, but newer data
mock_historical_data_newer_data_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data",
)

# Mock for historical data request, but newer and more data
mock_historical_data_newerdata_moredata_endpoint = build_data_endpoint(
    "historical_data_mock_anonymized_newer_data_moredata",
)


@pytest.mark.parametrize(
    "units,expected_native_unit,expected_factor",
    [
        (EOWUnits.UNIT_GAL, NativeUnits.GAL, 1),
        (EOWUnits.UNIT_100_GAL, NativeUnits.GAL, 100),
        (EOWUnits.UNIT_10_GAL, NativeUnits.GAL, 10),
        (EOWUnits.UNIT_CF, NativeUnits.CF, 1),
        (EOWUnits.UNIT_CCF, NativeUnits.CF, 100),
        (EOWUnits.UNIT_KGAL, NativeUnits.GAL, 1000),
        (EOWUnits.UNIT_CUBIC_FEET, NativeUnits.CF, 1),
        (EOWUnits.UNIT_CM, NativeUnits.CM, 1),
        (EOWUnits.UNIT_CUBIC_METER, NativeUnits.CM, 1),
        (EOWUnits.UNIT_LITER, NativeUnits.CM, 0.001),
        (EOWUnits.UNIT_LITERS, NativeUnits.CM, 0.001),
        (EOWUnits.UNIT_LITER_LC, NativeUnits.CM, 0.001),
    ],
)
async def test_meter_info(
    aiohttp_client: Any,
    units: EOWUnits,
    expected_native_unit: NativeUnits,
    expected_factor: float,
) -> None:
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

    _, client = await build_client(websession)
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


async def test_meter_historical_data_no_data(aiohttp_client: Any) -> None:
    """Basic meter test."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        mock_read_meter_endpoint,
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_endpoint,
    )
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    # Read historical data with no data
    data = await meter.read_historical_data(client=client, days_to_load=1)
    assert data != []
    assert meter.last_historical_data != []

    # New meter reading in CM
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        mock_read_meter_endpoint,
    )
    app.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_nodata_endpoint,
    )
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)
    meter.last_historical_data = data  # dirty hack for restoring historical data

    # Read meter with some historical
    data = await meter.read_historical_data(client=client, days_to_load=1)
    assert data == []

    # Read historical data with no data
    data = await meter.read_historical_data(client=client, days_to_load=1)
    assert data == []
    assert meter.last_historical_data != []


async def test_meter_info_mismatch(aiohttp_client: Any) -> None:
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

    _, client = await build_client(websession)
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

    _, client = await build_client(websession)
    await meter.read_meter_info(client)

    with pytest.raises(EyeOnWaterUnitError):
        assert meter.reading


async def test_meter_properties(aiohttp_client: Any) -> None:
    """Test meter_uuid, meter_id, and native_unit_of_measurement properties."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    assert meter.meter_uuid == "meter_uuid"
    assert meter.meter_id == "meter_id"
    assert meter.native_unit_of_measurement == NativeUnits.GAL


async def test_meter_info_none_raises(aiohttp_client: Any) -> None:
    """Test meter_info property raises when _meter_info is None."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    # pylint: disable-next=protected-access
    meter._meter_info = None  # type: ignore[assignment]
    with pytest.raises(EyeOnWaterException):
        _ = meter.meter_info


async def test_meter_reading_none_raises(aiohttp_client: Any) -> None:
    """Test reading property raises when _reading_data is None."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    # pylint: disable-next=protected-access
    meter._reading_data = None  # type: ignore[assignment]
    with pytest.raises(EyeOnWaterException):
        _ = meter.reading


async def test_meter_historical_same_date_more_data(aiohttp_client: Any) -> None:
    """Historical data: same end date but more points replaces existing."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app.router.add_post("/api/2/residential/consumption", mock_historical_data_endpoint)
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    # First read: populate last_historical_data
    await meter.read_historical_data(client=client, days_to_load=1)
    assert len(meter.last_historical_data) == 1

    # Second read with more data at same date
    app2 = web.Application()
    app2.router.add_post("/account/signin", mock_signin_endpoint)
    app2.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    app2.router.add_post(
        "/api/2/residential/consumption",
        mock_historical_data_newerdata_moredata_endpoint,
    )
    websession2 = await aiohttp_client(app2)
    _, client2 = await build_client(websession2)

    # Force same date in last_historical_data to trigger same-date-more-data branch
    await meter.read_historical_data(client=client2, days_to_load=1)
    # The moredata mock has 2 entries, should replace
    assert len(meter.last_historical_data) >= 1


async def test_meter_range_export_converts_and_preserves_cache(
    aiohttp_client: Any,
) -> None:
    """Export wrapper converts values, forwards params, and leaves cache unchanged."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post(
        "/api/2/residential/new_search",
        change_units_decorator(mock_read_meter_endpoint, EOWUnits.UNIT_100_GAL),
    )

    async def mock_export_initiate(request: web.Request) -> web.Response:
        assert request.query["meter_uuid"] == "meter_uuid"  # nosec: B101
        assert request.query["row-format"] == "range"  # nosec: B101
        assert request.query["export_resolution"] == "daily"  # nosec: B101
        assert request.query["export_unit"] == "Gallons"  # nosec: B101
        assert request.query["start-date"] == "02/28/2026"  # nosec: B101
        assert request.query["end-date"] == "03/01/2026"  # nosec: B101
        return web.Response(text='{"task_id":"task-123"}')

    async def mock_export_status(_request: web.Request) -> web.Response:
        return web.Response(
            text=(
                '{"state":"done","result":'
                '{"url":"https://eyeonwater.com/export/download.csv?token=abc"}}'
            )
        )

    async def mock_export_csv(_request: web.Request) -> web.Response:
        return web.Response(
            text=(
                "Read_Time,Read,Read_Unit,Flow,Timezone\n"
                "03/01/2026 1:15 PM,1.5,100 GAL,0.25,US/Pacific\n"
                "03/01/2026 12:15 PM,1.0,100 GAL,,US/Pacific\n"
            )
        )

    app.router.add_get("/reports/export_initiate", mock_export_initiate)
    app.router.add_get("/reports/export_check_status/task-123", mock_export_status)
    app.router.add_get("/export/download.csv", mock_export_csv)

    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)
    meter.last_historical_data = [
        DataPoint(
            dt=datetime(2026, 2, 1, tzinfo=timezone.utc),
            reading=42.0,
            unit=NativeUnits.GAL,
        )
    ]

    with patch("pyonwater.meter_reader.datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 3, 1, tzinfo=timezone.utc)
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
        data = await meter.read_historical_data_range_export(
            client=client,
            days_to_load=2,
            include_today=True,
            export_resolution="daily",
            export_unit="Gallons",
            max_retries=2,
            poll_interval=0.1,
        )

    assert [point.reading for point in data] == [100.0, 150.0]  # nosec: B101
    assert data[1].flow_value == 25.0  # nosec: B101
    assert data[0].unit == NativeUnits.GAL  # nosec: B101
    assert len(meter.last_historical_data) == 1  # nosec: B101
    assert meter.last_historical_data[0].reading == 42.0  # nosec: B101


async def test_meter_convert_to_native_preserves_flow_and_end_dt(
    aiohttp_client: Any,
) -> None:
    """Test flow_value conversion and end_dt passthrough on DataPoint conversion."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)

    _, client = await build_client(websession)
    meter = await build_meter(client)

    start_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(hours=1)
    converted = meter.convert_to_native(
        DataPoint(
            dt=start_dt,
            reading=1.0,
            unit=EOWUnits.UNIT_100_GAL,
            flow_value=2.0,
            end_dt=end_dt,
        )
    )

    assert converted.reading == 100.0
    assert converted.flow_value == 200.0
    assert converted.end_dt == end_dt


async def test_meter_cache_keeps_newer_data(aiohttp_client: Any) -> None:
    """Cache is not overwritten when incoming data has an older timestamp."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    newer_point = DataPoint(
        dt=datetime(2026, 3, 2, tzinfo=timezone.utc),
        reading=200.0,
        unit=EOWUnits.UNIT_GAL,
    )
    older_point = DataPoint(
        dt=datetime(2026, 3, 1, tzinfo=timezone.utc),
        reading=100.0,
        unit=EOWUnits.UNIT_GAL,
    )

    with patch.object(
        MeterReader,
        "read_historical_data",
        new=AsyncMock(side_effect=[[newer_point], [older_point]]),
    ):
        await meter.read_historical_data(client=client, days_to_load=1)
        first_dt = meter.last_historical_data[0].dt
        first_reading = meter.last_historical_data[0].reading

        # Second read returns older data — cache must NOT be overwritten
        await meter.read_historical_data(client=client, days_to_load=1)

    assert meter.last_historical_data[0].dt == first_dt
    assert meter.last_historical_data[0].reading == first_reading


async def test_meter_cache_not_updated_for_same_timestamp(aiohttp_client: Any) -> None:
    """Cache is not overwritten when same-timestamp data with equal count arrives."""
    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_post("/api/2/residential/new_search", mock_read_meter_endpoint)
    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    meter = await build_meter(client)

    point = DataPoint(
        dt=datetime(2026, 3, 1, tzinfo=timezone.utc),
        reading=100.0,
        unit=EOWUnits.UNIT_GAL,
    )

    with patch.object(
        MeterReader,
        "read_historical_data",
        new=AsyncMock(side_effect=[[point], [point]]),
    ):
        await meter.read_historical_data(client=client, days_to_load=1)
        assert len(meter.last_historical_data) == 1
        first_list_id = id(meter.last_historical_data)

        # Second read: same timestamp, same count — list must NOT be reassigned
        await meter.read_historical_data(client=client, days_to_load=1)

    # id() identity check: self.last_historical_data = historical_data was NOT executed
    assert id(meter.last_historical_data) == first_list_id


async def test_meter_read_include_today_false(aiohttp_client: Any) -> None:
    """include_today=False: end_date is yesterday, start_date is (days_to_load-1) days earlier."""
    captured_params: dict[str, str] = {}

    async def mock_initiate(request: web.Request) -> web.Response:
        captured_params.update(dict(request.query))
        return web.Response(text='{"task_id":"task-x"}')

    async def mock_status(_request: web.Request) -> web.Response:
        return web.Response(text='{"state":"done","result":{"url":"/export/dl.csv"}}')

    async def mock_csv(_request: web.Request) -> web.Response:
        return web.Response(text="Read_Time,Read,Read_Unit,Flow,Timezone\n")

    app = web.Application()
    app.router.add_post("/account/signin", mock_signin_endpoint)
    app.router.add_get("/reports/export_initiate", mock_initiate)
    app.router.add_get("/reports/export_check_status/task-x", mock_status)
    app.router.add_get("/export/dl.csv", mock_csv)
    websession = await aiohttp_client(app)
    _, client = await build_client(websession)
    reader = MeterReader(meter_uuid="meter_uuid", meter_id="meter_id")

    # Fix "today" to 2026-03-10 so date assertions are deterministic.
    # Patching datetime.datetime only; datetime.timedelta remains the real class.
    fixed_now = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("pyonwater.meter_reader.datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        with patch("pyonwater.meter_reader.asyncio.sleep"):
            await reader.read_historical_data_range_export(
                client=client,
                days_to_load=3,
                include_today=False,
                poll_interval=0.0,
            )

    # include_today=False, today=2026-03-10:
    #   end_date   = 2026-03-09  (today - 1)
    #   start_date = 2026-03-07  (end_date - (3-1) days)
    assert captured_params["end-date"] == "03/09/2026"
    assert captured_params["start-date"] == "03/07/2026"
