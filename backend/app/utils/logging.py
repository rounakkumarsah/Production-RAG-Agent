"""
Centralised logging configuration.
Call `setup_logging()` once at application startup.
"""

import logging
import sys
from typing import Literal


def setup_logging(
    level: str = "INFO",
    environment: Literal["development", "staging", "production"] = "development",
) -> None:
    """
    Configure root logger with a structured format.

    In development  → human-readable coloured output.
    In staging/prod → JSON-style single-line output (ready for log-aggregators).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if environment == "development":
        fmt = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        )
        datefmt = "%Y-%m-%d %H:%M:%S"
    else:
        # Single-line, parseable by Datadog / Loki / CloudWatch
        fmt = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","line":%(lineno)d,"msg":"%(message)s"}'
        )
        datefmt = "%Y-%m-%dT%H:%M:%SZ"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ("httpx", "httpcore", "asyncio", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — level=%s env=%s", level, environment
    )


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper so modules don't import `logging` directly."""
    return logging.getLogger(name)
