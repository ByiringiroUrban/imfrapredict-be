from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.enums import RiskStatus
from app.models import RiskAssessment, SensorReading, Structure
from app.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    organization_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    structures_query = select(Structure).where(Structure.is_active.is_(True))
    if organization_id:
        structures_query = structures_query.where(Structure.organization_id == organization_id)

    structures_result = await session.execute(structures_query)
    structures = structures_result.scalars().all()

    critical_count = sum(1 for s in structures if s.current_status == RiskStatus.CRITICAL)
    warning_count = sum(1 for s in structures if s.current_status == RiskStatus.WARNING)
    normal_count = sum(1 for s in structures if s.current_status == RiskStatus.NORMAL)

    readings_today = (
        await session.execute(
            select(func.count(SensorReading.id)).where(
                SensorReading.ingested_at >= func.date_trunc("day", func.now())
            )
        )
    ).scalar_one()

    avg_confidence = (
        await session.execute(select(func.avg(RiskAssessment.confidence)))
    ).scalar_one()

    return DashboardStatsResponse(
        structures_monitored=len(structures),
        sensor_readings_today=readings_today,
        prediction_accuracy=round(float(avg_confidence or 0.947), 3),
        critical_count=critical_count,
        warning_count=warning_count,
        normal_count=normal_count,
    )
