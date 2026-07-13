# Database Schema

PostgreSQL 15+ schema for InfraPredict AI. All primary keys use UUID v4. Timestamps are stored as `TIMESTAMPTZ` (UTC).

## Entity Relationship Diagram

```
users ──────────────┐
                    │
organizations ──────┼── structures ──── sensors ──── sensor_readings
       │            │        │              │
       │            │        ├── risk_assessments
       │            │        ├── inspections
       │            │        └── maintenance_plans
       │            │
       └── org_members          environmental_readings
```

## Enums

```sql
CREATE TYPE structure_type AS ENUM (
  'steel_truss',
  'concrete_beam',
  'cable_stayed',
  'reinforced_concrete',
  'steel_composite',
  'other'
);

CREATE TYPE risk_status AS ENUM ('normal', 'warning', 'critical');

CREATE TYPE sensor_type AS ENUM (
  'strain',
  'vibration',
  'temperature',
  'displacement',
  'humidity',
  'pressure'
);

CREATE TYPE maintenance_priority AS ENUM ('low', 'medium', 'high', 'urgent');

CREATE TYPE maintenance_status AS ENUM (
  'planned',
  'scheduled',
  'in_progress',
  'completed',
  'cancelled'
);

CREATE TYPE user_role AS ENUM ('admin', 'operator', 'viewer');
```

## Core Tables

### organizations

Multi-tenant root entity. Each customer organization owns structures and users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Organization display name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-safe identifier |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(255) | | |
| role | user_role | NOT NULL, DEFAULT 'viewer' | Global default role |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

### org_members

Links users to organizations with per-org roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| organization_id | UUID | FK → organizations, NOT NULL | |
| user_id | UUID | FK → users, NOT NULL | |
| role | user_role | NOT NULL | Role within this org |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Unique:** `(organization_id, user_id)`

### structures

Infrastructure assets monitored by the platform. Maps directly to frontend dashboard rows.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| organization_id | UUID | FK → organizations, NOT NULL | |
| name | VARCHAR(255) | NOT NULL | e.g. "Harbor Bridge #42" |
| structure_type | structure_type | NOT NULL | |
| location_lat | DECIMAL(10,7) | | GPS latitude |
| location_lng | DECIMAL(10,7) | | GPS longitude |
| location_description | TEXT | | Human-readable location |
| built_year | SMALLINT | | Used to compute age |
| current_risk_score | SMALLINT | CHECK (0–100) | Latest score (denormalized) |
| current_status | risk_status | NOT NULL, DEFAULT 'normal' | |
| last_assessed_at | TIMESTAMPTZ | | When risk was last computed |
| metadata | JSONB | DEFAULT '{}' | Flexible extra fields |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `(organization_id, is_active)`
- `(current_status)` — filter critical structures quickly
- `(current_risk_score DESC)` — dashboard sorting

### sensors

IoT devices attached to structures.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| structure_id | UUID | FK → structures, NOT NULL | |
| name | VARCHAR(255) | NOT NULL | |
| sensor_type | sensor_type | NOT NULL | |
| unit | VARCHAR(20) | NOT NULL | e.g. "με", "mm/s", "°C" |
| api_key_hash | VARCHAR(255) | | Hashed key for device auth |
| calibration_offset | DECIMAL(12,6) | DEFAULT 0 | |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| installed_at | TIMESTAMPTZ | | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `(structure_id, sensor_type, is_active)`

### sensor_readings

Time-series data. High-volume table — plan for partitioning.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| sensor_id | UUID | FK → sensors, NOT NULL | |
| value | DECIMAL(14,6) | NOT NULL | Measured value |
| recorded_at | TIMESTAMPTZ | NOT NULL | Device timestamp |
| ingested_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Server receipt time |
| quality_flag | VARCHAR(20) | DEFAULT 'good' | good / suspect / bad |
| idempotency_key | VARCHAR(64) | UNIQUE | Prevent duplicate ingestion |

**Indexes:**
- `(sensor_id, recorded_at DESC)` — primary query pattern
- `(recorded_at)` — partition key

**Partitioning (production):**
```sql
CREATE TABLE sensor_readings (
  ...
) PARTITION BY RANGE (recorded_at);
```

