"""Tests for pyonwater meter reader"""


import pytest

from pyonwater import EyeOnWaterAPIError, MeterReader


def test_conversion_us():
    """Test units conversion for US units"""
    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=True,
    )

    assert meter_reader.convert("CUBIC_METER", 1.0) == 1.0
    assert meter_reader.convert("CM", 1.0) == 1.0
    with pytest.raises(EyeOnWaterAPIError):
        assert meter_reader.convert("GAL", 1.0)


def test_conversion_metric():
    """Test units conversion for metric units"""
    meter_reader = MeterReader(
        meter_uuid="meter_uuid",
        meter_id="meter_id",
        metric_measurement_system=False,
    )

    assert meter_reader.convert("GAL", 1.0) == 1.0
    assert meter_reader.convert("KGAL", 1.0) == 1000.0
    assert meter_reader.convert("100 GAL", 1.0) == 100.0
    assert meter_reader.convert("10 GAL", 1.0) == 10.0
    assert meter_reader.convert("CF", 1.0) == 7.48052
    assert meter_reader.convert("CUBIC_FEET", 1.0) == 7.48052
    assert meter_reader.convert("CCF", 1.0) == 748.052
    with pytest.raises(EyeOnWaterAPIError):
        assert meter_reader.convert("CM", 1.0)
