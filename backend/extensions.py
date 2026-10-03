"""
Birthday Quest - Flask Extensions

Centralized Flask extension objects.

Extensions are created here without binding them to a specific
Flask application. The application factory initializes them
through init_extensions().
"""

from __future__ import annotations

from flask_cors import CORS


# ============================================================
# EXTENSIONS
# ============================================================

cors = CORS()


# ============================================================
# INITIALIZATION
# ============================================================

def init_extensions(
    app,
) -> None:
    """
    Initialize Flask extensions.

    CORS is restricted to the explicitly configured frontend
    origin.

    IMPORTANT:
    - Wildcard origins are not allowed.
    - Credentials are not required by the current API.
    - API routes only are exposed to cross-origin requests.
    """

    frontend_origin = (
        app.config.get(
            "FRONTEND_ORIGIN"
        )
        or ""
    ).strip()

    # --------------------------------------------------------
    # Development fallback
    # --------------------------------------------------------

    if not frontend_origin:
        if app.config.get(
            "FLASK_ENV"
        ) == "development":
            frontend_origin = (
                "http://localhost:3000"
            )
        else:
            raise RuntimeError(
                "FRONTEND_ORIGIN must be configured "
                "outside development."
            )

    # --------------------------------------------------------
    # Basic origin validation
    # --------------------------------------------------------

    if frontend_origin == "*":
        raise RuntimeError(
            "Wildcard CORS origin is not allowed."
        )

    if not (
        frontend_origin.startswith(
            "http://"
        )
        or frontend_origin.startswith(
            "https://"
        )
    ):
        raise RuntimeError(
            "FRONTEND_ORIGIN must be a valid "
            "HTTP or HTTPS origin."
        )

    # --------------------------------------------------------
    # Flask-CORS configuration
    # --------------------------------------------------------

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    frontend_origin
                ],
                "methods": [
                    "GET",
                    "POST",
                    "OPTIONS",
                ],
                "allow_headers": [
                    "Content-Type",
                    "Accept",
                ],
                "expose_headers": [
                    "X-Request-ID",
                ],
                "supports_credentials": False,
                "max_age": 600,
            }
        },
    )
