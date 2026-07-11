from datetime import datetime
from uuid import UUID

from app.core.enums import RiskStatus
from app.schemas.common import ORMModel


class RiskAssessmentResponse(ORMModel):
    id: UUID
    structure_id: UUID
    risk_score: int
    status: RiskStatus
    status_label: str
    confidence: float | None = None
    factors: dict
    model_version: str | None = None
    assessed_at: datetime
