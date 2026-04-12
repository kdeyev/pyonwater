"""Tests for additional model fields."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import pytest

from pyonwater.models import MeterInfo
from pyonwater.models.eow_historical_models import (
    HistoricalData,
    Hit,
    Params,
    TimeSerie,
)
from pyonwater.models.eow_models import Battery, Flags, LatestRead, Pwr
from pyonwater.models.units import EOWUnits

# ---------------------------------------------------------------------------
# Module-level constants shared across Phase 6 tests
# ---------------------------------------------------------------------------
_MINIMAL_FLAGS: dict[str, bool] = {
    "EmptyPipe": False,
    "Leak": False,
    "CoverRemoved": False,
    "Tamper": False,
    "ReverseFlow": False,
    "LowBattery": False,
    "BatteryCharging": False,
}
_MINIMAL_LATEST_READ: dict[str, object] = {
    "full_read": 0.0,
    "units": "GAL",
    "read_time": "2026-01-01T00:00:00Z",
}
_MINIMAL_REGISTER_0: dict[str, object] = {
    "flags": _MINIMAL_FLAGS,
    "latest_read": _MINIMAL_LATEST_READ,
}
_MINIMAL_HIT: dict[str, object] = {"meter.timezone": ["America/New_York"]}
_MINIMAL_TIMESERIES: dict[str, object] = {
    "grp1": {"series": [{"date": "2026-01-01", "value": 5.0}]}
}


def test_meter_info_parses_leak_fields() -> None:
    """Test leak fields parse for top-level, meter, and reading payloads."""
    payload: dict[str, Any] = {
        "register_0": {
            "flags": {
                "EmptyPipe": False,
                "Leak": False,
                "CoverRemoved": False,
                "Tamper": False,
                "ReverseFlow": False,
                "LowBattery": False,
                "BatteryCharging": False,
            },
            "latest_read": {
                "full_read": 1.0,
                "units": "GAL",
                "read_time": "2026-02-01T00:00:00Z",
            },
            "leak": {
                "rate": 1.2,
                "max_flow_rate": 3.4,
                "total_leak_24hrs": 5.6,
                "time": "2026-02-01T01:00:00Z",
                "received_time": "2026-02-01T01:01:00Z",
            },
        },
        "meter": {"leak": {"rate": 0.7, "max_flow_rate": 0.9}},
        "leak": {"rate": 2.2, "total_leak_24hrs": 9.9},
    }

    model = MeterInfo.model_validate(payload)

    assert model.leak is not None
    assert model.leak.rate == 2.2
    assert model.meter is not None
    assert model.meter.leak is not None
    assert model.meter.leak.max_flow_rate == 0.9
    assert model.reading.leak is not None
    assert model.reading.leak.total_leak_24hrs == 5.6


# ---------------------------------------------------------------------------
# Group A — ValidationError paths
# ---------------------------------------------------------------------------


def test_flags_missing_mandatory_field_raises() -> None:
    """Flags without EmptyPipe (mandatory aliased field) raises ValidationError."""
    with pytest.raises(ValidationError):
        Flags.model_validate(
            {
                # EmptyPipe intentionally omitted
                "Leak": False,
                "CoverRemoved": False,
                "Tamper": False,
                "ReverseFlow": False,
                "LowBattery": False,
                "BatteryCharging": False,
            }
        )


def test_latest_read_invalid_units_raises() -> None:
    """LatestRead with unrecognized units string raises ValidationError."""
    with pytest.raises(ValidationError):
        LatestRead.model_validate(
            {
                "full_read": 1.0,
                "units": "MEGAGALLON",
                "read_time": "2026-01-01T00:00:00Z",
            }
        )


def test_meter_info_missing_register_0_raises() -> None:
    """MeterInfo without required register_0 raises ValidationError."""
    with pytest.raises(ValidationError):
        MeterInfo.model_validate({})


def test_hit_missing_timezone_raises() -> None:
    """Hit without mandatory meter.timezone field raises ValidationError."""
    with pytest.raises(ValidationError):
        Hit.model_validate({})


# ---------------------------------------------------------------------------
# Group B — Valid minimal construction with aliased fields
# ---------------------------------------------------------------------------


def test_battery_register_alias_maps_to_attribute() -> None:
    """Battery 'register' JSON key maps to register_ Python attribute."""
    b = Battery.model_validate({"register": 5, "level": 80})
    assert b.register_ == 5
    assert b.level == 80


def test_pwr_register_alias_maps_to_attribute() -> None:
    """Pwr 'register' JSON key maps to register_ Python attribute."""
    p = Pwr.model_validate({"register": 3, "signal_strength": 90})
    assert p.register_ == 3


def test_timeserie_empty_series_is_valid() -> None:
    """TimeSerie with an empty series list is a valid API response."""
    ts = TimeSerie.model_validate({"series": []})
    assert ts.series == []


# ---------------------------------------------------------------------------
# Group C — MeterInfo structure
# ---------------------------------------------------------------------------


def test_meter_info_minimal_payload_parses() -> None:
    """MeterInfo with only register_0 parses cleanly; optional fields default to None."""
    model = MeterInfo.model_validate({"register_0": _MINIMAL_REGISTER_0})
    assert model.reading.latest_read.full_read == 0.0
    assert model.leak is None


# ---------------------------------------------------------------------------
# Group D — HistoricalData structure
# ---------------------------------------------------------------------------


def test_historical_data_full_parse() -> None:
    """HistoricalData parses the anonymized fixture without errors."""
    raw = Path("tests/mock_data/historical_data_mock_anonymized.json").read_text(
        encoding="utf-8"
    )
    data = HistoricalData.model_validate(json.loads(raw))
    assert len(data.timeseries) > 0
    assert data.hit.meter_timezone


def test_historical_data_missing_hit_raises() -> None:
    """HistoricalData without required 'hit' field raises ValidationError."""
    with pytest.raises(ValidationError):
        HistoricalData.model_validate({"timeseries": _MINIMAL_TIMESERIES})


def test_historical_data_missing_timeseries_raises() -> None:
    """HistoricalData without required 'timeseries' field raises ValidationError."""
    with pytest.raises(ValidationError):
        HistoricalData.model_validate({"hit": _MINIMAL_HIT})


# ---------------------------------------------------------------------------
# Group E — Params model
# ---------------------------------------------------------------------------


def test_params_units_enum() -> None:
    """Params with a valid units enum value round-trips to the correct EOWUnits member."""
    p = Params.model_validate({"units": "GAL"})
    assert p.units == EOWUnits.UNIT_GAL
