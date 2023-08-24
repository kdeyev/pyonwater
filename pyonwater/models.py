from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DataPoint(BaseModel):
    dt: datetime
    reading: float
