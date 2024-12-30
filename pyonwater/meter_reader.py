"""EyeOnWater API integration."""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError
import pytz

from .exceptions import EyeOnWaterAPIError, EyeOnWaterResponseIsEmpty
from .models import DataPoint, HistoricalData, MeterInfo

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

    pass

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"

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
            raise Exception(msg)

        try:
            meter_info = MeterInfo.model_validate(meters[0]["_source"])
        except ValidationError as e:
            msg = f"Unexpected EOW response {e} with payload {meters[0]['_source']}"
            raise EyeOnWaterAPIError(msg) from e

        return meter_info

    async def read_historical_data(
        self, client: Client, days_to_load: int
    ) -> list[DataPoint]:
        """Retrieve historical data for today and past N days."""
        today = datetime.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        date_list = [today - datetime.timedelta(days=x) for x in range(0, days_to_load)]
        date_list.reverse()

        _LOGGER.info(
            f"requesting historical statistics for {self.meter_uuid} on {date_list}",
        )

        statistics = []

        for date in date_list:
            _LOGGER.info(
                f"requesting historical statistics for {self.meter_uuid} on {date}",
            )
            try:
                statistics += await self.read_historical_data_one_day(
                    client=client, date=date
                )
            except EyeOnWaterResponseIsEmpty:
                continue

        return statistics

    def convert(self, data: HistoricalData, key: str) -> list[DataPoint]:
        """Convert the raw data into a list of DataPoint objects."""

        timezones = data.hit.meter_timezone
        timezone = pytz.timezone(timezones[0])

        ts = data.timeseries[key].series
        statistics = []
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
    ) -> list[DataPoint]:
        """Retrieve the historical hourly water readings for a requested day."""
        query = {
            "params": {
                "source": "barnacle",
                "aggregate": "hourly",
                "units": "cm",  # This parameter seems to be ignored and does not affect the output values :-)
                "combine": "true",
                "perspective": "billing",
                "display_minutes": True,
                "display_hours": True,
                "display_days": True,
                "date": date.strftime("%m/%d/%Y"),
                "furthest_zoom": "hr",
                "display_weeks": True,
            },
            "query": {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}},
        }
        raw_data = await client.request(
            path=CONSUMPTION_ENDPOINT,
            method="post",
            json=query,
        )
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
