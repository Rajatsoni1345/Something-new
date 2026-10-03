"""
Birthday Quest - Health Check Routes

Provides lightweight endpoints for checking whether the
backend is running correctly.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify


# ------------------------------------------------------------
# BLUEPRINT
# ------------------------------------------------------------

health_bp = Blueprint(
    "health",
    __name__,
    url_prefix="/health",
)


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@health_bp.get("")
def health_check():
    """
    Basic backend health check.

    This endpoint intentionally does not contact Firebase,
    Cloudinary, or any external service. It only confirms that
    the Flask application process is alive.
    """

    return jsonify(
        {
            "success": True,
            "data": {
                "status": "healthy",
                "service": current_app.config.get(
                    "APP_NAME",
                    "Birthday Quest",
                ),
                "environment": current_app.config.get(
                    "FLASK_ENV",
                    "unknown",
                ),
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
        }
    ), 200
