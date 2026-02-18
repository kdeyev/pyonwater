"""Units related tools."""

from .exceptions import EyeOnWaterUnitError
from .models import EOWUnits, NativeUnits

# Conversion matrix: (NativeUnits, EOWUnits) -> conversion_factor
# Maps from (target_native_unit, source_eow_unit) to the conversion multiplier
CONVERSION_MATRIX: dict[tuple[NativeUnits, EOWUnits], float] = {
    # Convert TO Cubic Meters (CM)
    (NativeUnits.CM, EOWUnits.UNIT_CUBIC_METER): 1.0,
    (NativeUnits.CM, EOWUnits.UNIT_CM): 1.0,
    (NativeUnits.CM, EOWUnits.UNIT_LITER): 1.0 / 1000.0,
    (NativeUnits.CM, EOWUnits.UNIT_LITERS): 1.0 / 1000.0,
    (NativeUnits.CM, EOWUnits.UNIT_LITER_LC): 1.0 / 1000.0,
    # Convert TO Gallons (GAL)
    (NativeUnits.GAL, EOWUnits.UNIT_KGAL): 1000.0,
    (NativeUnits.GAL, EOWUnits.UNIT_100_GAL): 100.0,
    (NativeUnits.GAL, EOWUnits.UNIT_10_GAL): 10.0,
    (NativeUnits.GAL, EOWUnits.UNIT_GAL): 1.0,
    # Convert TO Cubic Feet (CF)
    (NativeUnits.CF, EOWUnits.UNIT_CF): 1.0,
    (NativeUnits.CF, EOWUnits.UNIT_CUBIC_FEET): 1.0,
    (NativeUnits.CF, EOWUnits.UNIT_CCF): 100.0,
    (NativeUnits.CF, EOWUnits.UNIT_10_CF): 10.0,
}


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


def convert_to_native(
    native_unit: NativeUnits, read_unit: EOWUnits, value: float
) -> float:
    """Convert read units to native unit.

    Args:
        native_unit: The target native unit for conversion.
        read_unit: The source EOW unit to convert from.
        value: The numeric value to convert.

    Returns:
        The converted value in native units.

    Raises:
        EyeOnWaterUnitError: If the unit combination is not supported.
    """
    conversion_key = (native_unit, read_unit)

    if conversion_key in CONVERSION_MATRIX:
        return value * CONVERSION_MATRIX[conversion_key]

    msg = f"Unsupported unit conversion: {read_unit} to {native_unit}"
    raise EyeOnWaterUnitError(msg)
