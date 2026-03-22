from __future__ import annotations

import logging


def bind_request_id(
    logger: logging.Logger,
    request_id: str | None,
) -> logging.LoggerAdapter[logging.Logger]:
    return logging.LoggerAdapter(logger, extra={"request_id": request_id or "unknown"})
