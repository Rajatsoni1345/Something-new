"""
Birthday Quest - Flask Application

Application factory and global Flask configuration.

Architecture:

    Flask App
        |
        +-- Middleware
        |
        +-- API Routes
        |
        +-- Services
        |
        +-- Firebase / Cloudinary

The application factory keeps initialization predictable for:
- local development
- testing
- Render production deployment
"""

from __future__ import annotations

import logging
import os

from flask import Flask

from config import get_config

from extensions import init_extensions

from middleware.errors import register_error_middleware
from middleware.request_id import register_request_id_middleware
from middleware.security import register_security_middleware

from routes.health import health_bp
from routes.sessions import sessions_bp
from routes.quest import quest_bp
from routes.recordings import recordings_bp
from routes.reactions import reactions_bp


# ============================================================
# LOGGING
# ============================================================

def configure_logging(
    app: Flask,
) -> None:
    """
    Configure application-wide logging.

    Secrets and credentials must never be written to logs.
    """

    log_level_name = (
        app.config.get(
            "LOG_LEVEL",
            "INFO",
        )
        .upper()
    )

    log_level = getattr(
        logging,
        log_level_name,
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    app.logger.setLevel(
        log_level
    )


# ============================================================
# SECURITY HEADERS
# ============================================================

def register_security_headers(
    app: Flask,
) -> None:
    """
    Register security-related HTTP response headers.
    """

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(self), microphone=(self)",
        )

        if not app.debug:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response


# ============================================================
# BLUEPRINT REGISTRATION
# ============================================================

def register_blueprints(
    app: Flask,
) -> None:
    """
    Register every currently implemented API blueprint.

    API structure:

        /api/v1/health
        /api/v1/sessions
        /api/v1/quest
        /api/v1/recordings
        /api/v1/reactions
    """

    api_prefix = (
        app.config.get(
            "API_PREFIX",
            "/api/v1",
        )
        or "/api/v1"
    )

    app.register_blueprint(
        health_bp,
        url_prefix=f"{api_prefix}/health",
    )

    app.register_blueprint(
        sessions_bp,
        url_prefix=f"{api_prefix}/sessions",
    )

    app.register_blueprint(
        quest_bp,
        url_prefix=f"{api_prefix}/quest",
    )

    app.register_blueprint(
        recordings_bp,
        url_prefix=f"{api_prefix}/recordings",
    )

    app.register_blueprint(
        reactions_bp,
        url_prefix=f"{api_prefix}/reactions",
    )


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """

    config_class = get_config()

    app = Flask(
        __name__
    )

    app.config.from_object(
        config_class
    )

    app.config["MAX_CONTENT_LENGTH"] = (
        config_class.MAX_CONTENT_LENGTH
    )

    # --------------------------------------------------------
    # Core initialization
    # --------------------------------------------------------

    configure_logging(
        app
    )

    init_extensions(
        app
    )

    # --------------------------------------------------------
    # Middleware
    # --------------------------------------------------------

    register_security_headers(
        app
    )

    register_security_middleware(
        app
    )

    register_request_id_middleware(
        app
    )

    register_error_middleware(
        app
    )

    # --------------------------------------------------------
    # API routes
    # --------------------------------------------------------

    register_blueprints(
        app
    )

    # --------------------------------------------------------
    # Startup log
    # --------------------------------------------------------

    app.logger.info(
        "Birthday Quest backend initialized "
        "(environment=%s, api_prefix=%s)",
        config_class.FLASK_ENV,
        config_class.API_PREFIX,
    )

    return app


# ============================================================
# APPLICATION INSTANCE
# ============================================================

app = create_app()


# ============================================================
# LOCAL DEVELOPMENT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    host = os.getenv(
        "FLASK_HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "FLASK_PORT",
            "5000",
        )
    )

    app.run(
        host=host,
        port=port,
        debug=app.config.get(
            "DEBUG",
            False,
        ),
    )