### risk_assessments

Historical and current risk evaluation results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| structure_id | UUID | FK → structures, NOT NULL | |
| risk_score | SMALLINT | NOT NULL, CHECK (0–100) | |
| status | risk_status | NOT NULL | |
| confidence | DECIMAL(5,4) | | Model confidence 0.0–1.0 |
| factors | JSONB | NOT NULL, DEFAULT '{}' | Breakdown: structural, corrosion, load |
| model_version | VARCHAR(50) | | ML model identifier |
| assessed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Example `factors` JSON:**
```json
{
  "structural": { "score": 22, "status": "normal" },
  "corrosion": { "score": 48, "status": "warning" },
  "load": { "score": 15, "status": "normal" },
  "environmental": { "seismic_risk": 0.12, "weather_impact": 0.08 }
}
```

**Indexes:** `(structure_id, assessed_at DESC)`

### environmental_readings

External environmental data linked to structures or regions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| structure_id | UUID | FK → structures | Nullable for regional data |
| source | VARCHAR(100) | NOT NULL | e.g. "openweather", "usgs" |
| metric | VARCHAR(50) | NOT NULL | e.g. "temperature", "wind_speed" |
| value | DECIMAL(14,6) | NOT NULL | |
| unit | VARCHAR(20) | NOT NULL | |
| recorded_at | TIMESTAMPTZ | NOT NULL | |
| metadata | JSONB | DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `(structure_id, metric, recorded_at DESC)`

### inspections

Manual inspection reports.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| structure_id | UUID | FK → structures, NOT NULL | |
| inspector_name | VARCHAR(255) | | |
| inspection_date | DATE | NOT NULL | |
| findings | TEXT | | Free-text report |
| severity | maintenance_priority | | Overall finding severity |
| attachments | JSONB | DEFAULT '[]' | File URLs / metadata |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

### maintenance_plans

AI-generated or manually created maintenance recommendations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| structure_id | UUID | FK → structures, NOT NULL | |
| title | VARCHAR(255) | NOT NULL | |
| description | TEXT | | |
| priority | maintenance_priority | NOT NULL | |
| status | maintenance_status | NOT NULL, DEFAULT 'planned' | |
| estimated_cost | DECIMAL(12,2) | | |
| scheduled_date | DATE | | |
| completed_at | TIMESTAMPTZ | | |
| triggered_by_assessment_id | UUID | FK → risk_assessments | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:** `(structure_id, status, priority)`

### refresh_tokens

Stored refresh tokens for JWT auth rotation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| user_id | UUID | FK → users, NOT NULL | |
| token_hash | VARCHAR(255) | NOT NULL | |
| expires_at | TIMESTAMPTZ | NOT NULL | |
| revoked_at | TIMESTAMPTZ | | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

## Sample Queries

### Dashboard: structures with risk (matches frontend preview)

```sql
SELECT
  s.name,
  s.structure_type,
  EXTRACT(YEAR FROM AGE(CURRENT_DATE, MAKE_DATE(s.built_year, 1, 1))) AS age_years,
  s.current_risk_score,
  s.current_status
FROM structures s
WHERE s.organization_id = :org_id
  AND s.is_active = true
ORDER BY s.current_risk_score DESC;
```

### Latest readings for a structure (last 24 hours)

```sql
SELECT sr.sensor_id, sen.sensor_type, sr.value, sr.unit, sr.recorded_at
FROM sensor_readings sr
JOIN sensors sen ON sen.id = sr.sensor_id
WHERE sen.structure_id = :structure_id
  AND sr.recorded_at >= NOW() - INTERVAL '24 hours'
ORDER BY sr.recorded_at DESC;
```

### Risk trend (30-day)

```sql
SELECT assessed_at::date AS day, AVG(risk_score) AS avg_risk
FROM risk_assessments
WHERE structure_id = :structure_id
  AND assessed_at >= NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day;
```

## Migration Strategy

1. Use Alembic for all schema changes — never alter production manually
2. Seed data script for development (`scripts/seed_dev.py`) with the five sample structures from the frontend
3. Enable `pg_trgm` extension if full-text search on structure names is needed

## Related Documents

- [Architecture](./architecture.md)
- [API Reference](./api-reference.md)
