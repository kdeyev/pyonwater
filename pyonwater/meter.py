"""EyeOnWater API integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .exceptions import EyeOnWaterException
from .models import DataPoint
from .units import EOWUnits, convert_to_native, deduce_native_units

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client
    from .meter_reader import MeterReader
    from .models import MeterInfo, Reading

    pass

SEARCH_ENDPOINT = "/api/2/residential/new_search"
CONSUMPTION_ENDPOINT = "/api/2/residential/consumption?eow=True"

_LOGGER = logging.getLogger(__name__)


class Meter:
    """Class represents meter state."""

    def __init__(self, reader: MeterReader, meter_info: MeterInfo) -> None:
        """Initialize the meter."""
        self._reader = reader
        self.last_historical_data: list[DataPoint] = []

        self._reading_data: Reading | None = None
        self._meter_info = meter_info
        self._reading_data = self._meter_info.reading

        self._native_unit_of_measurement = deduce_native_units(
            self._meter_info.reading.latest_read.units
        )

    @property
    def meter_uuid(self) -> str:
        """Return meter UUID."""
        return self._reader.meter_uuid

    @property
    def meter_id(self) -> str:
        """Return meter ID."""
        return self._reader.meter_id

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native measurement units."""
        return self._native_unit_of_measurement.value

    async def read_meter_info(self, client: Client) -> None:
        """Read the latest meter info."""
        self._meter_info = await self._reader.read_meter_info(client)
        self._reading_data = self._meter_info.reading

    async def read_historical_data(
        self, client: Client, days_to_load: int
    ) -> list[DataPoint]:
        """Read historical data for N last days."""
        historical_data = await self._reader.read_historical_data(
            client=client, days_to_load=days_to_load
        )

        historical_data = [self._convert_to_native(dp) for dp in historical_data]

        if not self.last_historical_data:
            self.last_historical_data = historical_data
        elif historical_data and self.last_historical_data:
            if historical_data[-1].dt > self.last_historical_data[-1].dt:
                # Take newer data
                self.last_historical_data = historical_data
            elif historical_data[-1].reading == self.last_historical_data[-1].reading:
                # If it's the same date - take more data
                if len(historical_data) > len(self.last_historical_data):
                    self.last_historical_data = historical_data

        return historical_data

    @property
    def meter_info(self) -> MeterInfo:
        """Return MeterInfo."""
        if not self._meter_info:
            msg = "Data was not fetched"
            raise EyeOnWaterException(msg)
        return self._meter_info

    @property
    def reading(self) -> DataPoint:
        """Returns the latest meter reading."""
        if not self._reading_data:
            msg = "Data was not fetched"
            raise EyeOnWaterException(msg)
        reading = self._reading_data.latest_read
        dp = DataPoint(
            dt=reading.read_time, reading=reading.full_read, unit=reading.units
        )

        return self._convert_to_native(dp)

    def _convert_to_native(self, dp: DataPoint) -> DataPoint:
        """Convert data point to meters native units"""
        native_reading = convert_to_native(
            self._native_unit_of_measurement, EOWUnits(dp.unit), dp.reading
        )
        return DataPoint(
            dt=dp.dt, reading=native_reading, unit=self._native_unit_of_measurement
        )
