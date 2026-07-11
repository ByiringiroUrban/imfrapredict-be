from datetime import datetime
from app.core.enums import MaintenancePriority, RiskStatus, risk_status_from_score
from app.models import Structure

def predict_infrastructure_risk(
    built_year: int | None,
    traffic_load: int | None,
    slope_percent: float | None,
    annual_rainfall_mm: float | None,
    landslide_history: bool | None,
    inspection_severity: MaintenancePriority | None,
    cnn_defects: list[dict] | None = None
) -> tuple[int, float, dict]:
    """
    Simulates a Random Forest Classifier evaluating structural, environmental,
    geotechnical, and visual defect parameters to estimate infrastructure failure risk.
    
    Returns:
        tuple[risk_score, confidence, factors]
    """
    current_year = datetime.utcnow().year
    age = current_year - built_year if built_year else 0
    
    # 1. Structural Age Factor (Max 25 pts)
    # 1.2 pts per year of age
    age_score = min(age * 1.2, 25.0)
    
    # 2. Traffic Load Factor (Max 20 pts)
    # Heavy traffic accelerates fatigue
    traffic_val = traffic_load or 0
    traffic_score = min((traffic_val / 10000.0) * 5.0, 20.0)
    
    # 3. Geotechnical Slope & Landslide Factor (Max 20 pts)
    slope_val = slope_percent or 0.0
    slope_score = min(slope_val * 1.2, 12.0)
    if landslide_history:
        slope_score += 8.0
        
    # 4. Environmental Precipitation Factor (Max 15 pts)
    # High rainfall leads to erosion, flooding, and water logging
    rain_val = annual_rainfall_mm or 1000.0
    rain_score = min(max(rain_val - 1000.0, 0.0) * 0.03, 15.0)
    
    # 5. Visual Defects & Field Inspections Factor (Max 40 pts)
    inspection_score = 0.0
    if inspection_severity == MaintenancePriority.LOW:
        inspection_score = 8.0
    elif inspection_severity == MaintenancePriority.MEDIUM:
        inspection_score = 18.0
    elif inspection_severity == MaintenancePriority.HIGH:
        inspection_score = 30.0
    elif inspection_severity == MaintenancePriority.URGENT:
        inspection_score = 40.0
        
    # 6. CNN Image Analysis Defect Modifiers
    # If the user ran a CNN visual analysis, add weights for detected defects
    cnn_score = 0.0
    if cnn_defects:
        for defect in cnn_defects:
            confidence = defect.get("confidence", 0.0)
            defect_type = defect.get("type", "")
            if confidence >= 0.5:
                if defect_type == "crack":
                    cnn_score += 8.0 * confidence
                elif defect_type == "pothole":
                    cnn_score += 6.0 * confidence
                elif defect_type == "spalling":
                    cnn_score += 10.0 * confidence
                elif defect_type == "erosion":
                    cnn_score += 12.0 * confidence
    
    inspection_and_cnn_score = min(inspection_score + cnn_score, 45.0)
    
    # Total failure risk score calculation
    total_score_raw = age_score + traffic_score + slope_score + rain_score + inspection_and_cnn_score
    risk_score = int(min(max(total_score_raw, 0), 100))
    
    # Calculate confidence based on available variables
    available_inputs = 0
    total_inputs = 6
    if built_year is not None: available_inputs += 1
    if traffic_load is not None: available_inputs += 1
    if slope_percent is not None: available_inputs += 1
    if annual_rainfall_mm is not None: available_inputs += 1
    if landslide_history is not None: available_inputs += 1
    if inspection_severity is not None or cnn_defects is not None: available_inputs += 1
    
    confidence = round(0.70 + (available_inputs / total_inputs) * 0.28, 3)
    
    # Breakdown of contributors for explainable AI metrics
    factors = {
        "structural": {
            "score": round(age_score, 1),
            "status": "normal" if age_score < 10 else ("warning" if age_score < 18 else "critical")
        },
        "load": {
            "score": round(traffic_score, 1),
            "status": "normal" if traffic_score < 8 else ("warning" if traffic_score < 15 else "critical")
        },
        "environmental": {
            "score": round(slope_score + rain_score, 1),
            "status": "normal" if (slope_score + rain_score) < 12 else ("warning" if (slope_score + rain_score) < 22 else "critical")
        },
        "inspection": {
            "score": round(inspection_and_cnn_score, 1),
            "status": "normal" if inspection_and_cnn_score < 12 else ("warning" if inspection_and_cnn_score < 25 else "critical")
        }
    }
    
    return risk_score, confidence, factors
