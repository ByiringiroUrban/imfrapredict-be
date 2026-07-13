from fastapi import APIRouter

from app.api.v1 import (
    dashboard, health, risk_assessments, structures, auth,
    users, inspections, maintenance, telemetry, admin, analytics
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(structures.router)
api_router.include_router(risk_assessments.router)
api_router.include_router(dashboard.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(inspections.router)
api_router.include_router(maintenance.router)
api_router.include_router(telemetry.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
