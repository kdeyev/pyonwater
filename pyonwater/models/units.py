"""Supported EOW units."""

from __future__ import annotations

from enum import Enum


class EOWUnits(str, Enum):
    """Enum of supported EOW units."""

    MEASUREMENT_GALLONS = "GAL"
    MEASUREMENT_100_GALLONS = "100 GAL"
    MEASUREMENT_10_GALLONS = "10 GAL"
    MEASUREMENT_CF = "CF"
    MEASUREMENT_CUBIC_FEET = "CUBIC_FEET"
    MEASUREMENT_CCF = "CCF"
    MEASUREMENT_KILOGALLONS = "KGAL"
    MEASUREMENT_CM = "CM"
    MEASUREMENT_CUBICMETERS = "CUBIC_METER"
