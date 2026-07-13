from datetime import datetime

from app.core.enums import RISK_STATUS_LABELS, STRUCTURE_TYPE_LABELS, RiskStatus, StructureType
from app.models import RiskAssessment, Structure


def compute_age_years(built_year: int | None) -> int | None:
    if built_year is None:
        return None
    return datetime.utcnow().year - built_year


def structure_to_list_item(structure: Structure) -> dict:
    return {
        "id": structure.id,
        "name": structure.name,
        "structure_type": structure.structure_type,
        "structure_type_label": STRUCTURE_TYPE_LABELS[structure.structure_type],
        "built_year": structure.built_year,
        "age_years": compute_age_years(structure.built_year),
        "current_risk_score": structure.current_risk_score,
        "current_status": structure.current_status,
        "current_status_label": RISK_STATUS_LABELS[structure.current_status],
        "location_description": structure.location_description,
        "last_assessed_at": structure.last_assessed_at,
        "location_lat": float(structure.location_lat) if structure.location_lat is not None else None,
        "location_lng": float(structure.location_lng) if structure.location_lng is not None else None,
        "metadata": structure.metadata_ or {},
    }


def structure_to_detail(structure: Structure, latest_assessment: RiskAssessment | None = None) -> dict:
    data = structure_to_list_item(structure)
    data.update(
        {
            "risk_factors": latest_assessment.factors if latest_assessment else {},
            "sensor_count": len(structure.sensors) if structure.sensors else 0,
        }
    )
    return data


def assessment_to_response(assessment: RiskAssessment) -> dict:
    return {
        "id": assessment.id,
        "structure_id": assessment.structure_id,
        "risk_score": assessment.risk_score,
        "status": assessment.status,
        "status_label": RISK_STATUS_LABELS[assessment.status],
        "confidence": float(assessment.confidence) if assessment.confidence is not None else None,
        "factors": assessment.factors or {},
        "model_version": assessment.model_version,
        "assessed_at": assessment.assessed_at,
    }
