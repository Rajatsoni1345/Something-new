"""
Birthday Quest - Application Configuration

Centralized configuration for development, testing, and
production.

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

    raw_value = _get_env(name, default)

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

    Environment variables commonly store newline characters as
    the literal sequence '\\n'.
    """

    if not value:
        return None

    return value.replace("\\n", "\n")


# ------------------------------------------------------------
# APPLICATION DEFAULTS
# ------------------------------------------------------------

DEFAULT_APP_NAME: Final[str] = "Birthday Quest"
DEFAULT_FLASK_ENV: Final[str] = "development"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

DEFAULT_MAX_CONTENT_LENGTH: Final[int] = 250 * 1024 * 1024
DEFAULT_API_PREFIX: Final[str] = "/api/v1"


# ------------------------------------------------------------
# CONFIGURATION CLASS
# ------------------------------------------------------------

class Config:
    """Base application configuration."""

    # Application
    APP_NAME: str = (
        _get_env("APP_NAME", DEFAULT_APP_NAME) or DEFAULT_APP_NAME
    )

    FLASK_ENV: str = (
        _get_env("FLASK_ENV", DEFAULT_FLASK_ENV) or DEFAULT_FLASK_ENV
    )

    API_PREFIX: str = (
        _get_env("API_PREFIX", DEFAULT_API_PREFIX) or DEFAULT_API_PREFIX
    )

    SECRET_KEY: str | None = _get_env("SECRET_KEY")

    MAX_CONTENT_LENGTH: int = _get_int_env(
        "MAX_CONTENT_LENGTH",
        DEFAULT_MAX_CONTENT_LENGTH,
    )

    FRONTEND_ORIGIN: str | None = _get_env("FRONTEND_ORIGIN")

    TRUSTED_HOSTS: list[str] = _get_list_env(
        "TRUSTED_HOSTS",
        "localhost,127.0.0.1",
    )

    LOG_LEVEL: str = (
        _get_env("LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL
    ).upper()

    # Firebase
    FIREBASE_PROJECT_ID: str | None = _get_env("FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY_ID: str | None = _get_env("FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_PRIVATE_KEY: str | None = _normalize_private_key(
        _get_env("FIREBASE_PRIVATE_KEY")
    )
    FIREBASE_CLIENT_EMAIL: str | None = _get_env("FIREBASE_CLIENT_EMAIL")
    FIREBASE_CLIENT_ID: str | None = _get_env("FIREBASE_CLIENT_ID")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str | None = _get_env("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str | None = _get_env("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str | None = _get_env("CLOUDINARY_API_SECRET")

    # Admin
    ADMIN_UIDS: list[str] = _get_list_env("ADMIN_UIDS")
    ADMIN_EMAILS: list[str] = [
        email.lower()
        for email in _get_list_env("ADMIN_EMAILS")
    ]

    # Session cookie security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # Environment flags
    TESTING: bool = False
    DEBUG: bool = False

    @classmethod
    def validate(cls) -> None:
        """
        Validate configuration required for the current
        environment.

        Development and testing intentionally do not require
        production credentials so the application can be built
        and tested incrementally.

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

        if cls.MAX_CONTENT_LENGTH <= 0:
            raise ValueError(
                "MAX_CONTENT_LENGTH must be greater than zero."
            )

        if not cls.API_PREFIX.startswith("/"):
            raise ValueError("API_PREFIX must start with '/'.")

        if not cls.TRUSTED_HOSTS:
            raise RuntimeError(
                "TRUSTED_HOSTS must contain at least one host."
            )

        if environment == "production":
            if not cls.ADMIN_UIDS:
                raise RuntimeError(
                    "ADMIN_UIDS must contain at least one "
                    "authorized Firebase user UID in production."
                )

        if environment == "production":
            required_values = {
                "SECRET_KEY": cls.SECRET_KEY,
                "FRONTEND_ORIGIN": cls.FRONTEND_ORIGIN,
                "FIREBASE_PROJECT_ID": cls.FIREBASE_PROJECT_ID,
                "FIREBASE_PRIVATE_KEY_ID": cls.FIREBASE_PRIVATE_KEY_ID,
                "FIREBASE_PRIVATE_KEY": cls.FIREBASE_PRIVATE_KEY,
                "FIREBASE_CLIENT_EMAIL": cls.FIREBASE_CLIENT_EMAIL,
                "FIREBASE_CLIENT_ID": cls.FIREBASE_CLIENT_ID,
                "CLOUDINARY_CLOUD_NAME": cls.CLOUDINARY_CLOUD_NAME,
                "CLOUDINARY_API_KEY": cls.CLOUDINARY_API_KEY,
                "CLOUDINARY_API_SECRET": cls.CLOUDINARY_API_SECRET,
            }

            missing = [
                name for name, value in required_values.items() if not value
            ]

            if missing:
                raise RuntimeError(
                    "Missing required production environment "
                    f"variables: {', '.join(missing)}"
                )

            if cls.SECRET_KEY == "change-this-to-a-long-random-secret":
                raise RuntimeError(
                    "The default development SECRET_KEY cannot "
                    "be used in production."
                )


# ------------------------------------------------------------
# ENVIRONMENT CONFIGURATIONS
# ------------------------------------------------------------

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
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


def get_config(
    environment: str | None = None,
) -> type[Config]:
    """
    Return the configuration class matching the requested or
    configured FLASK_ENV.

    Priority:
        1. Explicit `environment` argument (used by tests)
        2. FLASK_ENV environment variable
        3. Development fallback

    This makes `create_app("testing")` possible without
    polluting global environment state.
    """

    if environment is not None:
        normalized = environment.strip().lower()
    else:
        normalized = (
            _get_env("FLASK_ENV", DEFAULT_FLASK_ENV) or DEFAULT_FLASK_ENV
        ).lower()

    try:
        config_class = CONFIG_MAP[normalized]
    except KeyError as exc:
        raise ValueError(
            "FLASK_ENV must be one of: "
            "development, production, testing."
        ) from exc

    # Validate against the SELECTED environment, not the global
    # FLASK_ENV. This lets tests run cleanly.
    original_env = os.environ.get("FLASK_ENV")
    os.environ["FLASK_ENV"] = normalized

    try:
        config_class.validate()
    finally:
        if original_env is None:
            os.environ.pop("FLASK_ENV", None)
        else:
            os.environ["FLASK_ENV"] = original_env

    return config_class
