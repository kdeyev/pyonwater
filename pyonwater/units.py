"""Units related tools."""
from .exceptions import EyeOnWaterUnitError
from .models import EOWUnits, NativeUnits


def deduce_native_units(read_unit: EOWUnits) -> NativeUnits:
    """Deduce native units based on oew units"""

    if read_unit in [EOWUnits.MEASUREMENT_CUBICMETERS, EOWUnits.MEASUREMENT_CM]:
        return NativeUnits.CM
    elif read_unit in [
        EOWUnits.MEASUREMENT_GALLONS,
        EOWUnits.MEASUREMENT_10_GALLONS,
        EOWUnits.MEASUREMENT_100_GALLONS,
        EOWUnits.MEASUREMENT_KILOGALLONS,
    ]:
        return NativeUnits.GAL
    elif read_unit in [
        EOWUnits.MEASUREMENT_CCF,
        EOWUnits.MEASUREMENT_CF,
        EOWUnits.MEASUREMENT_CUBIC_FEET,
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
        if read_unit in [EOWUnits.MEASUREMENT_CUBICMETERS, EOWUnits.MEASUREMENT_CM]:
            return value
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    elif native_unit == NativeUnits.GAL:
        if read_unit == EOWUnits.MEASUREMENT_KILOGALLONS:
            return value * 1000
        elif read_unit == EOWUnits.MEASUREMENT_100_GALLONS:
            return value * 100
        elif read_unit == EOWUnits.MEASUREMENT_10_GALLONS:
            return value * 10
        elif read_unit == EOWUnits.MEASUREMENT_GALLONS:
            return value
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    elif native_unit == NativeUnits.CF:
        if read_unit == EOWUnits.MEASUREMENT_CCF:
            return value * 100
        elif read_unit in [EOWUnits.MEASUREMENT_CF, EOWUnits.MEASUREMENT_CUBIC_FEET]:
            return value
        else:
            msg = f"Unsupported measurement unit: {read_unit} for native unit: {native_unit}"
            raise EyeOnWaterUnitError(msg)
    else:
        msg = f"Unsupported native unit: {native_unit}"
        raise EyeOnWaterUnitError(
            msg,
        )
