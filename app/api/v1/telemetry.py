from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from uuid import UUID

from app.api.deps import get_session
from app.models import Sensor, SensorReading, Structure
from app.schemas.telemetry import SensorResponse, TelemetryHistoryResponse

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.get("/sensors", response_model=List[SensorResponse])
async def list_sensors(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Sensor).where(Sensor.is_active.is_(True)))
    sensors = result.scalars().all()
    
    # Fetch structure names
    structure_ids = {s.structure_id for s in sensors}
    structures = await session.execute(select(Structure).where(Structure.id.in_(structure_ids)))
    structure_map = {st.id: st.name for st in structures.scalars().all()}
    
    # Fetch latest reading for each sensor
    # A simple approach for a small dataset, but for large datasets a lateral join or window function is better.
    # We will do individual queries here for simplicity given the prototype nature, or one query grouped.
    
    response = []
    for s in sensors:
        resp = SensorResponse.model_validate(s)
        resp.structure_name = structure_map.get(s.structure_id, "Unknown Structure")
        
        reading_res = await session.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == s.id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        latest_reading = reading_res.scalars().first()
        if latest_reading:
            resp.latest_reading = float(latest_reading.value)
            resp.latest_reading_at = latest_reading.recorded_at
            
        response.append(resp)
        
    return response

@router.get("/sensors/{sensor_id}/history", response_model=List[TelemetryHistoryResponse])
async def get_sensor_history(sensor_id: UUID, limit: int = 50, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(limit)
    )
    readings = result.scalars().all()
    
    response = [
        TelemetryHistoryResponse(timestamp=r.recorded_at, value=float(r.value))
        for r in reversed(readings) # Return ascending order for charts
    ]
    return response
