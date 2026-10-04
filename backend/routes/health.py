"""
Birthday Quest - Health Check Routes

Provides lightweight endpoints for checking whether the
backend is running correctly.

URL prefix is declared centrally in app.py. Blueprints never
declare their own prefix.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("")
def health_check():
    """
    Basic backend health check.

    Intentionally does not contact Firebase, Cloudinary, or any
    external service. Only confirms the Flask process is alive.
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    ), 200
