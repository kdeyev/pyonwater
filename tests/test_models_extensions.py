"""Tests for additional model fields."""

from typing import Any

from pyonwater.models import MeterInfo


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
