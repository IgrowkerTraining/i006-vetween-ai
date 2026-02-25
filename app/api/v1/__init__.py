"""API v1 endpoints."""

from fastapi import APIRouter
from app.api.v1 import health, informes

api_router = APIRouter(prefix="/api/v1")

# Include all v1 routers
api_router.include_router(informes.router)
api_router.include_router(health.router)
