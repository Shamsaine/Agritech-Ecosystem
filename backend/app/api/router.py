from fastapi import APIRouter

from app.api.routes.applications import router as applications_router
from app.api.routes.catalog import router as catalog_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(applications_router)
api_router.include_router(catalog_router)
