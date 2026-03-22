from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.envelope import success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def health_check() -> dict:
    settings = get_settings()
    return success_response(
        {
            "status": "OK",
            "service": settings.app_name,
            "environment": settings.environment,
            "timestamp": datetime.now(UTC).isoformat(),
            "ports": {
                "backend": settings.backend_port,
                "frontend": 5176,
            },
        }
    )


@router.get("/readiness", summary="Readiness check")
def readiness_check() -> dict:
    settings = get_settings()
    return success_response(
        {
            "status": "READY",
            "dependencies": {
                "database": {
                    "status": "CONFIGURED",
                    "url": settings.database_url_masked,
                },
                "redis": {
                    "status": "CONFIGURED",
                    "url": settings.redis_url,
                },
                "ollama": {
                    "status": "CONFIGURED",
                    "baseUrl": settings.ollama_base_url,
                    "model": settings.ollama_model,
                },
            },
        }
    )
