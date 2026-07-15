from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_session
from app.models import Inspection, Structure
from app.schemas.inspection import InspectionCreate, InspectionResponse

router = APIRouter(prefix="/inspections", tags=["inspections"])

@router.get("", response_model=List[InspectionResponse])
async def list_inspections(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Inspection).order_by(Inspection.inspection_date.desc())
    )
    inspections = result.scalars().all()
    
    # Fetch structure names
    structure_ids = {i.structure_id for i in inspections}
    structures = await session.execute(select(Structure).where(Structure.id.in_(structure_ids)))
    structure_map = {s.id: s.name for s in structures.scalars().all()}
    
    response = []
    for i in inspections:
        resp = InspectionResponse.model_validate(i)
        resp.structure_name = structure_map.get(i.structure_id, "Unknown Structure")
        response.append(resp)
        
    return response

@router.post("", response_model=InspectionResponse)
async def create_inspection(
    data: InspectionCreate,
    session: AsyncSession = Depends(get_session)
):
    structure = await session.get(Structure, data.structure_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")

    inspection = Inspection(
        structure_id=data.structure_id,
        inspector_name=data.inspector_name,
        inspection_date=data.inspection_date,
        findings=data.findings,
        severity=data.severity,
        attachments=data.attachments
    )
    session.add(inspection)
    await session.commit()
    await session.refresh(inspection)
    
    resp = InspectionResponse.model_validate(inspection)
    resp.structure_name = structure.name
    return resp
