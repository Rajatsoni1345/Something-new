"""
Birthday Quest - Admin Routes

Administrative authentication and protected admin endpoints.

Security model:
- Firebase ID token is required.
- Firebase Admin SDK verifies the token server-side.
- Firebase UID is the primary admin allowlist.
- Optionally, a verified Firebase email may also be allowlisted.
- No admin credentials are stored in source code.
- Normal Birthday Quest sessions do not grant admin access.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, g, request

from firebase_admin import auth

from config import get_config
from services.firebase_service import get_firebase_app
from utils.responses import error_response, success_response


# ============================================================
# BLUEPRINT
# ============================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/v1/admin",
)


# ============================================================
# ADMIN AUTHENTICATION HELPERS
# ============================================================

def _get_bearer_token() -> str | None:
    """
    Extract a Bearer token from the Authorization header.

    Expected format:

        Authorization: Bearer <firebase-id-token>
    """

    authorization = request.headers.get(
        "Authorization",
        "",
    )

    if not isinstance(
        authorization,
        str,
    ):
        return None

    authorization = authorization.strip()

    if not authorization:
        return None

    parts = authorization.split(
        " ",
        1,
    )

    if len(parts) != 2:
        return None

    scheme, token = parts

    if scheme.lower() != "bearer":
        return None

    token = token.strip()

    if not token:
        return None

    return token


def _verify_firebase_token(
    token: str,
) -> dict[str, Any]:
    """
    Verify a Firebase ID token using the Firebase Admin SDK.

    The Firebase app is initialized through the existing
    firebase_service layer.
    """

    if not isinstance(
        token,
        str,
    ):
        raise ValueError(
            "Firebase token must be a string."
        )

    token = token.strip()

    if not token:
        raise ValueError(
            "Firebase token cannot be empty."
        )

    # Ensure the existing centralized Firebase initialization
    # has completed before token verification.
    firebase_app = get_firebase_app()

    return auth.verify_id_token(
        token,
        app=firebase_app,
        check_revoked=True,
    )


def _is_authorized_admin(
    decoded_token: dict[str, Any],
) -> bool:
    """
    Determine whether a verified Firebase identity is an admin.

    UID is the primary authorization mechanism.

    Email authorization is allowed only when:
    - the email exists,
    - Firebase marks the email as verified,
    - and the normalized email appears in ADMIN_EMAILS.
    """

    config = get_config()

    uid = decoded_token.get(
        "uid"
    )

    if isinstance(
        uid,
        str,
    ):
        uid = uid.strip()

        if uid and uid in config.ADMIN_UIDS:
            return True

    email = decoded_token.get(
        "email"
    )

    email_verified = decoded_token.get(
        "email_verified",
        False,
    )

    if (
        isinstance(email, str)
        and email_verified is True
    ):
        normalized_email = email.strip().lower()

        if (
            normalized_email
            and normalized_email in config.ADMIN_EMAILS
        ):
            return True

    return False


def _sanitize_admin_identity(
    decoded_token: dict[str, Any],
) -> dict[str, Any]:
    """
    Return only safe identity fields for an admin response.

    Firebase tokens contain claims that should not be blindly
    returned to the client.
    """

    uid = decoded_token.get(
        "uid"
    )

    email = decoded_token.get(
        "email"
    )

    email_verified = decoded_token.get(
        "email_verified",
        False,
    )

    return {
        "uid": uid
        if isinstance(uid, str)
        else None,
        "email": email
        if isinstance(email, str)
        else None,
        "email_verified": (
            email_verified is True
        ),
    }


# ============================================================
# ADMIN DECORATOR
# ============================================================

def require_admin(
    view_function: Callable[..., Any],
) -> Callable[..., Any]:
    """
    Protect an endpoint with Firebase authentication and
    Birthday Quest admin authorization.

    The verified Firebase identity is stored in Flask's request
    context as:

        g.admin_identity
    """

    @wraps(view_function)
    def wrapped_view(
        *args: Any,
        **kwargs: Any,
    ):
        token = _get_bearer_token()

        if token is None:
            return error_response(
                code="AUTHENTICATION_REQUIRED",
                message=(
                    "A valid Firebase Bearer token is required."
                ),
                status_code=401,
            )

        try:
            decoded_token = _verify_firebase_token(
                token
            )

        except auth.ExpiredIdTokenError:
            return error_response(
                code="AUTHENTICATION_EXPIRED",
                message=(
                    "The Firebase authentication token has expired."
                ),
                status_code=401,
            )

        except auth.RevokedIdTokenError:
            return error_response(
                code="AUTHENTICATION_REVOKED",
                message=(
                    "The Firebase authentication token has been revoked."
                ),
                status_code=401,
            )

        except (
            auth.InvalidIdTokenError,
            ValueError,
        ):
            return error_response(
                code="INVALID_AUTHENTICATION",
                message=(
                    "The Firebase authentication token is invalid."
                ),
                status_code=401,
            )

        except Exception:
            # Do not expose Firebase internals or credential
            # verification details to the client.
            return error_response(
                code="AUTHENTICATION_ERROR",
                message=(
                    "Authentication could not be completed."
                ),
                status_code=401,
            )

        if not _is_authorized_admin(
            decoded_token
        ):
            uid = decoded_token.get(
                "uid",
                "unknown",
            )

            # Never log the Firebase token itself.
            # UID is acceptable for server-side audit/debugging.
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
                message=(
                    "You are not authorized to access this resource."
                ),
                status_code=403,
            )

        g.admin_identity = decoded_token

        return view_function(
            *args,
            **kwargs,
        )

    return wrapped_view


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@admin_bp.get("/me")
@require_admin
def get_admin_identity():
    """
    Verify the current Firebase identity and return the safe
    admin identity information.

    This endpoint intentionally does not expose:
    - Firebase tokens
    - service-account credentials
    - private claims
    - Firestore data
    - Cloudinary credentials
    """

    identity = getattr(
        g,
        "admin_identity",
        None,
    )

    if not isinstance(
        identity,
        dict,
    ):
        return error_response(
            code="ADMIN_CONTEXT_MISSING",
            message=(
                "The authenticated admin context is unavailable."
            ),
            status_code=500,
        )

    return success_response(
        data={
            "authenticated": True,
            "admin": _sanitize_admin_identity(
                identity
            ),
        }
    )
