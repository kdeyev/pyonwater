"""EyeOnWater API integration."""

from __future__ import annotations

from .account import Account
from .client import Client
from .exceptions import (
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterAuthExpired,
    EyeOnWaterException,
    EyeOnWaterRateLimitError,
    EyeOnWaterResponseIsEmpty,
    EyeOnWaterUnitError,
)
from .meter import Meter
from .meter_reader import MeterReader
from .models import DataPoint, EOWUnits, NativeUnits
from .units import convert_to_native, deduce_native_units

__all__ = [
    "Account",
    "Client",
    "DataPoint",
    "EOWUnits",
    "EyeOnWaterAPIError",
    "EyeOnWaterAuthError",
    "EyeOnWaterAuthExpired",
    "EyeOnWaterException",
    "EyeOnWaterRateLimitError",
    "EyeOnWaterResponseIsEmpty",
    "EyeOnWaterUnitError",
    "Meter",
    "MeterReader",
    "NativeUnits",
    "convert_to_native",
    "deduce_native_units",
]
