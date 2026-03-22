from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthDependency(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "unavailable"]
    required: bool
    details: dict[str, str] = Field(default_factory=dict)


class HealthData(BaseModel):
    status: Literal["healthy", "degraded", "unavailable"]
    service: str
    environment: str
    version: str
    request_id: str | None = None
    dependencies: list[HealthDependency] = Field(default_factory=list)
