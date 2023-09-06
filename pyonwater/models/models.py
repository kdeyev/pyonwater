"""EOW Client data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class DataPoint:
    """One data point representation."""

    dt: datetime
    reading: float
    unit: str
