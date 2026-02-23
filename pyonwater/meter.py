"""EyeOnWater API integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING

from .exceptions import EyeOnWaterException
from .models import DataPoint
from .models.eow_historical_models import AtAGlanceData
from .models.units import AggregationLevel, RequestUnits
from .units import EOWUnits, convert_to_native, deduce_native_units

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client
    from .meter_reader import MeterReader
    from .models import MeterInfo, Reading

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
        self,
        client: Client,
        days_to_load: int,
        aggregation: AggregationLevel = AggregationLevel.HOURLY,
        units: RequestUnits | None = None,
        end_date: datetime | None = None,
    ) -> list[DataPoint]:
        """Read historical data for N last days.

        Args:
            client: The authenticated API client.
            days_to_load: Number of days of history to retrieve.
            aggregation: Granularity level (default: HOURLY).
                         Use QUARTER_HOURLY for 15-minute resolution.
            units: Preferred units for response (optional).
            end_date: Optional end date (defaults to today if not provided).
        """
        historical_data = await self._reader.read_historical_data(
            client=client,
            days_to_load=days_to_load,
            aggregation=aggregation,
            units=units,
            end_date=end_date,
        )

        historical_data = [self._convert_to_native(dp) for dp in historical_data]

        if not self.last_historical_data:
            self.last_historical_data = historical_data
        elif historical_data and self.last_historical_data:
            if historical_data[-1].dt > self.last_historical_data[-1].dt:
                self.last_historical_data = historical_data
            elif historical_data[-1].reading == self.last_historical_data[-1].reading:
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

    @property
    def last_read_time(self) -> datetime | None:
        """Return the time of the most recent meter read.

        Sourced from ``meter.last_read_time`` in the new_search response.
        Returns ``None`` when meter data has not been fetched yet or the field
        is absent in the API response.
        """
        if self._meter_info and self._meter_info.meter:
            return self._meter_info.meter.last_read_time
        return None

    @property
    def communication_seconds(self) -> int | None:
        """Return the meter's data transmission interval in seconds.

        Typical values: 86400 (daily), 3600 (hourly), 900 (15-minute).
        Sourced from ``meter.communication_seconds`` in the new_search response.
        Returns ``None`` when meter data has not been fetched or the field is
        absent.
        """
        if self._meter_info and self._meter_info.meter:
            return self._meter_info.meter.communication_seconds
        return None

    @property
    def next_update(self) -> datetime | None:
        """Return the estimated time of the next meter data update.

        Computed as ``last_read_time + communication_seconds``.  This matches
        the "Next Update" value shown on the EyeOnWater dashboard (within a few
        minutes, as the exact transmission schedule can vary).

        Returns ``None`` when either ``last_read_time`` or
        ``communication_seconds`` is unavailable.
        """
        lrt = self.last_read_time
        cs = self.communication_seconds
        if lrt is None or cs is None:
            return None
        return lrt + timedelta(seconds=cs)

    async def read_at_a_glance(
        self,
        client: Client,
    ) -> AtAGlanceData:
        """Retrieve quick summary statistics.

        Returns per-day usage for this week and last week, plus a rolling
        daily average.  Units and aggregation are determined server-side;
        use ``read_historical_data`` for unit/aggregation control.

        Args:
            client: The authenticated API client.
        """
        return await self._reader.read_at_a_glance(client=client)
