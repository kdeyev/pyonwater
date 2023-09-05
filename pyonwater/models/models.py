"""EOW Client data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .units import EOWUnits

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class DataPoint:
    """One data point representation."""

    dt: datetime
    reading: float
    unit: EOWUnits
