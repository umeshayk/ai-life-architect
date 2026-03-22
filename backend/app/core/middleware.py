from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

RequestHandler = Callable[[Request], Awaitable[Response]]


async def correlation_middleware(request: Request, call_next: RequestHandler) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


async def timing_middleware(request: Request, call_next: RequestHandler) -> Response:
    started_at = time.perf_counter()
    response = await call_next(request)
    response.headers["x-response-time-ms"] = f"{(time.perf_counter() - started_at) * 1000:.2f}"
    return response
