"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Manually create the enum types in the database
    op.execute("CREATE TYPE structure_type AS ENUM ('steel_truss', 'concrete_beam', 'cable_stayed', 'reinforced_concrete', 'steel_composite', 'other')")
    op.execute("CREATE TYPE risk_status AS ENUM ('normal', 'warning', 'critical')")
    op.execute("CREATE TYPE sensor_type AS ENUM ('strain', 'vibration', 'temperature', 'displacement', 'humidity', 'pressure')")
    op.execute("CREATE TYPE maintenance_priority AS ENUM ('low', 'medium', 'high', 'urgent')")
    op.execute("CREATE TYPE maintenance_status AS ENUM ('planned', 'scheduled', 'in_progress', 'completed', 'cancelled')")
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'operator', 'viewer')")

    structure_type = postgresql.ENUM(
        "steel_truss",
        "concrete_beam",
        "cable_stayed",
        "reinforced_concrete",
        "steel_composite",
        "other",
        name="structure_type",
        create_type=False,
    )
    risk_status = postgresql.ENUM("normal", "warning", "critical", name="risk_status", create_type=False)
    sensor_type = postgresql.ENUM(
        "strain",
        "vibration",
        "temperature",
        "displacement",
        "humidity",
        "pressure",
        name="sensor_type",
        create_type=False,
    )
    maintenance_priority = postgresql.ENUM("low", "medium", "high", "urgent", name="maintenance_priority", create_type=False)
    maintenance_status = postgresql.ENUM(
        "planned",
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
        name="maintenance_status",
        create_type=False,
    )
    user_role = postgresql.ENUM("admin", "operator", "viewer", name="user_role", create_type=False)


    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "org_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    op.create_table(
        "structures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("structure_type", structure_type, nullable=False),
        sa.Column("location_lat", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("location_lng", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("location_description", sa.Text(), nullable=True),
        sa.Column("built_year", sa.SmallInteger(), nullable=True),
        sa.Column("current_risk_score", sa.SmallInteger(), nullable=True),
        sa.Column("current_status", risk_status, nullable=False, server_default="normal"),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_structures_organization_id", "structures", ["organization_id"])
    op.create_index("ix_structures_current_status", "structures", ["current_status"])

    op.create_table(
        "sensors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("structure_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sensor_type", sensor_type, nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("api_key_hash", sa.String(length=255), nullable=True),
        sa.Column("calibration_offset", sa.Numeric(precision=12, scale=6), server_default="0", nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensors_structure_id", "sensors", ["structure_id"])

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sensor_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("quality_flag", sa.String(length=20), server_default="good", nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_sensor_readings_sensor_id", "sensor_readings", ["sensor_id"])
    op.create_index("ix_sensor_readings_recorded_at", "sensor_readings", ["recorded_at"])

    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("structure_id", sa.UUID(), nullable=False),
        sa.Column("risk_score", sa.SmallInteger(), nullable=False),
        sa.Column("status", risk_status, nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("factors", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_assessments_structure_id", "risk_assessments", ["structure_id"])

    op.create_table(
        "environmental_readings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("structure_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("metric", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_environmental_readings_structure_id", "environmental_readings", ["structure_id"])

    op.create_table(
        "inspections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("structure_id", sa.UUID(), nullable=False),
        sa.Column("inspector_name", sa.String(length=255), nullable=True),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("severity", maintenance_priority, nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "maintenance_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("structure_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", maintenance_priority, nullable=False),
        sa.Column("status", maintenance_status, nullable=False, server_default="planned"),
        sa.Column("estimated_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by_assessment_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["triggered_by_assessment_id"], ["risk_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_plans_structure_id", "maintenance_plans", ["structure_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("maintenance_plans")
    op.drop_table("inspections")
    op.drop_table("environmental_readings")
    op.drop_table("risk_assessments")
    op.drop_table("sensor_readings")
    op.drop_table("sensors")
    op.drop_table("structures")
    op.drop_table("org_members")
    op.drop_table("users")
    op.drop_table("organizations")

    for enum_name in (
        "user_role",
        "maintenance_status",
        "maintenance_priority",
        "sensor_type",
        "risk_status",
        "structure_type",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
