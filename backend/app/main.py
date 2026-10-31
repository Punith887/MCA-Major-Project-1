from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import (
    admin,
    anomalies,
    auth,
    dashboard,
    deployments,
    health,
    incidents,
    monitoring,
    projects,
)
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=(
        "Local AIOps platform. Prometheus application metrics can be analyzed with "
        "Isolation Forest to persist anomalies and linked incidents. RAG, GenAI, "
        "predictive analytics, and recovery operations are not yet connected."
    ),
    version="0.3.0",
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
api_router.include_router(projects.router)
api_router.include_router(anomalies.router)
api_router.include_router(incidents.router)
api_router.include_router(deployments.router)
api_router.include_router(admin.router)
app.include_router(api_router)

Instrumentator(
    excluded_handlers=["/metrics"],
    should_group_status_codes=False,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
