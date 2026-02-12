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

_LOGGER = logging.getLogger(__name__)


class MeterReader:
    """Class represents meter reader."""

    def __init__(self, meter_uuid: str, meter_id: str) -> None:
        """Initialize the meter."""
        self.meter_uuid = meter_uuid
        self.meter_id: str = meter_id

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
            days_to_load: Number of days of history to retrieve.
            aggregation: Granularity level for data (default: HOURLY).
                         Use QUARTER_HOURLY for 15-minute resolution.
            units: Preferred units for response data (optional).
        """
        today = datetime.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        date_list = [today - datetime.timedelta(days=x) for x in range(0, days_to_load)]
        date_list.reverse()

        _LOGGER.info(
            "requesting historical statistics for %s on %s",
            self.meter_uuid,
            date_list,
        )

        statistics: list[DataPoint] = []

        for date in date_list:
            _LOGGER.info(
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
                continue

        return statistics

    def convert(self, data: HistoricalData, key: str) -> list[DataPoint]:
        """Convert the raw data into a list of DataPoint objects."""

        timezones = data.hit.meter_timezone
        timezone = pytz.timezone(timezones[0])

        ts = data.timeseries[key].series
        statistics: list[DataPoint] = []
        for d in ts:
            if d.bill_read is None or d.display_unit is None:
                continue

            statistics.append(
                DataPoint(
                    dt=timezone.localize(d.date),
                    reading=d.bill_read,
                    unit=d.display_unit,
                ),
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
        }
        if units is not None:
            params["units"] = units.value

        query: dict[str, object] = {
            "params": params,
            "query": {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}},
        }
        raw_data = await client.request(
            path=CONSUMPTION_ENDPOINT,
            method="post",
            json=query,
        )
        
        # Handle empty responses from API
        if not raw_data or not raw_data.strip():
            msg = "Empty response from Eye on Water API"
            raise EyeOnWaterResponseIsEmpty(msg)
        
        try:
            data = HistoricalData.model_validate_json(raw_data)
        except ValidationError as e:
            msg = f"Unexpected EOW response {e}"
            raise EyeOnWaterAPIError(msg) from e

        key = f"{self.meter_uuid},0"
        if key not in data.timeseries:
            msg = f"Meter {key} not found"
            raise EyeOnWaterResponseIsEmpty(msg)

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
            units: Preferred units for response (optional).

        Returns:
            AtAGlanceData with this_week, last_week, and average values.
        """
        params: dict[str, str] = {
            "source": "barnacle",
            "perspective": "billing",
        }
        if units is not None:
            params["units"] = units.value

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
