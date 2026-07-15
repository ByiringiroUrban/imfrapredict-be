from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional

from app.core.enums import SensorType

class SensorReadingResponse(BaseModel):
    id: UUID
    sensor_id: UUID
    value: float
    recorded_at: datetime
    quality_flag: str

    class Config:
        from_attributes = True

class SensorResponse(BaseModel):
    id: UUID
    structure_id: UUID
    name: str
    sensor_type: SensorType
    unit: str
    is_active: bool
    structure_name: Optional[str] = None
    latest_reading: Optional[float] = None
    latest_reading_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TelemetryHistoryResponse(BaseModel):
    timestamp: datetime
    value: float
