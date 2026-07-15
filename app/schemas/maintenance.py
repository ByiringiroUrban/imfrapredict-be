from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.enums import MaintenancePriority, MaintenanceStatus

class MaintenanceBase(BaseModel):
    structure_id: UUID
    title: str
    description: Optional[str] = None
    priority: MaintenancePriority
    status: MaintenanceStatus = MaintenanceStatus.PLANNED
    estimated_cost: Optional[float] = None
    scheduled_date: Optional[date] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceResponse(MaintenanceBase):
    id: UUID
    completed_at: Optional[datetime] = None
    triggered_by_assessment_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    structure_name: Optional[str] = None

    class Config:
        from_attributes = True
