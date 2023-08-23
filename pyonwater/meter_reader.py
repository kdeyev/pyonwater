"""EyeOnWater API integration."""
from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING, Any
import urllib.parse

from dateutil import parser
import pytz
from tenacity import retry, retry_if_exception_type

from .client import Client
from .exceptions import (
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterAuthExpired,
    EyeOnWaterRateLimitError,
    EyeOnWaterResponseIsEmpty,
)

if TYPE_CHECKING:
    from aiohttp import ClientSession

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"

MEASUREMENT_GALLONS = "GAL"
MEASUREMENT_100_GALLONS = "100 GAL"
MEASUREMENT_10_GALLONS = "10 GAL"
MEASUREMENT_CF = ["CF", "CUBIC_FEET"]
MEASUREMENT_CCF = "CCF"
MEASUREMENT_KILOGALLONS = "KGAL"
MEASUREMENT_CUBICMETERS = ["CM", "CUBIC_METER"]

METER_UUID_FIELD = "meter_uuid"
READ_UNITS_FIELD = "units"
READ_AMOUNT_FIELD = "full_read"


_LOGGER = logging.getLogger(__name__)


class MeterReader:
    """Class represents meter reader."""

    def __init__(
        self,
        meter_uuid: str,
        meter_info: dict[str, Any],
        metric_measurement_system: bool,
    ) -> None:
        """Initialize the meter."""
        self.meter_uuid = meter_uuid
        self.meter_id = meter_info["meter_id"]

        self.metric_measurement_system = metric_measurement_system
        self.native_unit_of_measurement = (
            "m\u00b3" if self.metric_measurement_system else "gal"
        )

    async def read_meter(self, client: Client) -> dict[str, Any]:
        """Triggers an on-demand meter read and returns it when complete."""
        _LOGGER.debug("Requesting meter reading")

        query = {"query": {"terms": {"meter.meter_uuid": [self.meter_uuid]}}}
        data = await client.request(path=SEARCH_ENDPOINT, method="post", json=query)
        data = json.loads(data)
        meters = data["elastic_results"]["hits"]["hits"]
        if len(meters) > 1:
            msg = "More than one meter reading found"
            raise Exception(msg)

        meter_info = meters[0]["_source"]

        return meter_info

    def convert(self, read_unit_upper, amount):
        if self.metric_measurement_system:
            if read_unit_upper in MEASUREMENT_CUBICMETERS:
                pass
            else:
                msg = f"Unsupported measurement unit: {read_unit_upper}"
                raise EyeOnWaterAPIError(
                    msg,
                )
        else:
            if read_unit_upper == MEASUREMENT_KILOGALLONS:
                amount = amount * 1000
            elif read_unit_upper == MEASUREMENT_100_GALLONS:
                amount = amount * 100
            elif read_unit_upper == MEASUREMENT_10_GALLONS:
                amount = amount * 10
            elif read_unit_upper == MEASUREMENT_GALLONS:
                pass
            elif read_unit_upper == MEASUREMENT_CCF:
                amount = amount * 748.052
            elif read_unit_upper in MEASUREMENT_CF:
                amount = amount * 7.48052
            else:
                msg = f"Unsupported measurement unit: {read_unit_upper}"
                raise EyeOnWaterAPIError(
                    msg,
                )
        return amount

    async def read_historical_data(self, client: Client, days_to_load: int):
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
                    date=date, client=client
                )
            except EyeOnWaterResponseIsEmpty:
                continue

        return statistics

    async def read_historical_data_one_day(self, client: Client, date: datetime):
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
        data = await client.request(
            path=CONSUMPTION_ENDPOINT,
            method="post",
            json=query,
        )
        data = json.loads(data)

        key = f"{self.meter_uuid},0"
        if key not in data["timeseries"]:
            msg = "Response is empty"
            raise EyeOnWaterResponseIsEmpty(msg)

        timezone = data["hit"]["meter.timezone"][0]
        timezone = pytz.timezone(timezone)

        data = data["timeseries"][key]["series"]
        statistics = []
        for d in data:
            response_unit = d["display_unit"].upper()
            statistics.append(
                {
                    "dt": timezone.localize(parser.parse(d["date"])),
                    "reading": self.convert(response_unit, d["bill_read"]),
                },
            )

        statistics.sort(key=lambda d: d["dt"])

        return statistics
