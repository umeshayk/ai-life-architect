from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse[DataT](BaseModel):
    success: bool = True
    data: DataT
    error: ErrorDetail | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    error: ErrorDetail
    meta: dict[str, Any] = Field(default_factory=dict)
