from __future__ import annotations

from typing import Literal

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import ping_database
from app.schemas.health import HealthData, HealthDependency


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_liveness(self, request_id: str | None = None) -> HealthData:
        return HealthData(
            status="healthy",
            service=self.settings.app_name,
            environment=self.settings.app_env,
            version="0.1.0",
            request_id=request_id,
            dependencies=[],
        )

    def build_readiness(self, request_id: str | None = None) -> HealthData:
        dependencies: list[HealthDependency] = []
        overall_status: Literal["healthy", "degraded", "unavailable"] = "healthy"

        try:
            ping_database()
            dependencies.append(
                HealthDependency(
                    name="database",
                    status="healthy",
                    required=True,
                    details={"engine": "postgresql", "pgvector_ready": "true"},
                )
            )
        except SQLAlchemyError as exc:
            overall_status = "unavailable"
            dependencies.append(
                HealthDependency(
                    name="database",
                    status="unavailable",
                    required=True,
                    details={"reason": exc.__class__.__name__},
                )
            )

        worker_status: Literal["healthy", "degraded", "unavailable"] = (
            "healthy" if self.settings.worker_enabled else "degraded"
        )
        if worker_status != "healthy" and overall_status == "healthy":
            overall_status = "degraded"
        dependencies.append(
            HealthDependency(
                name="worker",
                status=worker_status,
                required=False,
                details={"queue": self.settings.worker_queue, "redis_url_configured": "true"},
            )
        )

        dependencies.append(
            HealthDependency(
                name="ai_provider",
                status="healthy" if self.settings.ollama_model else "degraded",
                required=False,
                details={
                    "provider": "ollama",
                    "base_url": str(self.settings.ollama_base_url),
                    "model": self.settings.ollama_model or "missing",
                },
            )
        )

        return HealthData(
            status=overall_status,
            service=self.settings.app_name,
            environment=self.settings.app_env,
            version="0.1.0",
            request_id=request_id,
            dependencies=dependencies,
        )
