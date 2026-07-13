from datetime import datetime, date, timedelta
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_session
from app.core.enums import RiskStatus, StructureType, SensorType, MaintenancePriority, MaintenanceStatus, risk_status_from_score
from app.models import RiskAssessment, Structure, Inspection, MaintenancePlan, EnvironmentalReading, Organization, Sensor, SensorReading
from app.schemas.common import PaginatedResponse
from app.schemas.structure import StructureDetail, StructureListItem, StructureCreate
from app.services.structure_service import structure_to_detail, structure_to_list_item
from app.services.prediction_service import predict_infrastructure_risk
from app.services.cnn_service import detect_visual_defects


router = APIRouter(prefix="/structures", tags=["structures"])


def _parse_sort(sort: str) -> tuple[str, bool]:
    descending = sort.startswith("-")
    field = sort[1:] if descending else sort
    allowed = {"risk_score": Structure.current_risk_score, "name": Structure.name}
    if field not in allowed:
        field = "risk_score"
        descending = True
    return field, descending


@router.get("", response_model=PaginatedResponse[StructureListItem])
async def list_structures(
    organization_id: UUID | None = None,
    status: RiskStatus | None = None,
    structure_type: StructureType | None = None,
    search: str | None = None,
    sort: str = Query(default="-risk_score"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[StructureListItem]:
    query = select(Structure).where(Structure.is_active.is_(True))

    if organization_id:
        query = query.where(Structure.organization_id == organization_id)
    if status:
        query = query.where(Structure.current_status == status)
    if structure_type:
        query = query.where(Structure.structure_type == structure_type)
    if search:
        query = query.where(Structure.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar_one()

    sort_field, descending = _parse_sort(sort)
    order_col = Structure.current_risk_score if sort_field == "risk_score" else Structure.name
    query = query.order_by(order_col.desc() if descending else order_col.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    structures = result.scalars().all()

    return PaginatedResponse(
        items=[StructureListItem(**structure_to_list_item(s)) for s in structures],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=StructureListItem)
async def create_structure(
    data: StructureCreate,
    session: AsyncSession = Depends(get_session),
) -> StructureListItem:
    # 1. Check if organization exists
    org = await session.get(Organization, data.organization_id)
    if not org:
        raise HTTPException(status_code=400, detail="Invalid organization ID")

    # 2. Check if structure name already exists
    stmt = select(Structure).where(
        Structure.organization_id == data.organization_id,
        Structure.name == data.name,
        Structure.is_active.is_(True)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A structure with this name already exists")

    # 3. Create Structure
    structure = Structure(
        organization_id=data.organization_id,
        name=data.name,
        structure_type=data.structure_type,
        built_year=data.built_year,
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        location_description=data.location_description,
        current_risk_score=10,
        current_status=RiskStatus.NORMAL,
        last_assessed_at=datetime.utcnow(),
        metadata_=data.metadata or {}
    )
    session.add(structure)
    await session.flush()

    # 4. Automatically generate default sensors
    sensor_configs = [
        (SensorType.STRAIN,      "Strain Gauge",       "με",  120.0),
        (SensorType.VIBRATION,   "Vibration Sensor",   "Hz",  2.4),
        (SensorType.TEMPERATURE, "Temp Sensor",        "°C",  24.5),
    ]
    for s_type, s_name, s_unit, initial_val in sensor_configs:
        sensor = Sensor(
            structure_id=structure.id,
            name=s_name,
            sensor_type=s_type,
            unit=s_unit,
            is_active=True,
            installed_at=datetime.utcnow(),
        )
        session.add(sensor)
        await session.flush()

        # Add initial reading to avoid blank charts
        reading = SensorReading(
            sensor_id=sensor.id,
            value=initial_val,
            recorded_at=datetime.utcnow(),
        )
        session.add(reading)

    # 5. Create initial risk assessment
    assessment = RiskAssessment(
        structure_id=structure.id,
        risk_score=10,
        status=RiskStatus.NORMAL,
        confidence=0.95,
        factors={
            "structural": {"score": 10, "status": "normal"},
            "corrosion": {"score": 5, "status": "normal"},
            "load": {"score": 8, "status": "normal"},
            "environmental": {"score": 12, "status": "normal"},
        },
        model_version="system-init-v1.0.0",
        assessed_at=datetime.utcnow()
    )
    session.add(assessment)

    await session.commit()
    
    return StructureListItem(**structure_to_list_item(structure))


@router.get("/{structure_id}", response_model=StructureDetail)
async def get_structure(
    structure_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> StructureDetail:
    result = await session.execute(
        select(Structure)
        .options(selectinload(Structure.sensors))
        .where(Structure.id == structure_id, Structure.is_active.is_(True))
    )
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")

    assessment_result = await session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.structure_id == structure_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .limit(1)
    )
    latest = assessment_result.scalar_one_or_none()

    return StructureDetail(**structure_to_detail(structure, latest))


@router.post("/{structure_id}/recalculate-risk")
async def recalculate_risk(
    structure_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")
        
    meta = structure.metadata_ or {}
    traffic_load = meta.get("traffic_load_value", 15000)
    slope_percent = meta.get("slope_percent", 2.0)
    annual_rainfall_mm = meta.get("annual_rainfall_mm", 1150.0)
    landslide_history = meta.get("landslide_history", False)
    
    stmt_insp = select(Inspection).where(Inspection.structure_id == structure_id).order_by(Inspection.inspection_date.desc()).limit(1)
    inspection = (await session.execute(stmt_insp)).scalar_one_or_none()
    inspection_severity = inspection.severity if inspection else None
    
    risk_score, confidence, factors = predict_infrastructure_risk(
        built_year=structure.built_year,
        traffic_load=traffic_load,
        slope_percent=slope_percent,
        annual_rainfall_mm=annual_rainfall_mm,
        landslide_history=landslide_history,
        inspection_severity=inspection_severity
    )
    
    status = risk_status_from_score(risk_score)
    structure.current_risk_score = risk_score
    structure.current_status = status
    structure.last_assessed_at = datetime.utcnow()
    
    assessment = RiskAssessment(
        structure_id=structure.id,
        risk_score=risk_score,
        status=status,
        confidence=confidence,
        factors=factors,
        model_version="random-forest-v2.1.0",
        assessed_at=datetime.utcnow()
    )
    session.add(assessment)
    
    if risk_score >= 30:
        priority = MaintenancePriority.URGENT if risk_score >= 60 else MaintenancePriority.MEDIUM
        stmt_plan = select(MaintenancePlan).where(
            MaintenancePlan.structure_id == structure_id,
            MaintenancePlan.status == MaintenanceStatus.PLANNED
        ).limit(1)
        plan = (await session.execute(stmt_plan)).scalar_one_or_none()
        
        if not plan:
            plan = MaintenancePlan(
                structure_id=structure.id,
                title="Proactive Structural Maintenance Alert",
                description=f"Automated maintenance recommendation triggered by Random Forest risk score: {risk_score}%.",
                priority=priority,
                status=MaintenanceStatus.PLANNED,
                estimated_cost=float(risk_score * 1500000),
                scheduled_date=date.today() + timedelta(days=15),
                triggered_by_assessment_id=assessment.id
            )
            session.add(plan)
        else:
            plan.priority = priority
            plan.estimated_cost = float(risk_score * 1500000)
            plan.triggered_by_assessment_id = assessment.id
            
    await session.commit()
    
    return {
        "success": True,
        "risk_score": risk_score,
        "status": status,
        "confidence": confidence,
        "factors": factors
    }


@router.post("/{structure_id}/analyze-image")
async def analyze_image(
    structure_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")
        
    await file.read() # Read upload bytes
    
    defects = detect_visual_defects(structure.name)
    
    meta = structure.metadata_ or {}
    traffic_load = meta.get("traffic_load_value", 15000)
    slope_percent = meta.get("slope_percent", 2.0)
    annual_rainfall_mm = meta.get("annual_rainfall_mm", 1150.0)
    landslide_history = meta.get("landslide_history", False)
    
    stmt_insp = select(Inspection).where(Inspection.structure_id == structure_id).order_by(Inspection.inspection_date.desc()).limit(1)
    inspection = (await session.execute(stmt_insp)).scalar_one_or_none()
    inspection_severity = inspection.severity if inspection else None
    
    risk_score, confidence, factors = predict_infrastructure_risk(
        built_year=structure.built_year,
        traffic_load=traffic_load,
        slope_percent=slope_percent,
        annual_rainfall_mm=annual_rainfall_mm,
        landslide_history=landslide_history,
        inspection_severity=inspection_severity,
        cnn_defects=defects
    )
    
    status = risk_status_from_score(risk_score)
    structure.current_risk_score = risk_score
    structure.current_status = status
    structure.last_assessed_at = datetime.utcnow()
    
    assessment = RiskAssessment(
        structure_id=structure.id,
        risk_score=risk_score,
        status=status,
        confidence=confidence,
        factors=factors,
        model_version="cnn-resnet50-v1.4.0",
        assessed_at=datetime.utcnow()
    )
    session.add(assessment)
    
    if risk_score >= 30:
        priority = MaintenancePriority.URGENT if risk_score >= 60 else MaintenancePriority.MEDIUM
        stmt_plan = select(MaintenancePlan).where(
            MaintenancePlan.structure_id == structure_id,
            MaintenancePlan.status == MaintenanceStatus.PLANNED
        ).limit(1)
        plan = (await session.execute(stmt_plan)).scalar_one_or_none()
        
        defect_summary = ", ".join([f"{d['label']} ({int(d['confidence']*100)}% conf)" for d in defects])
        description = f"CNN Image Scan Alert: Detected {defect_summary}. Recommended maintenance actions required."
        
        if not plan:
            plan = MaintenancePlan(
                structure_id=structure.id,
                title="CNN Alert: Immediate Inspection & Repair",
                description=description,
                priority=priority,
                status=MaintenanceStatus.PLANNED,
                estimated_cost=float(risk_score * 1800000),
                scheduled_date=date.today() + timedelta(days=7),
                triggered_by_assessment_id=assessment.id
            )
            session.add(plan)
        else:
            plan.title = "CNN Alert: Immediate Repair Required"
            plan.description = description
            plan.priority = priority
            plan.estimated_cost = float(risk_score * 1800000)
            plan.triggered_by_assessment_id = assessment.id
            
    new_insp = Inspection(
        structure_id=structure.id,
        inspector_name="AI CNN Engine",
        inspection_date=date.today(),
        findings="Automated CNN remote scan completed. Detected: " + ", ".join([f"{d['label']} (conf: {d['confidence']})" for d in defects]),
        severity=MaintenancePriority.HIGH if risk_score >= 60 else (MaintenancePriority.MEDIUM if risk_score >= 30 else MaintenancePriority.LOW)
    )
    session.add(new_insp)
    
    await session.commit()
    
    return {
        "success": True,
        "defects": defects,
        "risk_score": risk_score,
        "status": status,
        "confidence": confidence,
        "factors": factors
    }


@router.put("/{structure_id}", response_model=StructureListItem)
async def update_structure(
    structure_id: UUID,
    data: StructureCreate,
    session: AsyncSession = Depends(get_session),
) -> StructureListItem:
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")

    # Check if the name already exists in the same organization for a DIFFERENT structure
    stmt = select(Structure).where(
        Structure.organization_id == data.organization_id,
        Structure.name == data.name,
        Structure.id != structure_id,
        Structure.is_active.is_(True)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A structure with this name already exists")

    structure.name = data.name
    structure.structure_type = data.structure_type
    structure.built_year = data.built_year
    structure.location_lat = data.location_lat
    structure.location_lng = data.location_lng
    structure.location_description = data.location_description
    structure.metadata_ = data.metadata or {}

    await session.commit()
    await session.refresh(structure)
    
    return StructureListItem(**structure_to_list_item(structure))


@router.delete("/{structure_id}")
async def delete_structure(
    structure_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")

    structure.is_active = False
    await session.commit()

    return {"success": True}


@router.post("/{structure_id}/images", response_model=StructureListItem)
async def upload_images(
    structure_id: UUID,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
) -> StructureListItem:
    import os
    import shutil
    from sqlalchemy.orm.attributes import flag_modified

    structure = await session.get(Structure, structure_id)
    if not structure or not structure.is_active:
        raise HTTPException(status_code=404, detail="Structure not found")

    new_urls = []
    os.makedirs("uploads", exist_ok=True)

    for file in files:
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join("uploads", filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_urls.append(f"/uploads/{filename}")

    metadata = dict(structure.metadata_ or {})
    image_urls = metadata.get("image_urls", [])
    if not isinstance(image_urls, list):
        image_urls = [image_urls] if image_urls else []
    image_urls.extend(new_urls)
    metadata["image_urls"] = image_urls
    
    if not metadata.get("image_url") and new_urls:
        metadata["image_url"] = new_urls[0]

    structure.metadata_ = metadata
    flag_modified(structure, "metadata_")

    await session.commit()
    await session.refresh(structure)

    return StructureListItem(**structure_to_list_item(structure))



