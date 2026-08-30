from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interviews import router as interviews_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(applications_router)
api_v1_router.include_router(interviews_router)
api_v1_router.include_router(analytics_router)
