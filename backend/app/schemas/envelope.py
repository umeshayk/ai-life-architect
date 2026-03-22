from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResponseEnvelope(BaseModel, Generic[DataT]):
    success: bool
    data: DataT | None
    error: ErrorDetail | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


def success_response(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return ResponseEnvelope[Any](success=True, data=data, error=None, meta=meta or {}).model_dump()


def error_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return ResponseEnvelope[Any](
        success=False,
        data=None,
        error=ErrorDetail(code=code, message=message, details=details or {}),
        meta=meta or {},
    ).model_dump()
