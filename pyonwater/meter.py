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
from .meter_reader import MeterReader
from .models import DataPoint

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


class Meter:
    """Class represents meter state."""

    def __init__(self, reader: MeterReader) -> None:
        """Initialize the meter."""
        self.reader = reader
        self.meter_info = None
        self.last_historical_data: list[DataPoint] = []
        self.reading_data = None

    @property
    def meter_uuid(self) -> str:
        return self.reader.meter_uuid

    @property
    def meter_id(self) -> str:
        return self.reader.meter_id

    async def read_meter(self, client: Client, days_to_load: int = 3) -> dict[str, Any]:
        """Triggers an on-demand meter read and returns it when complete."""

        self.meter_info = await self.reader.read_meter(client)
        self.reading_data = self.meter_info["register_0"]

        try:
            # TODO: identify missing days and request only missing dates.
            historical_data = await self.reader.read_historical_data(
                days_to_load=days_to_load,
                client=client,
            )
            if not self.last_historical_data:
                self.last_historical_data = historical_data
            elif (
                historical_data
                and historical_data[-1].dt > self.last_historical_data[-1].dt
            ):
                # Take newer data
                self.last_historical_data = historical_data
            elif historical_data[-1]["reading"] == self.last_historical_data[-1][
                "reading"
            ] and len(historical_data) > len(self.last_historical_data):
                # If it the same date - take more data
                self.last_historical_data = historical_data

        except EyeOnWaterResponseIsEmpty:
            self.last_historical_data = []

    @property
    def attributes(self):
        """Define attributes."""
        return self.meter_info

    def get_flags(self, flag) -> bool:
        """Define flags."""
        flags = self.reading_data["flags"]
        if flag not in flags:
            msg = f"Cannot find {flag} field"
            raise EyeOnWaterAPIError(msg)
        return flags[flag]

    @property
    def reading(self) -> float:
        """Returns the latest meter reading in gal."""
        reading = self.reading_data["latest_read"]
        if READ_UNITS_FIELD not in reading:
            msg = "Cannot find read units in reading data"
            raise EyeOnWaterAPIError(msg)
        read_unit = reading[READ_UNITS_FIELD]
        read_unit_upper = read_unit.upper()
        amount = float(reading[READ_AMOUNT_FIELD])
        return self.reader.convert(read_unit_upper, amount)
