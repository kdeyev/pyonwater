"""Tests for input validation in MeterReader class."""

from unittest.mock import Mock

import pytest

from pyonwater.meter_reader import MeterReader


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
