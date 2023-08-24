"""EOW Client data models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class DataPoint(BaseModel):
    """One data point representation."""

    dt: datetime = Field(..., description="datetime with timezone")
    reading: float = Field(..., description="reading in m^2 or gallons")
