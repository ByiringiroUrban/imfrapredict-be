from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.enums import MaintenancePriority

class InspectionBase(BaseModel):
    structure_id: UUID
    inspector_name: Optional[str] = None
    inspection_date: date
    findings: Optional[str] = None
    severity: Optional[MaintenancePriority] = None
    attachments: List[dict] = Field(default_factory=list)

class InspectionCreate(InspectionBase):
    pass

class InspectionResponse(InspectionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    structure_name: Optional[str] = None

    class Config:
        from_attributes = True
