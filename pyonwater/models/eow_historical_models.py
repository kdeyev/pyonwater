# ruff: noqa
"""Models for historical consumption data from EyeOnWater API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from .units import EOWUnits


class Register0EncoderItem(BaseModel):
    """Encoder dials information."""

    dials: Optional[int] = None


class Hit(BaseModel):
    """Meter and account metadata from search results."""

    meter_timezone: list[str] = Field(..., alias="meter.timezone")

    meter_communication_seconds: Optional[list[int]] = Field(
        None, alias="meter.communication_seconds"
    )
    register_0_encoder: Optional[list[Register0EncoderItem]] = Field(
        None, alias="register_0.encoder"
    )
    location_location_uuid: Optional[list[str]] = Field(
        None, alias="location.location_uuid"
    )
    meter_fluid_type: Optional[list[str]] = Field(None, alias="meter.fluid_type")
    meter_meter_id: Optional[list[str]] = Field(None, alias="meter.meter_id")
    account_full_name: Optional[list[str]] = Field(None, alias="account.full_name")
    meter_meter_uuid: Optional[list[str]] = Field(None, alias="meter.meter_uuid")
    meter_has_endpoint: Optional[list[bool]] = Field(None, alias="meter.has_endpoint")
    meter_serial_number: Optional[list[str]] = Field(None, alias="meter.serial_number")
    account_account_id: Optional[list[str]] = Field(None, alias="account.account_id")
    location_location_name: Optional[list[str]] = Field(
        None, alias="location.location_name"
    )
    service_service_id: Optional[list[str]] = Field(None, alias="service.service_id")
    register_0_serial_number: Optional[list[str]] = Field(
        None, alias="register_0.serial_number"
    )
    utility_utility_uuid: Optional[list[str]] = Field(
        None, alias="utility.utility_uuid"
    )
    account_account_uuid: Optional[list[str]] = Field(
        None, alias="account.account_uuid"
    )


class Params(BaseModel):
    """Request parameters used for the API call."""

    start_date_utc: Optional[float] = None
    date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    end_date_utc: Optional[float] = None
    compare: Optional[bool] = None
    read_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date_tz: Optional[str] = None
    aggregate: Optional[str] = None
    aggregate_group: Optional[str] = None
    perspective: Optional[str] = None
    units: Optional[EOWUnits] = None
    start_date_tz: Optional[str] = None
    adjust_to: Optional[bool] = None
    combine_group: Optional[bool] = None


class Series(BaseModel):
    """Individual data point in a time series."""

    date: datetime
    display_unit: Optional[EOWUnits] = None
    bill_read: Optional[float] = None
    end_date: Optional[datetime] = None
    meter_uuid: Optional[int] = None
    value: Optional[float] = None
    start_date: Optional[datetime] = None
    register_number: Optional[int] = None
    estimated: Optional[int] = None
    raw_read: Optional[int] = None
    unit: Optional[EOWUnits] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_flexible_date(cls, v: Any) -> datetime:
        """Parse date from various formats depending on API aggregation level.

        The API returns different date formats based on aggregation:
        - Hourly/Daily/Weekly: "YYYY-MM-DD HH:MM:SS" (space-separated,
          actual API format)
        - Daily/Weekly (ISO variant): "YYYY-MM-DDThh:mm:ss" (T-separated)
        - Date only: "YYYY-MM-DD"
        - Monthly: "YYYY-MM" (month only)
        - Yearly: "YYYY" (year only)
        """
        if isinstance(v, datetime):
            return v

        if not isinstance(v, str):
            raise ValueError(
                f"Date must be a string or datetime, got {type(v).__name__}"
            )

        # Try parsing in order of specificity
        date_formats = [
            "%Y-%m-%d %H:%M:%S",  # Actual API format: 2026-02-10 00:00:00
            "%Y-%m-%dT%H:%M:%S",  # ISO datetime:      2026-02-10T00:00:00
            "%Y-%m-%d",  # Date only:          2026-02-10
            "%Y-%m",  # Month only:         2026-02
            "%Y",  # Year only:          2026
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue

        raise ValueError(
            f"Unable to parse date '{v}'. Expected one of: "
            f"YYYY-MM-DD HH:MM:SS, YYYY-MM-DDThh:mm:ss, YYYY-MM-DD, YYYY-MM, or YYYY"
        )


class Legend(BaseModel):
    """Legend/metadata for a time series."""

    supply_zone_id: Optional[str] = None
    location_name: Optional[str] = None
    account_id: Optional[str] = None
    demand_zone_id: Optional[str] = None
    meter_id: Optional[str] = None
    full_name: Optional[str] = None
    serial_number: Optional[str] = None


class TimeSerie(BaseModel):
    """A collection of data points with optional legend."""

    series: list[Series]
    legend: Optional[Legend] = None


class HistoricalData(BaseModel):
    """Complete historical consumption data response."""

    hit: Hit
    timeseries: dict[str, TimeSerie]
    min_chart_aggregation: Optional[str] = None
    params: Optional[Params] = None
    timezone: Optional[str] = None
    min_aggregation_seconds: Optional[int] = None
    annotations: Optional[list[str]] = None


class DailyUsagePoint(BaseModel):
    """A single day's usage value in an at_a_glance response."""

    value: Optional[float] = None
    meter_count: Optional[int] = None
    date: Optional[str] = None


