"""Tests for units conversion."""


import pytest

from pyonwater import (
    EOWUnits,
    EyeOnWaterUnitError,
    NativeUnits,
    convert_to_native,
    deduce_native_units,
)


def test_deduce_native_unit():
    """Test units deducing native units."""

    assert deduce_native_units(EOWUnits.MEASUREMENT_CUBICMETERS) == NativeUnits.CM
    assert deduce_native_units(EOWUnits.MEASUREMENT_CM) == NativeUnits.CM

    assert deduce_native_units(EOWUnits.MEASUREMENT_GALLONS) == NativeUnits.GAL
    assert deduce_native_units(EOWUnits.MEASUREMENT_KILOGALLONS) == NativeUnits.GAL
    assert deduce_native_units(EOWUnits.MEASUREMENT_100_GALLONS) == NativeUnits.GAL
    assert deduce_native_units(EOWUnits.MEASUREMENT_10_GALLONS) == NativeUnits.GAL

    assert deduce_native_units(EOWUnits.MEASUREMENT_CF) == NativeUnits.CF
    assert deduce_native_units(EOWUnits.MEASUREMENT_CUBIC_FEET) == NativeUnits.CF
    assert deduce_native_units(EOWUnits.MEASUREMENT_CCF) == NativeUnits.CF

    with pytest.raises(EyeOnWaterUnitError):
        assert deduce_native_units("hey")


def test_convert_units():
    """Test units conversion."""
    assert convert_to_native(
        NativeUnits.GAL, EOWUnits.MEASUREMENT_GALLONS, 1.0
    ) == pytest.approx(1.0)
    assert convert_to_native(
        NativeUnits.GAL, EOWUnits.MEASUREMENT_KILOGALLONS, 1.0
    ) == pytest.approx(1000.0)
    assert convert_to_native(
        NativeUnits.GAL, EOWUnits.MEASUREMENT_100_GALLONS, 1.0
    ) == pytest.approx(100.0)
    assert convert_to_native(
        NativeUnits.GAL, EOWUnits.MEASUREMENT_10_GALLONS, 1.0
    ) == pytest.approx(10.0)
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(
            NativeUnits.GAL, EOWUnits.MEASUREMENT_CF, 1.0
        ) == pytest.approx(10.0)

    assert convert_to_native(
        NativeUnits.CF, EOWUnits.MEASUREMENT_CF, 1.0
    ) == pytest.approx(1.0)
    assert convert_to_native(
        NativeUnits.CF, EOWUnits.MEASUREMENT_CUBIC_FEET, 1.0
    ) == pytest.approx(1.0)
    assert convert_to_native(
        NativeUnits.CF, EOWUnits.MEASUREMENT_CCF, 1.0
    ) == pytest.approx(100.0)
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(NativeUnits.CF, EOWUnits.MEASUREMENT_GALLONS, 1.0)

    assert convert_to_native(
        NativeUnits.CM, EOWUnits.MEASUREMENT_CM, 1.0
    ) == pytest.approx(1.0)
    assert convert_to_native(
        NativeUnits.CM, EOWUnits.MEASUREMENT_CUBICMETERS, 1.0
    ) == pytest.approx(1.0)
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(NativeUnits.CM, EOWUnits.MEASUREMENT_GALLONS, 1.0)

    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native("hey", EOWUnits.MEASUREMENT_GALLONS, 1.0)
