"""Structured logging configuration and upstream failure context."""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """Render application log records as one JSON object per line."""

    fields = (
        "event",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "dataset",
        "dataset_id",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.fields:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str) -> None:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app_logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    app_logger.handlers = [handler]


def log_upstream_error(
    logger: logging.Logger,
    dataset: str,
    error: Exception,
    dataset_id: str | None = None,
) -> None:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    logger.error(
        "Upstream request failed",
        extra={
            "dataset": dataset,
            "dataset_id": dataset_id,
            "status_code": status_code,
            "error_type": type(error).__name__,
        },
    )
