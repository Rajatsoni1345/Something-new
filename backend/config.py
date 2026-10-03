"""
Birthday Quest - Application Configuration

Centralized configuration for development and production.

IMPORTANT:
- Never store real secrets in source code.
- Development may use safe local defaults.
- Production requires required secrets to be supplied through
  environment variables.
- Admin identities are configured through environment variables.
"""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv


# ------------------------------------------------------------
# LOAD ENVIRONMENT
# ------------------------------------------------------------

# Loads .env during local development.
# Render/production environment variables are loaded by the
# deployment environment itself.
load_dotenv()


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def _get_env(
    name: str,
    default: str | None = None,
) -> str | None:
    """Return a trimmed environment variable or the default."""

    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    return value if value else default


def _get_int_env(
    name: str,
    default: int,
) -> int:
    """Read a positive integer environment variable safely."""

    raw_value = _get_env(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name} must be a valid integer."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"Environment variable {name} must be greater than zero."
        )

    return value


def _get_list_env(
    name: str,
    default: str = "",
) -> list[str]:
    """
    Read a comma-separated environment variable.

    Example:
        ADMIN_UIDS=uid_one,uid_two

    becomes:
        ["uid_one", "uid_two"]
    """

    raw_value = _get_env(
        name,
        default,
    )

    if not raw_value:
        return []

    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


def _normalize_private_key(
    value: str | None,
) -> str | None:
    """
    Normalize Firebase private key formatting.

    Environment variables commonly store newline characters
    as the literal sequence '\\n'.
    """

    if not value:
        return None

    return value.replace(
        "\\n",
        "\n",
    )


# ------------------------------------------------------------
# APPLICATION DEFAULTS
# ------------------------------------------------------------

DEFAULT_APP_NAME: Final[str] = "Birthday Quest"
DEFAULT_FLASK_ENV: Final[str] = "development"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

# 250 MB maximum incoming request size.
DEFAULT_MAX_CONTENT_LENGTH: Final[int] = (
    250 * 1024 * 1024
)

DEFAULT_API_PREFIX: Final[str] = "/api/v1"


# ------------------------------------------------------------
# CONFIGURATION CLASS
# ------------------------------------------------------------

