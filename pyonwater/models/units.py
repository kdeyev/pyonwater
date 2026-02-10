"""Supported EOW units and aggregation levels."""

from __future__ import annotations

from enum import Enum


class EOWUnits(str, Enum):
    """Enum of supported EOW units (response format)."""

    UNIT_GAL = "GAL"
    UNIT_100_GAL = "100 GAL"
    UNIT_10_GAL = "10 GAL"
    UNIT_CF = "CF"
    UNIT_10_CF = "10 CF"
    UNIT_CUBIC_FEET = "CUBIC_FEET"
    UNIT_CCF = "CCF"
    UNIT_KGAL = "KGAL"
    UNIT_CM = "CM"
    UNIT_CUBIC_METER = "CUBIC_METER"
    UNIT_LITER = "LITER"
    UNIT_LITERS = "Liters"
    UNIT_LITER_LC = "Liter"


class NativeUnits(str, Enum):
    """Enum of supported native units."""

    GAL = "gal"
    CF = "cf"
    CM = "cm"


class RequestUnits(str, Enum):
    """Enum of units for API requests (different from response units)."""

    GALLONS = "gallons"
    CUBIC_FEET = "cf"
    CCF = "ccf"
    LITERS = "liters"
    CUBIC_METERS = "cm"
    IMPERIAL_GALLONS = "imp"
    OIL_BARRELS = "oil_barrel"
    FLUID_BARRELS = "fluid_barrel"


class AggregationLevel(str, Enum):
    """Enum of supported aggregation levels for consumption API.

    Each level has a corresponding aggregate_group strftime format
    that the API uses internally.
    """

    QUARTER_HOURLY = "hr"  # 15-minute intervals, group: %Y-%m-%d %H:%i:00
    HOURLY = "hourly"  # 1-hour intervals, group: %Y-%m-%d %H:00:00
    DAILY = "daily"  # 1-day intervals, group: %Y-%m-%d
    WEEKLY = "weekly"  # 7-day intervals, group: %Y-%m-%d
    MONTHLY = "monthly"  # 1-month intervals, group: %Y-%m
    YEARLY = "yearly"  # 1-year intervals, group: %Y
