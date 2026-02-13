"""EyeOnWater API integration."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError
import pytz

from .exceptions import EyeOnWaterAPIError, EyeOnWaterResponseIsEmpty
from .models import DataPoint, HistoricalData, MeterInfo
from .models.eow_historical_models import AtAGlanceData
from .models.units import AggregationLevel, RequestUnits

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"
AT_A_GLANCE_ENDPOINT = "/api/2/residential/at_a_glance"

# EyeOnWater API Contract Requirements
# =====================================
# The consumption endpoint has strict requirements for request parameters.
# Missing ANY required parameter will cause the API to return an empty response ("").
#
# REQUIRED Parameters for /api/2/residential/consumption:
#   - source: Must be "barnacle"
#   - aggregate: Aggregation level (e.g., "hourly", "daily", etc.)
#   - units: Units for response (e.g., "cm", "gal") - CRITICAL: Cannot be omitted
#   - perspective: Must be "billing"
#   - combine: Must be "true"
#   - date: Date in format MM/DD/YYYY
#   - display_minutes, display_hours, display_days, display_weeks: All boolean
#   - furthest_zoom: Typically "hr"
#
# Query structure:
#   {"query": {"terms": {"meter.meter_uuid": [<uuid>]}}}
#
# Historical Context:
#   PR #36 (Feb 2026) made 'units' conditional, causing all requests with units=None
#   to return empty responses. Always include all required parameters with defaults.

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

        today = datetime.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        date_list = [today - datetime.timedelta(days=x) for x in range(0, days_to_load)]
        date_list.reverse()

        _LOGGER.debug(
            "requesting historical statistics for %s on %s",
            self.meter_uuid,
            date_list,
        )

        statistics: list[DataPoint] = []

        for date in date_list:
            _LOGGER.debug(
                "requesting historical statistics for %s on %s",
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
            "units": (
                units.value if units is not None else "cm"
            ),  # Default to cm (cubic meters) if not specified
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

        # Handle empty responses from API
        if not raw_data or not raw_data.strip():
            msg = "Empty response from Eye on Water API"
            raise EyeOnWaterResponseIsEmpty(msg)

        _LOGGER.debug("Received %d bytes from API for date %s", len(raw_data), date)

        try:
            data = HistoricalData.model_validate_json(raw_data)
        except ValidationError as e:
            _LOGGER.error("Pydantic validation error: %s", e)
            _LOGGER.error("Validation errors detail: %s", e.errors())
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
            _LOGGER.error(msg)
            raise EyeOnWaterResponseIsEmpty(msg)

        _LOGGER.debug(
            "Found timeseries for %s, series has %d points",
            key,
            len(data.timeseries[key].series),
        )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.convert, data, key)

    async def read_at_a_glance(
        self,
        client: Client,
        units: RequestUnits | None = None,
    ) -> AtAGlanceData:
        """Retrieve quick summary statistics from at_a_glance endpoint.

        Returns usage summaries: this_week, last_week, and average daily usage.

        Args:
            client: The authenticated API client.
            units: Preferred units for response (optional, defaults to cm).

        Returns:
            AtAGlanceData with this_week, last_week, and average values.

        Note:
            The at_a_glance API may have similar parameter requirements as
            consumption API. We provide a default unit value to avoid empty
            responses, though it appears more lenient than consumption endpoint.
        """
        params: dict[str, str] = {
            "source": "barnacle",
            "perspective": "billing",
            "units": (
                units.value if units is not None else "cm"
            ),  # Default to cm for consistency
        }

        query: dict[str, Any] = {
            "params": params,
            "query": {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}},
        }
        raw_data = await client.request(
            path=AT_A_GLANCE_ENDPOINT,
            method="post",
            json=query,
        )
        try:
            data = AtAGlanceData.model_validate_json(raw_data)
        except ValidationError as e:
            msg = f"Unexpected at_a_glance response {e}"
            raise EyeOnWaterAPIError(msg) from e

        return data
