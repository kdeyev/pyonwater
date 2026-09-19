"""EOW Client data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class DataPoint:
    """One reading or historical interval.

    For interval data, ``dt`` is the inclusive bucket start and, when present,
    ``end_dt`` is the exclusive bucket end. ``reading`` is the cumulative
    register value at the end of the interval, while ``flow_value`` is the
    usage during ``[dt, end_dt)``. Interval-only fields are unset when the API
    does not provide enough information to populate them safely.
    """

    dt: datetime
    reading: float
    unit: str
    flow_value: float | None = None
    end_dt: datetime | None = None
