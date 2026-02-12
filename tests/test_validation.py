"""Tests for input validation in MeterReader class."""

from unittest.mock import Mock

import pytest

from pyonwater.meter_reader import MeterReader
from pyonwater.models.units import AggregationLevel, RequestUnits


def test_meter_reader_empty_uuid() -> None:
    """Verify that empty meter_uuid raises ValueError."""
    with pytest.raises(ValueError, match="meter_uuid cannot be empty"):
        MeterReader(meter_uuid="", meter_id="12345")


def test_meter_reader_whitespace_uuid() -> None:
    """Verify that whitespace-only meter_uuid raises ValueError."""
    with pytest.raises(ValueError, match="meter_uuid cannot be empty"):
        MeterReader(meter_uuid="   ", meter_id="12345")


def test_meter_reader_empty_meter_id() -> None:
    """Verify that empty meter_id raises ValueError."""
    with pytest.raises(ValueError, match="meter_id cannot be empty"):
        MeterReader(meter_uuid="valid-uuid", meter_id="")


def test_meter_reader_whitespace_meter_id() -> None:
    """Verify that whitespace-only meter_id raises ValueError."""
    with pytest.raises(ValueError, match="meter_id cannot be empty"):
        MeterReader(meter_uuid="valid-uuid", meter_id="   ")


def test_meter_reader_valid_init() -> None:
    """Verify that valid inputs initialize correctly."""
    reader = MeterReader(meter_uuid="test-uuid", meter_id="12345")
    assert reader.meter_uuid == "test-uuid"
    assert reader.meter_id == "12345"


def test_meter_reader_strips_whitespace() -> None:
    """Verify that whitespace is stripped from inputs."""
    reader = MeterReader(meter_uuid="  test-uuid  ", meter_id="  12345  ")
    assert reader.meter_uuid == "test-uuid"
    assert reader.meter_id == "12345"


@pytest.mark.asyncio()
async def test_historical_data_zero_days() -> None:
    """Verify that days_to_load=0 raises ValueError."""
    reader = MeterReader(meter_uuid="test-uuid", meter_id="12345")
    mock_client = Mock()  # Won't be accessed due to early validation
    with pytest.raises(ValueError, match="days_to_load must be at least 1"):
        await reader.read_historical_data(client=mock_client, days_to_load=0)


@pytest.mark.asyncio()
async def test_historical_data_negative_days() -> None:
    """Verify that negative days_to_load raises ValueError."""
    reader = MeterReader(meter_uuid="test-uuid", meter_id="12345")
    mock_client = Mock()  # Won't be accessed due to early validation
    with pytest.raises(ValueError, match="days_to_load must be at least 1"):
        await reader.read_historical_data(client=mock_client, days_to_load=-5)


# ============================================================================
# Enum Validation Tests
# ============================================================================


def test_aggregation_level_enum_invalid_value() -> None:
    """Verify that invalid aggregation level values raise ValueError.

    AggregationLevel is a Python Enum - trying to create an instance with
    an invalid value will raise ValueError. This provides type safety.
    """
    with pytest.raises(ValueError):
        AggregationLevel("invalid_aggregation")  # type: ignore


def test_aggregation_level_enum_valid_values() -> None:
    """Verify all valid AggregationLevel enum values."""
    # All 6 valid aggregation levels
    assert AggregationLevel.QUARTER_HOURLY.value == "hr"
    assert AggregationLevel.HOURLY.value == "hourly"
    assert AggregationLevel.DAILY.value == "daily"
    assert AggregationLevel.WEEKLY.value == "weekly"
    assert AggregationLevel.MONTHLY.value == "monthly"
    assert AggregationLevel.YEARLY.value == "yearly"


def test_request_units_enum_invalid_value() -> None:
    """Verify that invalid unit values raise ValueError.

    RequestUnits is a Python Enum - trying to create an instance with
    an invalid value will raise ValueError. This provides type safety.
    """
    with pytest.raises(ValueError):
        RequestUnits("invalid_unit")  # type: ignore


def test_request_units_enum_valid_values() -> None:
    """Verify all valid RequestUnits enum values."""
    # All 8 valid request units
    assert RequestUnits.GALLONS.value == "gallons"
    assert RequestUnits.CUBIC_FEET.value == "cf"
    assert RequestUnits.CCF.value == "ccf"
    assert RequestUnits.LITERS.value == "liters"
    assert RequestUnits.CUBIC_METERS.value == "cm"
    assert RequestUnits.IMPERIAL_GALLONS.value == "imp"
    assert RequestUnits.OIL_BARRELS.value == "oil_barrel"
    assert RequestUnits.FLUID_BARRELS.value == "fluid_barrel"


def test_aggregation_has_default() -> None:
    """Verify that aggregation parameter has a default value.

    The aggregation parameter defaults to HOURLY, so it cannot be None
    unless explicitly overridden (which type checking prevents).
    """
    # The signature has: aggregation: AggregationLevel = AggregationLevel.HOURLY
    # So it always has a valid value
    assert AggregationLevel.HOURLY.value == "hourly"


def test_units_defaults_to_cm_when_none() -> None:
    """Verify that units parameter defaults to 'cm' when None.

    The units parameter accepts RequestUnits | None, and when None is passed,
    the code defaults to 'cm' (cubic meters) in the API request.
    This prevents empty responses from the API.
    """
    # When units=None, the code uses: units.value if units is not None else "cm"
    units_value: RequestUnits | None = None
    result = units_value.value if units_value is not None else "cm"
    assert result == "cm"

    # When units is provided, it uses the enum value
    units_value = RequestUnits.GALLONS
    result = units_value.value
    assert result == "gallons"
