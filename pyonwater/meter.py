"""EyeOnWater API integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .exceptions import EyeOnWaterException

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client
    from .meter_reader import MeterReader
    from .models import DataPoint, MeterInfo, Reading

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
        self.last_historical_data: list[DataPoint] = []

        self._reading_data: Reading | None = None
        self._meter_info: MeterInfo | None = None

    @property
    def meter_uuid(self) -> str:
        """Return meter UUID."""
        return self.reader.meter_uuid

    @property
    def meter_id(self) -> str:
        """Return meter ID."""
        return self.reader.meter_id

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native measurement unit: [m^3, gal]."""
        return self.reader.native_unit_of_measurement

    async def read_meter(self, client: Client, days_to_load: int = 3) -> None:
        """Triggers an on-demand meter read and returns it when complete."""
        self._meter_info = await self.reader.read_meter(client)
        self._reading_data = self._meter_info.reading

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

    @property
    def meter_info(self) -> MeterInfo:
        """Return MeterInfo."""
        if not self._meter_info:
            msg = "Data was not fetched"
            raise EyeOnWaterException(msg)
        return self._meter_info

    @property
    def reading(self) -> float:
        """Returns the latest meter reading in me^3 or gal."""
        if not self._reading_data:
            msg = "Data was not fetched"
            raise EyeOnWaterException(msg)
        reading = self._reading_data.latest_read
        return self.reader.convert(reading.units, reading.full_read)
