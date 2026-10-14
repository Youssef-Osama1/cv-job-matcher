from fastapi import APIRouter

from app.api.endpoints import health_endpoints, match_endpoints

api_router = APIRouter()
api_router.include_router(health_endpoints.router, tags=["health"])
api_router.include_router(match_endpoints.router, prefix="/match", tags=["match"])
