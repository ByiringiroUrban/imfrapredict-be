# API Reference

Base URL: `http://localhost:8000/api/v1`

All request and response bodies are JSON. Datetimes use ISO 8601 UTC format (`2026-06-20T14:30:00Z`).

## Authentication

Protected endpoints require a Bearer token:

```
Authorization: Bearer <access_token>
```

Sensor ingestion endpoints accept an API key header:

```
X-API-Key: <sensor_api_key>
```

---

## Auth

### POST `/auth/register`

Create a new user account.

**Request:**
```json
{
  "email": "operator@example.com",
  "password": "SecurePass123!",
  "full_name": "Jane Operator"
}
```

**Response `201`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "operator@example.com",
  "full_name": "Jane Operator",
  "role": "viewer",
  "created_at": "2026-06-20T10:00:00Z"
}
```

### POST `/auth/login`

**Request:**
```json
{
  "email": "operator@example.com",
  "password": "SecurePass123!"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "dGhpcy...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST `/auth/refresh`

**Request:**
```json
{
  "refresh_token": "dGhpcy..."
}
```

**Response `200`:** Same shape as login.

### POST `/auth/logout`

Revoke the refresh token. Requires Bearer token.

**Response `204`:** No content.

---

## Organizations

### GET `/organizations`

List organizations the authenticated user belongs to.

**Response `200`:**
```json
{
  "items": [
    {
      "id": "org-uuid",
      "name": "City Infrastructure Dept",
      "slug": "city-infra",
      "role": "operator"
    }
  ],
  "total": 1
}
```

### GET `/organizations/{org_id}`

Get organization details.

---

## Structures

Infrastructure assets. Powers the frontend risk monitor dashboard.

### GET `/structures`

List structures for an organization.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `organization_id` | UUID | required | Filter by org |
| `status` | string | | `normal`, `warning`, `critical` |
| `structure_type` | string | | Filter by type |
| `sort` | string | `-risk_score` | Sort field (prefix `-` for desc) |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `search` | string | | Search by name |

**Response `200`:**
```json
{
  "items": [
    {
      "id": "struct-uuid",
      "name": "Harbor Bridge #42",
      "structure_type": "steel_truss",
      "built_year": 1979,
      "age_years": 47,
      "current_risk_score": 72,
      "current_status": "critical",
      "location_description": "Harbor District, Pier 7",
      "last_assessed_at": "2026-06-20T08:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

### GET `/structures/{structure_id}`

Get a single structure with latest risk factors.

**Response `200`:**
```json
{
  "id": "struct-uuid",
  "name": "Harbor Bridge #42",
  "structure_type": "steel_truss",
  "built_year": 1979,
  "age_years": 47,
  "current_risk_score": 72,
  "current_status": "critical",
  "location_lat": 40.7128,
  "location_lng": -74.0060,
  "location_description": "Harbor District, Pier 7",
  "last_assessed_at": "2026-06-20T08:00:00Z",
  "risk_factors": {
    "structural": { "score": 65, "status": "critical" },
    "corrosion": { "score": 78, "status": "critical" },
    "load": { "score": 42, "status": "warning" }
  },
  "sensor_count": 12,
  "metadata": {}
}
```

### POST `/structures`

Create a structure. Requires `admin` or `operator` role.

**Request:**
```json
{
  "organization_id": "org-uuid",
  "name": "Highway 1 Expansion Joint",
  "structure_type": "steel_composite",
  "built_year": 2021,
  "location_lat": 34.0522,
  "location_lng": -118.2437,
  "location_description": "Highway 1, Mile 42"
}
```

**Response `201`:** Structure object.

### PATCH `/structures/{structure_id}`

Partial update. Requires `admin` or `operator` role.

### DELETE `/structures/{structure_id}`

Soft-delete (sets `is_active = false`). Requires `admin` role.

**Response `204`:** No content.

---

## Sensors

### GET `/structures/{structure_id}/sensors`

List sensors attached to a structure.

**Response `200`:**
```json
{
  "items": [
    {
      "id": "sensor-uuid",
      "name": "Strain Gauge NE-01",
      "sensor_type": "strain",
      "unit": "με",
      "is_active": true,
      "installed_at": "2024-03-15T00:00:00Z"
    }
  ],
  "total": 12
}
```

### POST `/structures/{structure_id}/sensors`

Register a new sensor. Returns a one-time plaintext API key.

**Request:**
```json
{
  "name": "Vibration Sensor SW-02",
  "sensor_type": "vibration",
  "unit": "mm/s"
}
```

**Response `201`:**
```json
{
  "id": "sensor-uuid",
  "name": "Vibration Sensor SW-02",
  "sensor_type": "vibration",
  "unit": "mm/s",
  "api_key": "ip_sk_live_abc123...",
  "message": "Store this API key securely. It will not be shown again."
}
```

---

## Sensor Readings

### POST `/readings`

Ingest a single reading. Authenticated via `X-API-Key`.

**Request:**
```json
{
  "value": 142.5,
  "recorded_at": "2026-06-20T14:30:00Z",
  "quality_flag": "good",
  "idempotency_key": "device-001-20260620-143000"
}
```

**Response `201`:**
```json
{
  "id": "reading-uuid",
  "sensor_id": "sensor-uuid",
  "value": 142.5,
  "recorded_at": "2026-06-20T14:30:00Z",
  "ingested_at": "2026-06-20T14:30:01Z"
}
```

### POST `/readings/batch`

Ingest up to 1,000 readings in one request.

**Request:**
```json
{
  "readings": [
    {
      "value": 142.5,
      "recorded_at": "2026-06-20T14:30:00Z",
      "idempotency_key": "key-001"
    },
    {
      "value": 143.1,
      "recorded_at": "2026-06-20T14:31:00Z",
      "idempotency_key": "key-002"
    }
  ]
}
```

**Response `201`:**
```json
{
  "accepted": 2,
  "duplicates": 0,
  "errors": []
}
```

### GET `/structures/{structure_id}/readings`

Query readings for all sensors on a structure.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `sensor_type` | string | | Filter by sensor type |
| `from` | datetime | 24h ago | Start of range |
| `to` | datetime | now | End of range |
| `aggregation` | string | | `raw`, `hourly`, `daily` |
| `page_size` | int | 100 | Max 1000 |

**Response `200` (raw):**
```json
{
  "items": [
    {
      "sensor_id": "sensor-uuid",
      "sensor_type": "strain",
      "value": 142.5,
      "unit": "με",
      "recorded_at": "2026-06-20T14:30:00Z"
    }
  ],
  "total": 2880
}
```

---

## Risk Assessments

### GET `/structures/{structure_id}/risk-assessments`

Historical risk scores for trend charts.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `from` | datetime | 30 days ago | |
| `to` | datetime | now | |
| `page_size` | int | 50 | |

**Response `200`:**
```json
{
  "items": [
    {
      "id": "assessment-uuid",
      "risk_score": 72,
      "status": "critical",
      "confidence": 0.947,
      "factors": {
        "structural": { "score": 65, "status": "critical" },
        "corrosion": { "score": 78, "status": "critical" },
        "load": { "score": 42, "status": "warning" }
      },
      "model_version": "risk-v2.1.0",
      "assessed_at": "2026-06-20T08:00:00Z"
    }
  ],
  "total": 30
}
```

### GET `/structures/{structure_id}/risk-assessments/latest`

Most recent assessment. Powers the hero section risk gauge.

**Response `200`:** Single assessment object (same shape as items above).

### POST `/structures/{structure_id}/risk-assessments/trigger`

Manually trigger a risk recalculation. Requires `admin` or `operator` role.

**Response `202`:**
```json
{
  "job_id": "job-uuid",
  "status": "queued",
  "message": "Risk assessment queued for processing."
}
```

---

## Environmental Data

### GET `/structures/{structure_id}/environmental`

Recent environmental readings.

**Query parameters:** `from`, `to`, `metric`

**Response `200`:**
```json
{
  "items": [
    {
      "metric": "temperature",
      "value": 32.5,
      "unit": "°C",
      "source": "openweather",
      "recorded_at": "2026-06-20T12:00:00Z"
    },
    {
      "metric": "wind_speed",
      "value": 18.2,
      "unit": "km/h",
      "source": "openweather",
      "recorded_at": "2026-06-20T12:00:00Z"
    }
  ],
  "total": 2
}
```

### POST `/structures/{structure_id}/environmental`

Ingest environmental data (manual or webhook). Requires `operator` role.

---

## Inspections

### GET `/structures/{structure_id}/inspections`

List inspection reports.

### POST `/structures/{structure_id}/inspections`

Create an inspection report.

**Request:**
```json
{
  "inspector_name": "John Smith, PE",
  "inspection_date": "2026-06-15",
  "findings": "Moderate corrosion observed on north truss connection.",
  "severity": "medium"
}
```

**Response `201`:** Inspection object.

---

## Maintenance Plans

### GET `/maintenance`

List maintenance plans across an organization.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `organization_id` | UUID | Required |
| `status` | string | Filter by status |
| `priority` | string | Filter by priority |
| `sort` | string | Default: `-priority,scheduled_date` |

**Response `200`:**
```json
{
  "items": [
    {
      "id": "plan-uuid",
      "structure_id": "struct-uuid",
      "structure_name": "Harbor Bridge #42",
      "title": "Replace corroded truss connection bolts",
      "description": "Priority repair based on risk score 72 and corrosion factor.",
      "priority": "urgent",
      "status": "planned",
      "estimated_cost": 45000.00,
      "scheduled_date": "2026-07-15"
    }
  ],
  "total": 3
}
```

### POST `/structures/{structure_id}/maintenance`

Create a maintenance plan.

### PATCH `/maintenance/{plan_id}`

Update status, schedule, or details.

**Request:**
```json
{
  "status": "scheduled",
  "scheduled_date": "2026-07-10"
}
```

---

## Dashboard / Stats

Aggregated metrics for the frontend stats section.

### GET `/dashboard/stats`

**Query parameters:** `organization_id` (required)

**Response `200`:**
```json
{
  "structures_monitored": 12400,
  "sensor_readings_today": 2300000,
  "prediction_accuracy": 0.947,
  "critical_count": 12,
  "warning_count": 48,
  "normal_count": 11940
}
```

> Note: Production values are computed from live data. Development seed data returns smaller counts.

---

## Health

### GET `/health`

No authentication required.

**Response `200`:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## Pagination

List endpoints return a consistent pagination envelope:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

Link headers (optional):
```
Link: </api/v1/structures?page=2>; rel="next"
```

## Rate Limits

| Endpoint group | Limit |
|----------------|-------|
| Auth | 10 req/min per IP |
| Readings ingestion | 1,000 req/min per API key |
| General API | 100 req/min per user |

Exceeded limits return `429` with `Retry-After` header.

## OpenAPI

FastAPI auto-generates an OpenAPI 3.1 spec at `/openapi.json` once the application is implemented. Use this as the source of truth for client code generation.

## Related Documents

- [Architecture](./architecture.md)
- [Database Schema](./database-schema.md)
- [Setup Guide](./setup-guide.md)
