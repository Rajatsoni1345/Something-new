"""
Birthday Quest - API Response Utilities

Centralized helpers for consistent JSON API responses.
"""

from __future__ import annotations

from typing import Any

from flask import jsonify


# ------------------------------------------------------------
# SUCCESS RESPONSE
# ------------------------------------------------------------

def success_response(
    data: Any = None,
    status_code: int = 200,
):
    """
    Return a standardized successful API response.

    Example:
    {
        "success": true,
        "data": {...}
    }
    """

    return jsonify(
        {
            "success": True,
            "data": data,
        }
    ), status_code


# ------------------------------------------------------------
# ERROR RESPONSE
# ------------------------------------------------------------

def error_response(
    code: str,
    message: str,
    status_code: int,
    details: Any = None,
):
    """
    Return a standardized API error response.

    Example:
    {
        "success": false,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "...",
            "details": {...}
        }
    }
    """

    error_data: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if details is not None:
        error_data["details"] = details

    return jsonify(
        {
            "success": False,
            "error": error_data,
        }
    ), status_code


# ------------------------------------------------------------
# COMMON ERROR HELPERS
# ------------------------------------------------------------

def bad_request(
    message: str = "The request is invalid.",
    details: Any = None,
):
    """Return a 400 Bad Request response."""

    return error_response(
        code="BAD_REQUEST",
        message=message,
        status_code=400,
        details=details,
    )


def unauthorized(
    message: str = "Authentication is required.",
    details: Any = None,
):
    """Return a 401 Unauthorized response."""

    return error_response(
        code="UNAUTHORIZED",
        message=message,
        status_code=401,
        details=details,
    )


def forbidden(
    message: str = "You are not allowed to perform this action.",
    details: Any = None,
):
    """Return a 403 Forbidden response."""

    return error_response(
        code="FORBIDDEN",
        message=message,
        status_code=403,
        details=details,
    )


def not_found(
    message: str = "The requested resource was not found.",
    details: Any = None,
):
    """Return a 404 Not Found response."""

    return error_response(
        code="NOT_FOUND",
        message=message,
        status_code=404,
        details=details,
    )


def conflict(
    message: str = "The request conflicts with the current state.",
    details: Any = None,
):
    """Return a 409 Conflict response."""

    return error_response(
        code="CONFLICT",
        message=message,
        status_code=409,
        details=details,
    )


def too_many_requests(
    message: str = "Too many requests.",
    details: Any = None,
):
    """Return a 429 Too Many Requests response."""

    return error_response(
        code="TOO_MANY_REQUESTS",
        message=message,
        status_code=429,
        details=details,
    )


def internal_server_error(
    message: str = "An internal server error occurred.",
    details: Any = None,
):
    """
    Return a 500 Internal Server Error response.

    Internal implementation details should NOT be exposed to
    the client in production.
    """

    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message=message,
        status_code=500,
        details=details,
  )
