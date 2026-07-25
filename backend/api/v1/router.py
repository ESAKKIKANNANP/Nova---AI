# =============================================================================
# backend/api/v1/router.py
#
# Main API router combining all v1 endpoints.
# =============================================================================

from fastapi import APIRouter
from api.v1.endpoints.datasets import router as datasets_router
from api.v1.endpoints.analysis import router as analysis_router
from api.v1.endpoints.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(datasets_router)
api_router.include_router(analysis_router)

