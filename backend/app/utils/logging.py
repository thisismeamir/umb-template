# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN — Apache License 2.0
#  Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------
"""
Structured logger factory.

All modules get a logger via:
    from app.utils.logging import get_logger
    logger = get_logger(__name__)

Format emits JSON in production (debug=False) so log aggregators
(Loki, ELK) can index fields directly. In debug mode it emits a
readable plain-text format instead.
"""
import json
import logging
import sys

from app.config import get_settings


class _JsonFormatter(logging.Formatter):
    """Emits each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level"   : record.levelname,
            "logger"  : record.name,
            "message" : record.getMessage(),
        }
        # Merge any extra= fields passed by the caller (e.g. from LoggingMiddleware)
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def _build_handler() -> logging.Handler:
    handler   = logging.StreamHandler(sys.stdout)
    settings  = get_settings()

    if settings.debug:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%H:%M:%S",
        ))
    else:
        handler.setFormatter(_JsonFormatter())

    return handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.addHandler(_build_handler())
        logger.setLevel(logging.DEBUG if get_settings().debug else logging.INFO)
        logger.propagate = False

    return logger