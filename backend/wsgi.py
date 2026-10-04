"""
Birthday Quest - WSGI Entry Point

Gunicorn / production servers import this module.

Render start command:
    gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
"""

from __future__ import annotations

from app import create_app


# Production instance.
# Environment is resolved from FLASK_ENV (Render env var).
app = create_app()
