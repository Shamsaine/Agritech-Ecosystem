from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers


app = FastAPI(
    title=settings.app_name,
    description="Backend API for the Agritech Ecosystem Intelligence Platform.",
    debug=settings.debug,
    version="0.1.0",
)

register_error_handlers(app)
app.include_router(api_router)
app.include_router(health_router)

__all__ = ["app"]
