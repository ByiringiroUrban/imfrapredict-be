from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_session
from app.models import MaintenancePlan, Structure
from app.schemas.maintenance import MaintenanceResponse

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

@router.get("", response_model=List[MaintenanceResponse])
async def list_maintenance(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MaintenancePlan).order_by(MaintenancePlan.scheduled_date.asc())
    )
    plans = result.scalars().all()
    
    # Fetch structure names
    structure_ids = {p.structure_id for p in plans}
    structures = await session.execute(select(Structure).where(Structure.id.in_(structure_ids)))
    structure_map = {s.id: s.name for s in structures.scalars().all()}
    
    response = []
    for p in plans:
        resp = MaintenanceResponse.model_validate(p)
        resp.structure_name = structure_map.get(p.structure_id, "Unknown Structure")
        response.append(resp)
        
    return response
