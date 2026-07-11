# Setup Guide

Instructions for running the InfraPredict AI backend locally on Windows, macOS, or Linux.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 15+ | Database |
| Docker Desktop | latest (optional) | Run PostgreSQL in a container |
| Git | latest | Version control |

## Option A: Docker Compose (Recommended)

The fastest way to get PostgreSQL and the API running together.

### 1. Clone and enter the backend directory

```bash
cd backend
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — at minimum set a strong `SECRET_KEY`:

```env
DATABASE_URL=postgresql+asyncpg://infrapredict:infrapredict@localhost:5432/infrapredict
SECRET_KEY=your-random-secret-at-least-32-chars
```

### 3. Start services

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port `5432`
- (Once implemented) API on port `8000`

### 4. Run migrations

```bash
docker compose exec api alembic upgrade head
```

Or, if running the API locally against Docker PostgreSQL:

```bash
alembic upgrade head
```

### 5. Seed development data (optional)

```bash
python scripts/seed_dev.py
```

---

## Option B: Manual Setup

### 1. Create a Python virtual environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database

Connect to PostgreSQL as a superuser:

```sql
CREATE USER infrapredict WITH PASSWORD 'infrapredict';
CREATE DATABASE infrapredict OWNER infrapredict;
GRANT ALL PRIVILEGES ON DATABASE infrapredict TO infrapredict;
```

### 4. Configure environment variables

Copy and edit the example file:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing secret (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Default: `7` |
| `CORS_ORIGINS` | No | Comma-separated frontend URLs |
| `ENVIRONMENT` | No | `development` or `production` |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING` |

### 5. Apply database migrations

```bash
alembic upgrade head
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
- Health check: http://localhost:8000/api/v1/health
- Swagger UI: http://localhost:8000/docs

---

## Connecting the Frontend

In the React project root, create or update `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Restart the Vite dev server after changing environment variables:

```bash
npm run dev
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Single test file
pytest tests/test_structures.py -v
```

Tests use a separate test database. Set in `.env`:

```env
TEST_DATABASE_URL=postgresql+asyncpg://infrapredict:infrapredict@localhost:5432/infrapredict_test
```

---

## Database Migrations

### Create a new migration after model changes

```bash
alembic revision --autogenerate -m "add sensor calibration table"
alembic upgrade head
```

### Roll back one migration

```bash
alembic downgrade -1
```

---

## Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Use a strong, unique `SECRET_KEY` (store in secrets manager)
- [ ] Use managed PostgreSQL (AWS RDS, Azure Database, etc.)
- [ ] Enable SSL on database connections (`?sslmode=require`)
- [ ] Restrict `CORS_ORIGINS` to your frontend domain
- [ ] Run behind a reverse proxy (nginx, Caddy) with TLS
- [ ] Use a process manager (systemd, gunicorn + uvicorn workers)
- [ ] Set up database backups and point-in-time recovery
- [ ] Configure log aggregation (CloudWatch, Datadog, etc.)
- [ ] Enable rate limiting and WAF at the edge
- [ ] Partition `sensor_readings` table by month

### Example production start command

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

---

## Troubleshooting

### Cannot connect to PostgreSQL

```
sqlalchemy.exc.OperationalError: connection refused
```

- Confirm PostgreSQL is running: `docker compose ps` or `pg_isready -h localhost -p 5432`
- Verify `DATABASE_URL` credentials match your setup
- On Windows, ensure Docker Desktop is running if using containers

### Migration conflicts

```bash
alembic heads          # Show current heads
alembic merge heads    # Merge divergent branches
alembic upgrade head
```

### CORS errors in browser

Add your frontend origin to `.env`:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Restart the API server after changing `.env`.

---

## Related Documents

- [Backend README](../README.md)
- [Architecture](./architecture.md)
- [API Reference](./api-reference.md)
- [Database Schema](./database-schema.md)
