"""EyeOnWater API integration."""

from __future__ import annotations

import asyncio
import csv
import datetime
import json
import logging
import time
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

from pydantic import ValidationError
import pytz

from .exceptions import EyeOnWaterAPIError, EyeOnWaterResponseIsEmpty
from .models import DataPoint, HistoricalData, MeterInfo
from .models.units import AggregationLevel, RequestUnits

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"
EXPORT_INIT_ENDPOINT = "/reports/export_initiate"
EXPORT_STATUS_ENDPOINT = "/reports/export_check_status/"

# Fallback units when the caller does not specify a preference.
DEFAULT_REQUEST_UNITS = "cm"

_LOGGER = logging.getLogger(__name__)


class MeterReader:
    """Class represents meter reader."""

    def __init__(self, meter_uuid: str, meter_id: str) -> None:
        """Initialize the meter.

        Args:
            meter_uuid: The unique identifier for the meter (cannot be empty).
            meter_id: The meter ID (cannot be empty).

        Raises:
            ValueError: If meter_uuid or meter_id is empty/None.
        """
        if not meter_uuid or not meter_uuid.strip():
            msg = "meter_uuid cannot be empty"
            raise ValueError(msg)
        if not meter_id or not meter_id.strip():
            msg = "meter_id cannot be empty"
            raise ValueError(msg)

        self.meter_uuid = meter_uuid.strip()
        self.meter_id: str = meter_id.strip()

    async def read_meter_info(self, client: Client) -> MeterInfo:
        """Triggers an on-demand meter read and returns it when complete."""
        _LOGGER.debug("Requesting meter reading")

        query = {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}}
        data = await client.request(path=SEARCH_ENDPOINT, method="post", json=query)
        data = json.loads(data)
        meters = data["elastic_results"]["hits"]["hits"]
        if len(meters) > 1:
            msg = "More than one meter reading found"
            raise EyeOnWaterAPIError(msg)

        try:
            meter_info = MeterInfo.model_validate(meters[0]["_source"])
        except ValidationError as e:
            msg = f"Unexpected EOW response {e} with payload {meters[0]['_source']}"
            raise EyeOnWaterAPIError(msg) from e

        return meter_info

    async def read_historical_data(
        self,
        client: Client,
        days_to_load: int,
        aggregation: AggregationLevel = AggregationLevel.HOURLY,
        units: RequestUnits | None = None,
    ) -> list[DataPoint]:
        """Retrieve historical data for today and past N days.

        Args:
            client: The authenticated API client.
            days_to_load: Number of days of history to retrieve (must be positive).
            aggregation: Granularity level for data (default: HOURLY).
                         Use QUARTER_HOURLY for 15-minute resolution.
            units: Preferred units for response data (optional).

        Raises:
            ValueError: If days_to_load is not positive.
        """
        if days_to_load < 1:
            msg = f"days_to_load must be at least 1, got {days_to_load}"
            raise ValueError(msg)

        today = datetime.datetime.now(tz=pytz.UTC).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        date_list: list[datetime.datetime] = [
            today - datetime.timedelta(days=x) for x in range(0, days_to_load)
        ]
        date_list.reverse()

        _LOGGER.debug(
            "requesting historical statistics for %s on %s",
            self.meter_uuid,
            [d.isoformat() for d in date_list],
        )

        statistics: list[DataPoint] = []

        for date in date_list:
            _LOGGER.debug(
                "Fetching data for %s on %s",
                self.meter_uuid,
                date,
            )
            try:
                statistics += await self.read_historical_data_one_day(
                    client=client,
                    date=date,
                    aggregation=aggregation,
                    units=units,
                )
            except EyeOnWaterResponseIsEmpty:
                _LOGGER.warning(
                    "Empty response from API for meter %s on %s - skipping this date",
                    self.meter_uuid,
                    date,
                )
                continue

        return statistics

    def convert(self, data: HistoricalData, key: str) -> list[DataPoint]:
        """Convert the raw data into a list of DataPoint objects."""

        timezones = data.hit.meter_timezone
        timezone = pytz.timezone(timezones[0])

        ts = data.timeseries[key].series
        statistics: list[DataPoint] = []

        _LOGGER.debug("Converting %d total data points from API response", len(ts))

        skipped_count = 0
        for d in ts:
            if d.bill_read is None or d.display_unit is None:
                skipped_count += 1
                continue

            statistics.append(
                DataPoint(
                    dt=timezone.localize(d.date),
                    reading=d.bill_read,
                    unit=d.display_unit,
                ),
            )

        _LOGGER.debug(
            "After filtering: %d valid points "
            "(skipped %d points due to missing bill_read or display_unit)",
            len(statistics),
            skipped_count,
        )
        statistics.sort(key=lambda d: d.dt)

        return statistics

    async def read_historical_data_one_day(
        self,
        client: Client,
        date: datetime.datetime,
        aggregation: AggregationLevel = AggregationLevel.HOURLY,
        units: RequestUnits | None = None,
    ) -> list[DataPoint]:
        """Retrieve historical water readings for a requested day.

        Args:
            client: The authenticated API client.
            date: The date to retrieve data for.
            aggregation: Granularity level (default: HOURLY).
                         Use QUARTER_HOURLY for 15-minute resolution.
            units: Preferred units for response (e.g., RequestUnits.GALLONS).
        """
        params: dict[str, str | bool] = {
            "source": "barnacle",
            "aggregate": aggregation.value,
            "combine": "true",
            "perspective": "billing",
            "display_minutes": True,
            "display_hours": True,
            "display_days": True,
            "date": date.strftime("%m/%d/%Y"),
            "furthest_zoom": "hr",
            "display_weeks": True,
            "units": (units.value if units is not None else DEFAULT_REQUEST_UNITS),
        }

        query: dict[str, object] = {
            "params": params,
            "query": {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}},
        }
        raw_data = await client.request(
            path=CONSUMPTION_ENDPOINT,
            method="post",
            json=query,
        )

        _LOGGER.debug(
            "API Response for %s: %d bytes",
            date.strftime("%Y-%m-%d"),
            len(raw_data) if raw_data else 0,
        )
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Raw response (first 1000 chars): %s",
                raw_data[:1000] if raw_data else "None",
            )

        # The API signals "no data for this date" in three ways:
        #   '' or whitespace-only, '""' (JSON-encoded empty string), or 'null'.
        # All three are treated as empty so the daily loop can skip them cleanly.
        stripped = raw_data.strip() if raw_data else ""
        if not stripped or stripped in ('""', "null"):
            date_str = date.strftime("%Y-%m-%d")
            msg = f"Empty/null response from Eye on Water API for {date_str}"
            raise EyeOnWaterResponseIsEmpty(msg)

        _LOGGER.debug("Received %d bytes from API for date %s", len(raw_data), date)

        try:
            data = HistoricalData.model_validate_json(raw_data)
        except ValidationError as e:
            # A json_invalid error with empty input means the API returned an
            # empty or null body that slipped past the stripped-string check above.
            # ErrorDetails (pydantic_core TypedDict) has Any-typed fields; annotate
            # errors explicitly so pyright resolves .get() calls.
            errors: list[dict[str, Any]] = cast(list[dict[str, Any]], e.errors())
            if (
                errors
                and errors[0].get("type") == "json_invalid"
                and not errors[0].get("input", "SENTINEL")
            ):
                msg = (
                    f"Empty/null JSON from Eye on Water API for "
                    f"{date.strftime('%Y-%m-%d')}"
                )
                _LOGGER.debug(msg)
                raise EyeOnWaterResponseIsEmpty(msg) from e
            _LOGGER.error(
                "Pydantic validation error for %s: %s",
                date.strftime("%Y-%m-%d"),
                e,
            )
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug(
                    "Raw API response (first 1000 chars): %s",
                    raw_data[:1000] if raw_data else "None",
                )
            msg = f"Unexpected EOW response {e}"
            raise EyeOnWaterAPIError(msg) from e

        key = f"{self.meter_uuid},0"
        if key not in data.timeseries:
            available_keys = list(data.timeseries.keys())
            msg = f"Meter {key} not found in timeseries keys: {available_keys}"
            _LOGGER.debug(msg)
            raise EyeOnWaterResponseIsEmpty(msg)

        _LOGGER.debug(
            "Found timeseries for %s, series has %d points",
            key,
            len(data.timeseries[key].series),
        )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.convert, data, key)

    async def read_historical_data_range_export(
        self,
        client: Client,
        days_to_load: int,
        *,
        include_today: bool = True,
        export_resolution: str = "hourly",
        export_unit: str = "Gallons",
        max_retries: int = 30,
        poll_interval: float = 2.0,
    ) -> list[DataPoint]:
        """Retrieve historical data via the export range API."""
        if days_to_load < 1:
            msg = f"days_to_load must be at least 1, got {days_to_load}"
            raise ValueError(msg)
        if max_retries < 1:
            msg = f"max_retries must be at least 1, got {max_retries}"
            raise ValueError(msg)
        if poll_interval < 0:
            msg = f"poll_interval must be non-negative, got {poll_interval}"
            raise ValueError(msg)

        today = datetime.datetime.now(tz=pytz.UTC).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        if include_today:
            end_date = today
            start_date = today - datetime.timedelta(days=max(days_to_load - 1, 0))
        else:
            end_date = today - datetime.timedelta(days=1)
            start_date = end_date - datetime.timedelta(days=max(days_to_load - 1, 0))

        params = {
            "export_unit": export_unit,
            "site": "residential",
            "export_resolution": export_resolution,
            "start-date": start_date.strftime("%m/%d/%Y"),
            "end-date": end_date.strftime("%m/%d/%Y"),
            "meter_uuid": self.meter_uuid,
            "row-format": "range",
            "export_all": "false",
            "_": int(time.time() * 1000),
        }

        raw = await client.request(
            path=EXPORT_INIT_ENDPOINT,
            method="get",
            params=params,
        )
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            msg = f"Unexpected export initiate response: {raw[:200]}"
            raise EyeOnWaterAPIError(msg) from exc

        task_id = payload.get("task_id")
        if not task_id:
            msg = f"Export task id not found in response: {payload}"
            raise EyeOnWaterAPIError(msg)
        _LOGGER.debug(
            "Initiated export for meter %s with task_id %s",
            self.meter_uuid,
            task_id,
        )

        status = await self._poll_export_task(
            client, task_id, max_retries, poll_interval
        )

        result = status.get("result")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, ValueError):
                result = None
        if not isinstance(result, dict) or "url" not in result:
            msg = f"Export result missing URL: {status}"
            raise EyeOnWaterAPIError(msg)

        export_path = self._normalize_export_path(result["url"])
        raw_csv = await client.request(path=export_path, method="get")
        _LOGGER.debug(
            "Downloaded export CSV for task %s: %d bytes", task_id, len(raw_csv)
        )
        points = self._parse_export_csv(raw_csv)
        _LOGGER.debug("Parsed %d export data points for task %s", len(points), task_id)
        return points

    async def _poll_export_task(
        self,
        client: Client,
        task_id: str,
        max_retries: int,
        poll_interval: float,
    ) -> dict[str, Any]:
        """Poll export task until done, error, or timeout."""
        status: dict[str, Any] | None = None
        for attempt in range(max_retries):
            if attempt:
                await asyncio.sleep(poll_interval)
            status_raw = await client.request(
                path=f"{EXPORT_STATUS_ENDPOINT}{task_id}",
                method="get",
                params={"_": int(time.time() * 1000)},
            )
            try:
                status = json.loads(status_raw)
            except (json.JSONDecodeError, ValueError):
                status = None
            state = status.get("state") if isinstance(status, dict) else None
            _LOGGER.debug(
                "Export poll %d/%d for task %s returned state %s",
                attempt + 1,
                max_retries,
                task_id,
                state,
            )
            if not status:
                continue
            if state == "done":
                return status
            if state == "error":
                msg = status.get("message", "Export task error")
                raise EyeOnWaterAPIError(msg)

        msg = f"Export task did not complete: {status}"
        raise EyeOnWaterAPIError(msg)

    @staticmethod
    def _normalize_export_path(export_url: str) -> str:
        """Normalize export URLs into a request path."""
        if export_url.startswith("/"):
            return export_url
        if export_url.startswith(("http://", "https://")):
            parsed = urlparse(export_url)
            if parsed.path:
                path = parsed.path
                if parsed.query:
                    path = f"{path}?{parsed.query}"
                return path
        msg = f"Unsupported export url format: {export_url}"
        raise EyeOnWaterAPIError(msg)

    def _parse_export_csv(self, raw_csv: str) -> list[DataPoint]:
        """Parse range export CSV into data points."""
        if not raw_csv:
            return []

        reader = csv.DictReader(raw_csv.splitlines())
        points: list[DataPoint] = []
        for row in reader:
            read_time = row.get("Read_Time") or row.get("Read Time")
            timezone_name = row.get("Timezone") or "UTC"
            read_value = row.get("Read")
            read_unit = row.get("Read_Unit") or row.get("Read Unit") or row.get("Unit")
            flow_value = row.get("Flow")
            if not read_time or read_value is None or not read_unit:
                continue
            try:
                dt_value = self._parse_export_datetime(read_time)
                timezone = pytz.timezone(timezone_name)
                reading = float(read_value)
                flow = float(flow_value) if flow_value not in (None, "") else None  # type: ignore[arg-type]
            except (ValueError, KeyError, pytz.UnknownTimeZoneError):
                _LOGGER.warning("Skipping unparsable CSV row: %s", row)
                continue
            points.append(
                DataPoint(
                    dt=timezone.localize(dt_value),
                    reading=reading,
                    unit=read_unit,
                    flow_value=flow,
                )
            )

        points.sort(key=lambda d: d.dt)
        return points

    @staticmethod
    def _parse_export_datetime(value: str) -> datetime.datetime:
        """Parse export timestamps with the formats observed in EOW exports."""
        for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p"):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.datetime.fromisoformat(value)
        except ValueError as exc:
            msg = f"Unrecognized export datetime: {value}"
            raise ValueError(msg) from exc
