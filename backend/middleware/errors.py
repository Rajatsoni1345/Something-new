"""
Birthday Quest - Error Middleware

Centralized application and HTTP error handling.
"""

from __future__ import annotations

import logging

from flask import Flask, current_app
from werkzeug.exceptions import HTTPException

from utils.responses import error_response


# ------------------------------------------------------------
# REGISTRATION
# ------------------------------------------------------------

def register_error_middleware(app: Flask) -> None:
    """
    Register centralized Flask error handlers.
    """

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """
        Convert standard Werkzeug/Flask HTTP errors into the
        application's consistent JSON response format.
        """

        return error_response(
            code=_http_error_code(error),
            message=error.description,
            status_code=error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        """
        Catch unexpected application exceptions.

        Full exception details are logged server-side but are
        never exposed to the client.
        """

        current_app.logger.exception(
            "Unhandled application exception.",
            exc_info=error,
        )

        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred.",
            status_code=500,
        )


# ------------------------------------------------------------
# HTTP ERROR CODE
# ------------------------------------------------------------

def _http_error_code(error: HTTPException) -> str:
    """
    Convert an HTTP status into a stable application error code.

    Example:
        404 -> NOT_FOUND
        405 -> METHOD_NOT_ALLOWED
    """

    status_code = error.code or 500

    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        413: "REQUEST_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
    }

    return mapping.get(
        status_code,
        f"HTTP_ERROR_{status_code}",
    )