class AtAGlanceData(BaseModel):
    """Model for at_a_glance endpoint response.

    The endpoint is called with ``{"meter_uuid": "<uuid>"}`` and returns
    per-day usage arrays for this week and last week, plus a rolling average.

    Response shape (actual API)::

        {
          "this_week": {
            "<meter_uuid_or_null>": [
              {"value": 95.8, "meter_count": 1, "date": "2026-02-16"},
              ...
            ]
          },
          "last_week": {"<meter_uuid_or_null>": [...]},
          "average": 126.26,
          "days_in_average": 30.0,
          "in_units": "GAL",
          "display_units": "GAL"
        }
    """

    # Per-day arrays keyed by meter UUID (or "null" for single-meter requests).
    this_week: Optional[dict[str, list[DailyUsagePoint]]] = None
    last_week: Optional[dict[str, list[DailyUsagePoint]]] = None
    average: Optional[float] = None
    days_in_average: Optional[float] = None
    in_units: Optional[EOWUnits] = None
    display_units: Optional[EOWUnits] = None

    @property
    def this_week_points(self) -> list[DailyUsagePoint]:
        """Return this week's daily usage points as a flat list."""
        if not self.this_week:
            return []
        points: list[DailyUsagePoint] = []
        for daily_list in self.this_week.values():
            points.extend(daily_list)
        points.sort(key=lambda p: p.date or "")
        return points

    @property
    def last_week_points(self) -> list[DailyUsagePoint]:
        """Return last week's daily usage points as a flat list."""
        if not self.last_week:
            return []
        points: list[DailyUsagePoint] = []
        for daily_list in self.last_week.values():
            points.extend(daily_list)
        points.sort(key=lambda p: p.date or "")
        return points

    @property
    def this_week_total(self) -> Optional[float]:
        """Return total usage for this week."""
        pts = self.this_week_points
        if not pts:
            return None
        return sum(p.value for p in pts if p.value is not None)

    @property
    def last_week_total(self) -> Optional[float]:
        """Return total usage for last week."""
        pts = self.last_week_points
        if not pts:
            return None
        return sum(p.value for p in pts if p.value is not None)


__all__ = [
    "Register0EncoderItem",
    "Hit",
    "Params",
    "Series",
    "Legend",
    "TimeSerie",
    "HistoricalData",
    "DailyUsagePoint",
    "AtAGlanceData",
]
