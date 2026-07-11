from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models import RiskAssessment, Sensor, SensorReading, Structure
from app.schemas.common import PaginatedResponse
from app.schemas.risk import RiskAssessmentResponse
from app.services.structure_service import assessment_to_response

router = APIRouter(tags=["risk-assessments"])


@router.get(
    "/structures/{structure_id}/risk-assessments",
    response_model=PaginatedResponse[RiskAssessmentResponse],
)
async def list_risk_assessments(
    structure_id: UUID,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[RiskAssessmentResponse]:
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")

    base_query = select(RiskAssessment).where(RiskAssessment.structure_id == structure_id)
    total = (await session.execute(select(func.count()).select_from(base_query.subquery()))).scalar_one()

    result = await session.execute(
        base_query.order_by(RiskAssessment.assessed_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    assessments = result.scalars().all()

    return PaginatedResponse(
        items=[RiskAssessmentResponse(**assessment_to_response(a)) for a in assessments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/structures/{structure_id}/risk-assessments/latest", response_model=RiskAssessmentResponse)
async def get_latest_risk_assessment(
    structure_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> RiskAssessmentResponse:
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")

    result = await session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.structure_id == structure_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .limit(1)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No risk assessment found")

    return RiskAssessmentResponse(**assessment_to_response(assessment))
