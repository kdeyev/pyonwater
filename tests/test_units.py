"""Tests for units conversion."""  # nosec: B101, B106

from typing import Any, cast

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

    assert (
        deduce_native_units(EOWUnits.UNIT_CUBIC_METER) == NativeUnits.CM
    )  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_CM) == NativeUnits.CM  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_LITER) == NativeUnits.CM  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_LITERS) == NativeUnits.CM  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_LITER_LC) == NativeUnits.CM  # nosec: B101

    assert deduce_native_units(EOWUnits.UNIT_GAL) == NativeUnits.GAL  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_KGAL) == NativeUnits.GAL  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_100_GAL) == NativeUnits.GAL  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_10_GAL) == NativeUnits.GAL  # nosec: B101

    assert deduce_native_units(EOWUnits.UNIT_CF) == NativeUnits.CF  # nosec: B101
    assert (
        deduce_native_units(EOWUnits.UNIT_CUBIC_FEET) == NativeUnits.CF
    )  # nosec: B101
    assert deduce_native_units(EOWUnits.UNIT_CCF) == NativeUnits.CF  # nosec: B101

    with pytest.raises(EyeOnWaterUnitError):
        deduce_native_units(cast(Any, "hey"))


def test_convert_units() -> None:
    """Test units conversion."""
    result = convert_to_native(NativeUnits.GAL, EOWUnits.UNIT_GAL, 1.0)
    assert result == 1.0  # nosec: B101

    approx_1000 = pytest.approx(1000.0)  # type: ignore[reportUnknownMemberType]
    result = convert_to_native(NativeUnits.GAL, EOWUnits.UNIT_KGAL, 1.0)
    assert result == approx_1000  # nosec: B101

    approx_100 = pytest.approx(100.0)  # type: ignore[reportUnknownMemberType]
    result = convert_to_native(NativeUnits.GAL, EOWUnits.UNIT_100_GAL, 1.0)
    assert result == approx_100  # nosec: B101

    approx_10 = pytest.approx(10.0)  # type: ignore[reportUnknownMemberType]
    result = convert_to_native(NativeUnits.GAL, EOWUnits.UNIT_10_GAL, 1.0)
    assert result == approx_10  # nosec: B101

    with pytest.raises(EyeOnWaterUnitError):
        approx_10_err = pytest.approx(10.0)  # type: ignore[reportUnknownMemberType]
        result = convert_to_native(NativeUnits.GAL, EOWUnits.UNIT_CF, 1.0)
        assert result == approx_10_err  # nosec: B101

    result = convert_to_native(NativeUnits.CF, EOWUnits.UNIT_CF, 1)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CF, EOWUnits.UNIT_CUBIC_FEET, 1)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CF, EOWUnits.UNIT_CCF, 1.0)
    assert result == 100.0  # nosec: B101
    with pytest.raises(EyeOnWaterUnitError):
        convert_to_native(NativeUnits.CF, EOWUnits.UNIT_GAL, 1.0)

    result = convert_to_native(NativeUnits.CM, EOWUnits.UNIT_CM, 1.0)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CM, EOWUnits.UNIT_CUBIC_METER, 1.0)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CM, EOWUnits.UNIT_LITER, 1000.0)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CM, EOWUnits.UNIT_LITERS, 1000.0)
    assert result == 1.0  # nosec: B101
    result = convert_to_native(NativeUnits.CM, EOWUnits.UNIT_LITER_LC, 1000.0)
    assert result == 1.0  # nosec: B101

    with pytest.raises(EyeOnWaterUnitError):
        convert_to_native(NativeUnits.CM, EOWUnits.UNIT_GAL, 1.0)

    with pytest.raises(EyeOnWaterUnitError):
        convert_to_native(cast(Any, "hey"), EOWUnits.UNIT_GAL, 1.0)
