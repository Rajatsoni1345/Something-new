"""
Birthday Quest - Flask Extensions

Centralized extension objects.

Extensions are created here without binding them to a specific
Flask application. The application factory will initialize them
later using init_app().
"""

from __future__ import annotations

from flask_cors import CORS


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------

cors = CORS()


# ------------------------------------------------------------
# EXTENSION INITIALIZATION
# ------------------------------------------------------------

def init_extensions(app) -> None:
    """
    Initialize all Flask extensions.

    Keeping initialization in one place prevents circular
    imports and keeps the application factory clean.
    """

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get(
                    "FRONTEND_ORIGIN"
                )
            }
        },
        supports_credentials=False,
    )
