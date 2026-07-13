import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import (
    MaintenancePriority,
    MaintenanceStatus,
    RiskStatus,
    SensorType,
    StructureType,
    UserRole,
)


def sqla_enum(enum_class, name: str):
    return Enum(enum_class, name=name, values_callable=lambda x: [e.value for e in x])


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    structures: Mapped[list["Structure"]] = relationship(back_populates="organization")
    members: Mapped[list["OrgMember"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(sqla_enum(UserRole, "user_role"), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships: Mapped[list["OrgMember"]] = relationship(back_populates="user")


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(sqla_enum(UserRole, "user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Structure(Base, TimestampMixin):
    __tablename__ = "structures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    structure_type: Mapped[StructureType] = mapped_column(sqla_enum(StructureType, "structure_type"), nullable=False)
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    location_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    location_description: Mapped[str | None] = mapped_column(Text)
    built_year: Mapped[int | None] = mapped_column(SmallInteger)
    current_risk_score: Mapped[int | None] = mapped_column(SmallInteger)
    current_status: Mapped[RiskStatus] = mapped_column(sqla_enum(RiskStatus, "risk_status"), default=RiskStatus.NORMAL, nullable=False, index=True)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="structures")
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="structure")
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="structure")
    maintenance_plans: Mapped[list["MaintenancePlan"]] = relationship(back_populates="structure")


class Sensor(Base, TimestampMixin):
    __tablename__ = "sensors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("structures.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sensor_type: Mapped[SensorType] = mapped_column(sqla_enum(SensorType, "sensor_type"), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(255))
    calibration_offset: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    structure: Mapped["Structure"] = relationship(back_populates="sensors")
    readings: Mapped[list["SensorReading"]] = relationship(back_populates="sensor")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sensors.id"), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(20), default="good")
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)

    sensor: Mapped["Sensor"] = relationship(back_populates="readings")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("structures.id"), nullable=False, index=True)
    risk_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[RiskStatus] = mapped_column(sqla_enum(RiskStatus, "risk_status"), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    factors: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    model_version: Mapped[str | None] = mapped_column(String(50))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    structure: Mapped["Structure"] = relationship(back_populates="risk_assessments")


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("structures.id"), index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Inspection(Base, TimestampMixin):
    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("structures.id"), nullable=False)
    inspector_name: Mapped[str | None] = mapped_column(String(255))
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    findings: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[MaintenancePriority | None] = mapped_column(sqla_enum(MaintenancePriority, "maintenance_priority"))
    attachments: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")


class MaintenancePlan(Base, TimestampMixin):
    __tablename__ = "maintenance_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("structures.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[MaintenancePriority] = mapped_column(sqla_enum(MaintenancePriority, "maintenance_priority"), nullable=False)
    status: Mapped[MaintenanceStatus] = mapped_column(sqla_enum(MaintenanceStatus, "maintenance_status"), default=MaintenanceStatus.PLANNED, nullable=False)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_by_assessment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("risk_assessments.id"))

    structure: Mapped["Structure"] = relationship(back_populates="maintenance_plans")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
