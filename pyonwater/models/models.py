"""EOW Client data models"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DataPoint(BaseModel):
    """One data point representation"""

    dt: datetime = Field(..., description="datetime with timezone")
    reading: float = Field(..., description="reading in m^2 or gallons")
