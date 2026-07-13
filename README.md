# InfraPredict AI — Backend

Python REST API backend for the InfraPredict AI platform. It ingests sensor and environmental data, runs risk assessments, and exposes infrastructure monitoring data to the frontend.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| API framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (Bearer tokens) |
| Task queue (optional) | Celery + Redis |

FastAPI is recommended for this project because it provides native async support, automatic OpenAPI documentation, and strong Pydantic integration — all well suited for high-volume sensor ingestion and REST APIs.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture](./docs/architecture.md) | System design, layers, and data flow |
| [Database Schema](./docs/database-schema.md) | PostgreSQL tables, relationships, and indexes |
| [API Reference](./docs/api-reference.md) | REST endpoints, request/response formats |
| [Setup Guide](./docs/setup-guide.md) | Local development and deployment |

## High-Level Capabilities

The backend supports the six core modules reflected in the frontend:

1. **Real-Time Sensor Integration** — ingest and query IoT readings (strain, vibration, temperature, displacement)
2. **ML-Powered Prediction** — trigger and retrieve model inference results
3. **Risk Scoring Engine** — compute and store dynamic risk scores per structure
4. **Trend Analysis** — time-series aggregation and deterioration forecasts
5. **Environmental Monitoring** — weather, seismic, traffic, and seasonal factor ingestion
6. **Maintenance Optimization** — prioritized maintenance recommendations

## Repository Layout (Planned)

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings and environment variables
│   ├── api/
│   │   ├── deps.py          # Shared dependencies (DB session, auth)
│   │   └── v1/
│   │       ├── router.py    # Versioned API router
│   │       ├── structures.py
│   │       ├── sensors.py
│   │       ├── readings.py
│   │       ├── risk_assessments.py
│   │       ├── maintenance.py
│   │       └── auth.py
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   ├── repositories/        # Database access layer
│   └── core/
│       ├── security.py      # JWT, password hashing
│       └── database.py      # Engine, session factory
├── alembic/                 # Database migrations
├── tests/
├── docs/                    # This documentation
├── requirements.txt
├── .env.example
└── docker-compose.yml       # PostgreSQL + API for local dev
```

## Quick Start

See the [Setup Guide](./docs/setup-guide.md) for full instructions. Minimal steps:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Edit DATABASE_URL and secrets
docker compose up -d postgres      # Start PostgreSQL
alembic upgrade head               # Apply migrations
uvicorn app.main:app --reload --port 8000
```

Interactive API docs will be available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Versioning

All endpoints are prefixed with `/api/v1/`. Breaking changes require a new version (`/api/v2/`).

## Frontend Integration

The React frontend (Vite, port 5173) communicates with this backend via REST. Configure the frontend environment variable:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Status

The backend is **implemented** with core endpoints, database migrations, and seed data.

**Implemented endpoints:**
- `GET /api/v1/health`
- `GET /api/v1/structures`
- `GET /api/v1/structures/{id}`
- `GET /api/v1/structures/{id}/risk-assessments`
- `GET /api/v1/structures/{id}/risk-assessments/latest`
- `GET /api/v1/dashboard/stats`

**Quick start after PostgreSQL is running:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt
copy .env.example .env
docker compose up -d postgres       # or use local PostgreSQL
alembic upgrade head
python scripts/seed_dev.py
uvicorn app.main:app --reload --port 8000
```
