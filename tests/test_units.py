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

    assert deduce_native_units(EOWUnits.UNIT_CUBIC_METER) == NativeUnits.cm
    assert deduce_native_units(EOWUnits.UNIT_CM) == NativeUnits.cm

    assert deduce_native_units(EOWUnits.UNIT_GAL) == NativeUnits.gal
    assert deduce_native_units(EOWUnits.UNIT_KGAL) == NativeUnits.gal
    assert deduce_native_units(EOWUnits.UNIT_100_GAL) == NativeUnits.gal
    assert deduce_native_units(EOWUnits.UNIT_10_GAL) == NativeUnits.gal

    assert deduce_native_units(EOWUnits.UNIT_CF) == NativeUnits.cf
    assert deduce_native_units(EOWUnits.UNIT_CUBIC_FEET) == NativeUnits.cf
    assert deduce_native_units(EOWUnits.UNIT_CCF) == NativeUnits.cf

    with pytest.raises(EyeOnWaterUnitError):
        assert deduce_native_units("hey")


def test_convert_units():
    """Test units conversion."""
    assert convert_to_native(NativeUnits.gal, EOWUnits.UNIT_GAL, 1.0) == 1.0
    assert convert_to_native(NativeUnits.gal, EOWUnits.UNIT_KGAL, 1.0) == pytest.approx(
        1000.0
    )
    assert convert_to_native(
        NativeUnits.gal, EOWUnits.UNIT_100_GAL, 1.0
    ) == pytest.approx(100.0)
    assert convert_to_native(
        NativeUnits.gal, EOWUnits.UNIT_10_GAL, 1.0
    ) == pytest.approx(10.0)
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(
            NativeUnits.gal, EOWUnits.UNIT_CF, 1.0
        ) == pytest.approx(10.0)

    assert convert_to_native(NativeUnits.cf, EOWUnits.UNIT_CF, 1.0) == 1.0
    assert convert_to_native(NativeUnits.cf, EOWUnits.UNIT_CUBIC_FEET, 1.0) == 1.0
    assert convert_to_native(NativeUnits.cf, EOWUnits.UNIT_CCF, 1.0) == pytest.approx(
        100.0
    )
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(NativeUnits.cf, EOWUnits.UNIT_GAL, 1.0)

    assert convert_to_native(NativeUnits.cm, EOWUnits.UNIT_CM, 1.0) == 1.0
    assert convert_to_native(NativeUnits.cm, EOWUnits.UNIT_CUBIC_METER, 1.0) == 1.0
    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native(NativeUnits.cm, EOWUnits.UNIT_GAL, 1.0)

    with pytest.raises(EyeOnWaterUnitError):
        assert convert_to_native("hey", EOWUnits.UNIT_GAL, 1.0)
