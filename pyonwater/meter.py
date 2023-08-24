"""EyeOnWater API integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .client import Client
from .exceptions import EyeOnWaterException, EyeOnWaterResponseIsEmpty
from .meter_reader import MeterReader
from .models import DataPoint, Flags, MeterInfo, Reading

if TYPE_CHECKING:
    pass

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"

MEASUREMENT_GALLONS = "GAL"
MEASUREMENT_100_GALLONS = "100 GAL"
MEASUREMENT_10_GALLONS = "10 GAL"
MEASUREMENT_CF = ["CF", "CUBIC_FEET"]
MEASUREMENT_CCF = "CCF"
MEASUREMENT_KILOGALLONS = "KGAL"
MEASUREMENT_CUBICMETERS = ["CM", "CUBIC_METER"]


_LOGGER = logging.getLogger(__name__)


class Meter:
    """Class represents meter state."""

    def __init__(self, reader: MeterReader) -> None:
        """Initialize the meter."""
        self.reader = reader
        self.meter_info: MeterInfo | None = None
        self.last_historical_data: list[DataPoint] = []
        self.reading_data: Reading | None = None

    @property
    def meter_uuid(self) -> str:
        """Return meter UUID"""
        return self.reader.meter_uuid

    @property
    def meter_id(self) -> str:
        """Return meter ID"""
        return self.reader.meter_id

    async def read_meter(self, client: Client, days_to_load: int = 3) -> None:
        """Triggers an on-demand meter read and returns it when complete."""

        self.meter_info = await self.reader.read_meter(client)
        self.reading_data = self.meter_info.reading

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
            elif historical_data[-1].reading == self.last_historical_data[
                -1
            ].reading and len(historical_data) > len(self.last_historical_data):
                # If it the same date - take more data
                self.last_historical_data = historical_data

        except EyeOnWaterResponseIsEmpty:
            self.last_historical_data = []

    @property
    def attributes(self) -> MeterInfo:
        """Define attributes."""
        if not self.meter_info:
            raise EyeOnWaterException("Data was not fetched")
        return self.meter_info

    @property
    def flags(self) -> Flags:
        """Define flags."""
        if not self.reading_data:
            raise EyeOnWaterException("Data was not fetched")
        return self.reading_data.flags

    @property
    def reading(self) -> float:
        """Returns the latest meter reading in gal."""
        if not self.reading_data:
            raise EyeOnWaterException("Data was not fetched")
        reading = self.reading_data.latest_read
        return self.reader.convert(reading.units, reading.full_read)
