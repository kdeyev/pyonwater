"""EyeOnWater API integration."""
from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError
import pytz

from .exceptions import EyeOnWaterAPIError, EyeOnWaterResponseIsEmpty
from .models import DataPoint, EOWUnits, HistoricalData, MeterInfo

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client

    pass

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"

_LOGGER = logging.getLogger(__name__)


class MeterReader:
    """Class represents meter reader."""

    def __init__(
        self,
        meter_uuid: str,
        meter_id: str,
        metric_measurement_system: bool,
    ) -> None:
        """Initialize the meter."""
        self.meter_uuid = meter_uuid
        self.meter_id: str = meter_id

        self.metric_measurement_system = metric_measurement_system
        self.native_unit_of_measurement = (
            "m\u00b3" if self.metric_measurement_system else "gal"
        )

    async def read_meter(self, client: Client) -> MeterInfo:
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
            meter_info = MeterInfo.parse_obj(meters[0]["_source"])
        except ValidationError as e:
            msg = f"Unexpected EOW response {e}"
            raise EyeOnWaterAPIError(msg) from e

        return meter_info

    def convert(self, read_unit: str, value: float) -> float:
        """Convert reading to Cubic Meter or Gallons."""
        if self.metric_measurement_system:
            if read_unit in [EOWUnits.MEASUREMENT_CUBICMETERS, EOWUnits.MEASUREMENT_CM]:
                pass
            else:
                msg = f"Unsupported measurement unit: {read_unit}"
                raise EyeOnWaterAPIError(
                    msg,
                )
        else:
            if read_unit == EOWUnits.MEASUREMENT_KILOGALLONS:
                value = value * 1000
            elif read_unit == EOWUnits.MEASUREMENT_100_GALLONS:
                value = value * 100
            elif read_unit == EOWUnits.MEASUREMENT_10_GALLONS:
                value = value * 10
            elif read_unit == EOWUnits.MEASUREMENT_GALLONS:
                pass
            elif read_unit == EOWUnits.MEASUREMENT_CCF:
                value = value * 748.052
            elif read_unit in [
                EOWUnits.MEASUREMENT_CF,
                EOWUnits.MEASUREMENT_CUBIC_FEET,
            ]:
                value = value * 7.48052
            else:
                msg = f"Unsupported measurement unit: {read_unit}"
                raise EyeOnWaterAPIError(
                    msg,
                )
        return value

    async def read_historical_data(
        self,
        client: Client,
        days_to_load: int,
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
                    date=date,
                    client=client,
                )
            except EyeOnWaterResponseIsEmpty:
                continue

        return statistics

    async def read_historical_data_one_day(
        self,
        client: Client,
        date: datetime.datetime,
    ) -> list[DataPoint]:
        """Retrieve the historical hourly water readings for a requested day."""
        if self.metric_measurement_system:
            units = "CM"
        else:
            units = self.native_unit_of_measurement.upper()

        query = {
            "params": {
                "source": "barnacle",
                "aggregate": "hourly",
                "units": units,
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
            data = HistoricalData.parse_raw(raw_data)
        except ValidationError as e:
            msg = f"Unexpected EOW response {e}"
            raise EyeOnWaterAPIError(msg) from e

        key = f"{self.meter_uuid},0"
        if key not in data.timeseries:
            msg = f"Meter {key} not found"
            raise EyeOnWaterResponseIsEmpty(msg)

        timezones = data.hit.meter_timezone
        timezone = pytz.timezone(timezones[0])

        ts = data.timeseries[key].series
        statistics = []
        for d in ts:
            response_unit = d.display_unit.upper()
            statistics.append(
                DataPoint(
                    dt=timezone.localize(d.date),
                    reading=self.convert(response_unit, d.bill_read),
                ),
            )

        statistics.sort(key=lambda d: d.dt)

        return statistics
