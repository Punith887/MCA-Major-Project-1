from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, dashboard, deployments, health, incidents, monitoring
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=(
        "Phase 1 foundation for the Intelligent AIOps Framework. "
        "Monitoring, ML, RAG, and operations integrations are not connected yet."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(monitoring.router)
api_router.include_router(incidents.router)
api_router.include_router(deployments.router)
api_router.include_router(admin.router)
app.include_router(api_router)
