import enum


class StructureType(str, enum.Enum):
    STEEL_TRUSS = "steel_truss"
    CONCRETE_BEAM = "concrete_beam"
    CABLE_STAYED = "cable_stayed"
    REINFORCED_CONCRETE = "reinforced_concrete"
    STEEL_COMPOSITE = "steel_composite"
    OTHER = "other"


class RiskStatus(str, enum.Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class SensorType(str, enum.Enum):
    STRAIN = "strain"
    VIBRATION = "vibration"
    TEMPERATURE = "temperature"
    DISPLACEMENT = "displacement"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"


class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceStatus(str, enum.Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


STRUCTURE_TYPE_LABELS: dict[StructureType, str] = {
    StructureType.STEEL_TRUSS: "Steel Truss",
    StructureType.CONCRETE_BEAM: "Concrete Beam",
    StructureType.CABLE_STAYED: "Cable-Stayed",
    StructureType.REINFORCED_CONCRETE: "Reinforced Concrete",
    StructureType.STEEL_COMPOSITE: "Steel Composite",
    StructureType.OTHER: "Other",
}


RISK_STATUS_LABELS: dict[RiskStatus, str] = {
    RiskStatus.NORMAL: "Normal",
    RiskStatus.WARNING: "Warning",
    RiskStatus.CRITICAL: "Critical",
}


def risk_status_from_score(score: int) -> RiskStatus:
    if score >= 60:
        return RiskStatus.CRITICAL
    if score >= 30:
        return RiskStatus.WARNING
    return RiskStatus.NORMAL
