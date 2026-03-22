from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.schemas.common import ApiResponse
from app.schemas.health import HealthData
from app.services.health_service import HealthService

router = APIRouter()


def get_health_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthService:
    return HealthService(settings)


@router.get("/live", response_model=ApiResponse[HealthData])
async def live(
    request: Request,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> ApiResponse[HealthData]:
    return ApiResponse(data=service.build_liveness(getattr(request.state, "request_id", None)))


@router.get("/ready", response_model=ApiResponse[HealthData])
async def ready(
    request: Request,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> JSONResponse:
    payload = ApiResponse(data=service.build_readiness(getattr(request.state, "request_id", None)))
    status_code = (
        status.HTTP_200_OK
        if payload.data.status != "unavailable"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.get("/details", response_model=ApiResponse[HealthData])
async def details(
    request: Request,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> ApiResponse[HealthData]:
    return ApiResponse(data=service.build_readiness(getattr(request.state, "request_id", None)))
