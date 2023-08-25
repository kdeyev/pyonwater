"""EOW Client data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DataPoint:
    """One data point representation."""

    dt: datetime
    reading: float
