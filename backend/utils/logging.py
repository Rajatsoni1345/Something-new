"""
Birthday Quest - Logging Utilities

Centralized logging helpers for the backend.
"""

from __future__ import annotations

import logging
from typing import Any


# ------------------------------------------------------------
# LOGGER
# ------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Return a named application logger.
    """

    return logging.getLogger(name)


# ------------------------------------------------------------
# STRUCTURED LOG CONTEXT
# ------------------------------------------------------------

def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **context: Any,
) -> None:
    """
    Write a structured application event to the logger.

    Context values are included as key=value pairs.
    Sensitive values such as passwords, API keys, and tokens
    must never be passed into this function.
    """

    safe_context = " ".join(
        f"{key}={value!r}"
        for key, value in context.items()
        if value is not None
    )

    if safe_context:
        message = f"event={event} {safe_context}"
    else:
        message = f"event={event}"

    logger.log(level, message)


# ------------------------------------------------------------
# COMMON EVENTS
# ------------------------------------------------------------

def log_info(
    logger: logging.Logger,
    event: str,
    **context: Any,
) -> None:
    """Log an informational event."""

    log_event(
        logger,
        logging.INFO,
        event,
        **context,
    )


def log_warning(
    logger: logging.Logger,
    event: str,
    **context: Any,
) -> None:
    """Log a warning event."""

    log_event(
        logger,
        logging.WARNING,
        event,
        **context,
    )


def log_error(
    logger: logging.Logger,
    event: str,
    **context: Any,
) -> None:
    """Log an error event."""

    log_event(
        logger,
        logging.ERROR,
        event,
        **context,
)
