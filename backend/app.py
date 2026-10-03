"""
Birthday Quest - Flask Application

Application factory and global Flask configuration.
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


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

def configure_logging(app: Flask) -> None:
    """Configure application-wide logging."""

    log_level_name = app.config.get(
        "LOG_LEVEL",
        "INFO",
    ).upper()

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

    app.logger.setLevel(log_level)


# ------------------------------------------------------------
# SECURITY HEADERS
# ------------------------------------------------------------

def register_security_headers(app: Flask) -> None:
    """Attach baseline security headers to responses."""

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


# ------------------------------------------------------------
# BLUEPRINTS
# ------------------------------------------------------------

def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""

    api_prefix = app.config.get(
        "API_PREFIX",
        "/api/v1",
    )

    app.register_blueprint(
        health_bp,
        url_prefix=f"{api_prefix}/health",
    )


# ------------------------------------------------------------
# APPLICATION FACTORY
# ------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Birthday Quest Flask application.
    """

    config_class = get_config()

    app = Flask(__name__)

    # --------------------------------------------------------
    # LOAD CONFIGURATION
    # --------------------------------------------------------

    app.config.from_object(config_class)

    # --------------------------------------------------------
    # BASIC FLASK SETTINGS
    # --------------------------------------------------------

    app.config["MAX_CONTENT_LENGTH"] = (
        config_class.MAX_CONTENT_LENGTH
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    configure_logging(app)

    # --------------------------------------------------------
    # EXTENSIONS
    # --------------------------------------------------------

    init_extensions(app)

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    register_security_headers(app)
    register_security_middleware(app)

    # --------------------------------------------------------
    # REQUEST TRACKING
    # --------------------------------------------------------

    register_request_id_middleware(app)

    # --------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------

    register_error_middleware(app)

    # --------------------------------------------------------
    # ROUTES
    # --------------------------------------------------------

    register_blueprints(app)

    # --------------------------------------------------------
    # APPLICATION STARTUP LOG
    # --------------------------------------------------------

    app.logger.info(
        "Birthday Quest backend initialized "
        "(environment=%s)",
        config_class.FLASK_ENV,
    )

    return app


# ------------------------------------------------------------
# DEVELOPMENT ENTRY POINT
# ------------------------------------------------------------

app = create_app()


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
