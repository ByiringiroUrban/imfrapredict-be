from fastapi import APIRouter

from app.api.v1 import dashboard, health, risk_assessments, structures, auth

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(structures.router)
api_router.include_router(risk_assessments.router)
api_router.include_router(dashboard.router)
api_router.include_router(auth.router)
