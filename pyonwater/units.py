"""Units related tools."""
from .exceptions import EyeOnWaterUnitError
from .models import EOWUnits, NativeUnits


def deduce_native_units(read_unit: EOWUnits) -> NativeUnits:
    """Deduce native units based on oew units"""

    if read_unit in [
        EOWUnits.UNIT_CUBIC_METER,
        EOWUnits.UNIT_CM,
        EOWUnits.UNIT_LITER,
        EOWUnits.UNIT_LITERS,
        EOWUnits.UNIT_LITER_LC,
    ]:
        return NativeUnits.CM
    elif read_unit in [
        EOWUnits.UNIT_GAL,
        EOWUnits.UNIT_10_GAL,
        EOWUnits.UNIT_100_GAL,
        EOWUnits.UNIT_KGAL,
    ]:
        return NativeUnits.GAL
    elif read_unit in [
        EOWUnits.UNIT_CCF,
        EOWUnits.UNIT_10_CF,
        EOWUnits.UNIT_CF,
        EOWUnits.UNIT_CUBIC_FEET,
    ]:
        return NativeUnits.CF
    else:
        msg = f"Unsupported measurement unit: {read_unit}"
        raise EyeOnWaterUnitError(
            msg,
        )


def convert_to_native(  # noqa: C901
    native_unit: NativeUnits, read_unit: EOWUnits, value: float
) -> float:
    """Convert read units to native unit."""

    if native_unit == NativeUnits.CM:
        if read_unit in [EOWUnits.UNIT_CUBIC_METER, EOWUnits.UNIT_CM]:
            return value
        elif read_unit in [
            EOWUnits.UNIT_LITER,
            EOWUnits.UNIT_LITERS,
            EOWUnits.UNIT_LITER_LC,
        ]:
            return value / 1000.0
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    elif native_unit == NativeUnits.GAL:
        if read_unit == EOWUnits.UNIT_KGAL:
            return value * 1000
        elif read_unit == EOWUnits.UNIT_100_GAL:
            return value * 100
        elif read_unit == EOWUnits.UNIT_10_GAL:
            return value * 10
        elif read_unit == EOWUnits.UNIT_GAL:
            return value
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    elif native_unit == NativeUnits.CF:
        if read_unit in [EOWUnits.UNIT_CF, EOWUnits.UNIT_CUBIC_FEET]:
            return value
        elif read_unit == EOWUnits.UNIT_CCF:
            return value * 100
        elif read_unit == EOWUnits.UNIT_10_CF:
            return value * 10
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    else:
        msg = f"Unsupported native unit: {native_unit}"
        raise EyeOnWaterUnitError(
            msg,
        )
