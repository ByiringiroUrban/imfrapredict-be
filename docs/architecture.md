# Architecture

## Overview

InfraPredict AI backend follows a layered architecture: HTTP handlers delegate to services, services orchestrate business logic, and repositories handle PostgreSQL persistence. ML inference and batch jobs run as separate processes that write results back to the database.

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│                   (Vite — port 5173)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / REST (JSON)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Auth    │  │Structures│  │ Sensors  │  │ Risk / Maint │   │
│  │  Router  │  │  Router  │  │  Router  │  │   Routers    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       └─────────────┴─────────────┴───────────────┘           │
│                             │                                   │
│                    Service Layer                                │
│         (validation, risk scoring, aggregation)                 │
│                             │                                   │
│                   Repository Layer                              │
│              (SQLAlchemy queries, transactions)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │  ML Worker   │  │  Redis (opt.)   │
│   (primary DB)  │  │  (Celery)    │  │  cache / queue  │
└─────────────────┘  └──────────────┘  └─────────────────┘
         ▲
         │ IoT / external feeds
┌────────┴────────┐
│  Sensor Gateway │
│  Weather API    │
│  Inspection CSV │
└─────────────────┘
```

## Data Flow

### 1. Sensor Ingestion

```
IoT Device → POST /api/v1/readings/batch → validate → bulk insert → PostgreSQL
                                                      ↓
                                            trigger risk recalculation (async)
```

Readings are stored as time-series rows keyed by `sensor_id` and `recorded_at`. High-volume ingestion uses batch endpoints with idempotency keys to prevent duplicates.

### 2. Risk Assessment Pipeline

```
Scheduled job / event trigger
    → aggregate recent readings + environmental data + inspection history
    → ML model inference (or rule-based fallback)
    → write risk_assessments row
    → update structures.current_risk_score and structures.status
    → emit alert if status crosses threshold
```

Risk scores map to status levels (aligned with the frontend dashboard):

| Score Range | Status   | Frontend Color |
|-------------|----------|----------------|
| 0 – 29      | Normal   | Green          |
| 30 – 59     | Warning  | Amber          |
| 60 – 100    | Critical | Red            |

### 3. Dashboard Queries

The frontend risk monitor table maps to:

```
GET /api/v1/structures?include=risk&sort=-risk_score
```

Returns structure name, type, age, risk score, and status — matching the preview data in `RiskPreviewSection.tsx`.

## Layer Responsibilities

### API Layer (`app/api/`)

- Parse and validate HTTP requests (Pydantic schemas)
- Enforce authentication and authorization
- Map HTTP status codes to domain errors
- No direct database queries in route handlers

### Service Layer (`app/services/`)

- Business rules (e.g., risk threshold logic, maintenance prioritization)
- Coordinate multiple repositories in a single transaction
- Call external services (ML inference, weather APIs)

### Repository Layer (`app/repositories/`)

- CRUD operations and complex SQL queries
- Pagination, filtering, sorting
- No HTTP or business-rule knowledge

### Models (`app/models/`)

- SQLAlchemy declarative models
- Table definitions, relationships, constraints

## Authentication & Authorization

| Role | Permissions |
|------|-------------|
| `admin` | Full CRUD on all resources, user management |
| `operator` | Read all, write readings, trigger assessments |
| `viewer` | Read-only access to structures, risk, maintenance |

Authentication uses JWT access tokens (short-lived) and refresh tokens (long-lived, stored hashed in DB). Sensor ingestion endpoints accept API keys scoped to specific structures.

## Error Handling

All errors return a consistent JSON envelope:

```json
{
  "error": {
    "code": "STRUCTURE_NOT_FOUND",
    "message": "Structure with id 'abc-123' does not exist.",
    "details": {}
  }
}
```

| HTTP Status | Usage |
|-------------|-------|
| 400 | Validation failure, malformed request |
| 401 | Missing or invalid token |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate, stale state) |
| 422 | Unprocessable entity (Pydantic validation) |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |

## Scalability Considerations

- **Readings table** — partition by month on `recorded_at`; index `(sensor_id, recorded_at DESC)`
- **Risk assessments** — retain latest per structure in `structures` table; archive historical rows
- **Connection pooling** — SQLAlchemy pool size tuned per deployment (default: 10)
- **Async endpoints** — use async SQLAlchemy for I/O-bound read endpoints under load

## Security

- All secrets via environment variables (never committed)
- Parameterized queries only (SQLAlchemy ORM)
- Rate limiting on ingestion endpoints
- CORS restricted to frontend origin in production
- TLS termination at reverse proxy (nginx / cloud load balancer)

## Related Documents

- [Database Schema](./database-schema.md)
- [API Reference](./api-reference.md)
- [Setup Guide](./setup-guide.md)
