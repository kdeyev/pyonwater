"""Supported EOW units."""

from __future__ import annotations

from enum import Enum


class EOWUnits(str, Enum):
    """Enum of supported EOW units."""

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