class Config:
    """Base application configuration."""

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    APP_NAME: str = (
        _get_env(
            "APP_NAME",
            DEFAULT_APP_NAME,
        )
        or DEFAULT_APP_NAME
    )

    FLASK_ENV: str = (
        _get_env(
            "FLASK_ENV",
            DEFAULT_FLASK_ENV,
        )
        or DEFAULT_FLASK_ENV
    )

    API_PREFIX: str = (
        _get_env(
            "API_PREFIX",
            DEFAULT_API_PREFIX,
        )
        or DEFAULT_API_PREFIX
    )

    # --------------------------------------------------------
    # APPLICATION SECRET
    # --------------------------------------------------------

    SECRET_KEY: str | None = _get_env(
        "SECRET_KEY"
    )

    # --------------------------------------------------------
    # REQUEST LIMITS
    # --------------------------------------------------------

    MAX_CONTENT_LENGTH: int = _get_int_env(
        "MAX_CONTENT_LENGTH",
        DEFAULT_MAX_CONTENT_LENGTH,
    )

    # --------------------------------------------------------
    # FRONTEND / CORS
    # --------------------------------------------------------

    FRONTEND_ORIGIN: str | None = _get_env(
        "FRONTEND_ORIGIN"
    )

    # --------------------------------------------------------
    # TRUSTED HOSTS
    # --------------------------------------------------------

    TRUSTED_HOSTS: list[str] = _get_list_env(
        "TRUSTED_HOSTS",
        "localhost,127.0.0.1",
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    LOG_LEVEL: str = (
        _get_env(
            "LOG_LEVEL",
            DEFAULT_LOG_LEVEL,
        )
        or DEFAULT_LOG_LEVEL
    ).upper()

    # --------------------------------------------------------
    # FIREBASE
    # --------------------------------------------------------

    FIREBASE_PROJECT_ID: str | None = _get_env(
        "FIREBASE_PROJECT_ID"
    )

    FIREBASE_PRIVATE_KEY_ID: str | None = _get_env(
        "FIREBASE_PRIVATE_KEY_ID"
    )

    FIREBASE_PRIVATE_KEY: str | None = (
        _normalize_private_key(
            _get_env("FIREBASE_PRIVATE_KEY")
        )
    )

    FIREBASE_CLIENT_EMAIL: str | None = _get_env(
        "FIREBASE_CLIENT_EMAIL"
    )

    FIREBASE_CLIENT_ID: str | None = _get_env(
        "FIREBASE_CLIENT_ID"
    )

    # --------------------------------------------------------
    # CLOUDINARY
    # --------------------------------------------------------

    CLOUDINARY_CLOUD_NAME: str | None = _get_env(
        "CLOUDINARY_CLOUD_NAME"
    )

    CLOUDINARY_API_KEY: str | None = _get_env(
        "CLOUDINARY_API_KEY"
    )

    CLOUDINARY_API_SECRET: str | None = _get_env(
        "CLOUDINARY_API_SECRET"
    )

    # --------------------------------------------------------
    # ADMIN ACCESS
    # --------------------------------------------------------
    #
    # ADMIN_UIDS is the primary authorization mechanism.
    #
    # Example:
    # ADMIN_UIDS=firebase_uid_1,firebase_uid_2
    #
    # ADMIN_EMAILS is optional and can be used as an additional
    # identity allowlist after Firebase token verification.
    #
    # These values are never hard-coded into source code.
    # --------------------------------------------------------

    ADMIN_UIDS: list[str] = _get_list_env(
        "ADMIN_UIDS"
    )

    ADMIN_EMAILS: list[str] = [
        email.lower()
        for email in _get_list_env(
            "ADMIN_EMAILS"
        )
    ]

    # --------------------------------------------------------
    # SESSION COOKIE SECURITY
    # --------------------------------------------------------

    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # --------------------------------------------------------
    # ENVIRONMENT FLAGS
    # --------------------------------------------------------

    TESTING: bool = False
    DEBUG: bool = False

    @classmethod
    def validate(cls) -> None:
        """
        Validate configuration required for the current
        environment.

        Development intentionally does not require production
        credentials so the application can be built incrementally.

        Production fails fast if critical secrets/configuration
        are missing.
        """

        environment = cls.FLASK_ENV.lower()

        if environment not in {
            "development",
            "production",
            "testing",
        }:
            raise ValueError(
                "FLASK_ENV must be one of: "
                "development, production, testing."
            )

        # ----------------------------------------------------
        # General configuration validation
        # ----------------------------------------------------

        if cls.MAX_CONTENT_LENGTH <= 0:
            raise ValueError(
                "MAX_CONTENT_LENGTH must be greater than zero."
            )

        if not cls.API_PREFIX.startswith("/"):
            raise ValueError(
                "API_PREFIX must start with '/'."
            )

        # ----------------------------------------------------
        # Trusted hosts
        # ----------------------------------------------------

        if not cls.TRUSTED_HOSTS:
            raise RuntimeError(
                "TRUSTED_HOSTS must contain at least one host."
            )

        # ----------------------------------------------------
        # Admin configuration
        # ----------------------------------------------------

        if environment == "production":
            if not cls.ADMIN_UIDS:
                raise RuntimeError(
                    "ADMIN_UIDS must contain at least one "
                    "authorized Firebase user UID in production."
                )

        # ----------------------------------------------------
        # Production secrets
        # ----------------------------------------------------

        if environment == "production":
            required_values = {
                "SECRET_KEY": cls.SECRET_KEY,
                "FRONTEND_ORIGIN": cls.FRONTEND_ORIGIN,
                "FIREBASE_PROJECT_ID": cls.FIREBASE_PROJECT_ID,
                "FIREBASE_PRIVATE_KEY_ID": (
                    cls.FIREBASE_PRIVATE_KEY_ID
                ),
                "FIREBASE_PRIVATE_KEY": (
                    cls.FIREBASE_PRIVATE_KEY
                ),
                "FIREBASE_CLIENT_EMAIL": (
                    cls.FIREBASE_CLIENT_EMAIL
                ),
                "FIREBASE_CLIENT_ID": (
                    cls.FIREBASE_CLIENT_ID
                ),
                "CLOUDINARY_CLOUD_NAME": (
                    cls.CLOUDINARY_CLOUD_NAME
                ),
                "CLOUDINARY_API_KEY": (
                    cls.CLOUDINARY_API_KEY
                ),
                "CLOUDINARY_API_SECRET": (
                    cls.CLOUDINARY_API_SECRET
                ),
            }

            missing = [
                name
                for name, value in required_values.items()
                if not value
            ]

            if missing:
                raise RuntimeError(
                    "Missing required production environment "
                    f"variables: {', '.join(missing)}"
                )

            if cls.SECRET_KEY == (
                "change-this-to-a-long-random-secret"
            ):
                raise RuntimeError(
                    "The default development SECRET_KEY cannot "
                    "be used in production."
                )


# ------------------------------------------------------------
# DEVELOPMENT CONFIGURATION
# ------------------------------------------------------------

class DevelopmentConfig(Config):
    """Local development configuration."""

    DEBUG = True
    TESTING = False


# ------------------------------------------------------------
# PRODUCTION CONFIGURATION
# ------------------------------------------------------------

class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False


# ------------------------------------------------------------
# TEST CONFIGURATION
# ------------------------------------------------------------

class TestingConfig(Config):
    """Automated testing configuration."""

    DEBUG = False
    TESTING = True


# ------------------------------------------------------------
# CONFIGURATION SELECTOR
# ------------------------------------------------------------

CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> type[Config]:
    """
    Return the configuration class matching FLASK_ENV.
    """

    environment = (
        _get_env(
            "FLASK_ENV",
            DEFAULT_FLASK_ENV,
        )
        or DEFAULT_FLASK_ENV
    ).lower()

    try:
        config_class = CONFIG_MAP[
            environment
        ]
    except KeyError as exc:
        raise ValueError(
            "FLASK_ENV must be one of: "
            "development, production, testing."
        ) from exc

    config_class.validate()

    return config_class
