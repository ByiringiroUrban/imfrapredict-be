from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import RiskStatus, StructureType
from app.schemas.common import ORMModel


class StructureListItem(ORMModel):
    id: UUID
    name: str
    structure_type: StructureType
    structure_type_label: str
    built_year: int | None
    age_years: int | None
    current_risk_score: int | None
    current_status: RiskStatus
    current_status_label: str
    location_description: str | None = None
    last_assessed_at: datetime | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    created_by: UUID | None = None
    metadata: dict = Field(default_factory=dict)

class StructureDetail(StructureListItem):
    risk_factors: dict = Field(default_factory=dict)
    sensor_count: int = 0
    metadata: dict = Field(default_factory=dict)


class StructureCreate(BaseModel):
    organization_id: UUID
    name: str
    structure_type: StructureType
    built_year: int | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_description: str | None = None
    created_by: UUID | None = None
    metadata: dict = Field(default_factory=dict)

class StructureUpdate(BaseModel):
    name: str | None = None
    structure_type: StructureType | None = None
    built_year: int | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_description: str | None = None
    metadata: dict | None = None
