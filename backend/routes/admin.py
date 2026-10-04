"""
Birthday Quest - Admin Routes

Administrative authentication and protected admin endpoints.

URL prefix is declared centrally in app.py.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, g, request

from firebase_admin import auth

from config import get_config
from services.firebase_service import get_firebase_app
from utils.responses import error_response, success_response


admin_bp = Blueprint("admin", __name__)


# ============================================================
# AUTH HELPERS
# ============================================================

def _get_bearer_token() -> str | None:
    authorization = request.headers.get("Authorization", "")

    if not isinstance(authorization, str):
        return None

    authorization = authorization.strip()

    if not authorization:
        return None

    parts = authorization.split(" ", 1)

    if len(parts) != 2:
        return None

    scheme, token = parts

    if scheme.lower() != "bearer":
        return None

    token = token.strip()

    if not token:
        return None

    return token


def _verify_firebase_token(token: str) -> dict[str, Any]:
    if not isinstance(token, str):
        raise ValueError("Firebase token must be a string.")

    token = token.strip()

    if not token:
        raise ValueError("Firebase token cannot be empty.")

    firebase_app = get_firebase_app()

    return auth.verify_id_token(
        token,
        app=firebase_app,
        check_revoked=True,
    )


def _is_authorized_admin(decoded_token: dict[str, Any]) -> bool:
    config = get_config()

    uid = decoded_token.get("uid")

    if isinstance(uid, str):
        uid = uid.strip()
        if uid and uid in config.ADMIN_UIDS:
            return True

    email = decoded_token.get("email")
    email_verified = decoded_token.get("email_verified", False)

    if isinstance(email, str) and email_verified is True:
        normalized_email = email.strip().lower()
        if normalized_email and normalized_email in config.ADMIN_EMAILS:
            return True

    return False


def _sanitize_admin_identity(decoded_token: dict[str, Any]) -> dict[str, Any]:
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    email_verified = decoded_token.get("email_verified", False)

    return {
        "uid": uid if isinstance(uid, str) else None,
        "email": email if isinstance(email, str) else None,
        "email_verified": email_verified is True,
    }


# ============================================================
# ADMIN DECORATOR
# ============================================================

def require_admin(view_function: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view_function)
    def wrapped_view(*args: Any, **kwargs: Any):
        token = _get_bearer_token()

        if token is None:
            return error_response(
                code="AUTHENTICATION_REQUIRED",
                message="A valid Firebase Bearer token is required.",
                status_code=401,
            )

        try:
            decoded_token = _verify_firebase_token(token)

        except auth.ExpiredIdTokenError:
            return error_response(
                code="AUTHENTICATION_EXPIRED",
                message="The Firebase authentication token has expired.",
                status_code=401,
            )

        except auth.RevokedIdTokenError:
            return error_response(
                code="AUTHENTICATION_REVOKED",
                message="The Firebase authentication token has been revoked.",
                status_code=401,
            )

        except (auth.InvalidIdTokenError, ValueError):
            return error_response(
                code="INVALID_AUTHENTICATION",
                message="The Firebase authentication token is invalid.",
                status_code=401,
            )

        except Exception:
            return error_response(
                code="AUTHENTICATION_ERROR",
                message="Authentication could not be completed.",
                status_code=401,
            )

        if not _is_authorized_admin(decoded_token):
            uid = decoded_token.get("uid", "unknown")

            try:
                from flask import current_app
                current_app.logger.warning(
                    "Unauthorized admin access attempt for UID: %s",
                    uid,
                )
            except Exception:
                pass

            return error_response(
                code="ADMIN_ACCESS_DENIED",
                message="You are not authorized to access this resource.",
                status_code=403,
            )

        g.admin_identity = decoded_token

        return view_function(*args, **kwargs)

    return wrapped_view


# ============================================================
# ENDPOINTS
# ============================================================

@admin_bp.get("/me")
@require_admin
def get_admin_identity():
    identity = getattr(g, "admin_identity", None)

    if not isinstance(identity, dict):
        return error_response(
            code="ADMIN_CONTEXT_MISSING",
            message="The authenticated admin context is unavailable.",
            status_code=500,
        )

    return success_response(
        data={
            "authenticated": True,
            "admin": _sanitize_admin_identity(identity),
        }
            )
