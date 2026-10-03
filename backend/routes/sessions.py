"""
Birthday Quest - Session Routes

HTTP API endpoints for creating, recovering, and reading
Birthday Quest sessions.

Routes remain intentionally thin:

HTTP request
    -> schema validation
    -> service
    -> consistent API response
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
# CREATE SESSION
# ============================================================

@sessions_bp.post("")
def create_session_route():
    """
    Create a new Birthday Quest session.

    POST /api/v1/sessions
    """

    try:
        payload = request.get_json(
            silent=True
        )

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
        payload = request.get_json(
            silent=True
        )

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
