"""
Birthday Quest - Session Routes

HTTP API endpoints for creating, recovering, and reading
Birthday Quest sessions.

Routes remain intentionally thin:

HTTP request
    -> schema validation
    -> service
    -> consistent API response

Business rules remain inside the service layer.
"""

from __future__ import annotations

from flask import Blueprint, request

from schemas.common import validate_session_id

from schemas.session import (
    validate_create_session_request,
    validate_recover_session_request,
)

from services.session_service import (
    create_session,
    get_session,
    recover_session,
)

from utils.responses import (
    bad_request,
    error_response,
    not_found,
    success_response,
)


# ============================================================
# BLUEPRINT
# ============================================================

sessions_bp = Blueprint(
    "sessions",
    __name__,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_json_payload() -> dict:
    """
    Require a JSON object from the request body.
    """

    if not request.is_json:
        raise ValueError(
            "Request body must be JSON."
        )

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Request body must be a JSON object."
        )

    return payload


# ============================================================
# CREATE SESSION
# ============================================================

@sessions_bp.post("")
def create_session_route():
    """
    Create a new Birthday Quest session.

    POST /api/v1/sessions
    """

    try:
        payload = _get_json_payload()

        validated = validate_create_session_request(
            payload
        )

        session = create_session(
            metadata=validated["metadata"]
        )

        return success_response(
            data={
                "session": session.to_dict(),
            },
            status_code=201,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to create session.",
            status_code=500,
        )


# ============================================================
# RECOVER SESSION
# ============================================================

@sessions_bp.post("/recover")
def recover_session_route():
    """
    Recover an existing active session.

    POST /api/v1/sessions/recover
    """

    try:
        payload = _get_json_payload()

        validated = validate_recover_session_request(
            payload
        )

        session = recover_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message=(
                    "The requested session could not "
                    "be recovered."
                )
            )

        return success_response(
            data={
                "session": session.to_dict(),
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to recover session.",
            status_code=500,
        )


# ============================================================
# GET SESSION
# ============================================================

@sessions_bp.get("/<session_id>")
def get_session_route(
    session_id: str,
):
    """
    Read the current session.

    GET /api/v1/sessions/<session_id>
    """

    try:
        validated_session_id = validate_session_id(
            session_id
        )

        session = get_session(
            validated_session_id
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        return success_response(
            data={
                "session": session.to_dict(),
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except Exception:
        return error_response(
            message="Unable to retrieve session.",
            status_code=500,
    )
