"""
Birthday Quest - Reaction Routes

HTTP API endpoints for the final reaction recording.
"""

from __future__ import annotations

from flask import Blueprint, request

from schemas.common import validate_session_id

from schemas.recording import (
    validate_failed_recording_request,
    validate_recording_id_request,
    validate_start_recording_request,
    validate_stop_recording_request,
    validate_upload_recording_request,
)

from services.recording_service import (
    get_recording,
    mark_recording_failed,
    mark_recording_stopping,
    mark_recording_upload_pending,
    start_recording,
    upload_recording,
    verify_recording,
)

from services.session_service import get_session

from utils.responses import (
    bad_request,
    error_response,
    not_found,
    success_response,
)


reactions_bp = Blueprint("reactions", __name__)


REACTION_RECORDING_TYPE = "reaction"


# ============================================================
# HELPERS
# ============================================================

def _get_active_session(session_id: str):
    validated_session_id = validate_session_id(session_id)

    session = get_session(validated_session_id)

    if session is None:
        return None

    if not session.active:
        raise ValueError("The session is inactive.")

    return session


def _recording_response_data(recording) -> dict:
    data = {
        "recording_id": recording.recording_id,
        "session_id": recording.session_id,
        "recording_type": recording.recording_type,
        "status": recording.status,
        "created_at": recording.created_at,
        "updated_at": recording.updated_at,
        "duration_ms": recording.duration_ms,
        "file_size_bytes": recording.file_size_bytes,
        "content_type": recording.content_type,
        "completed_at": recording.completed_at,
        "attempt": recording.attempt,
        "version": recording.version,
    }

    if recording.status == "verified" and recording.secure_url:
        data["secure_url"] = recording.secure_url

    return data


def _get_json_payload() -> dict:
    if not request.is_json:
        raise ValueError("Request body must be JSON.")

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    return payload


def _get_reaction_recording(session, recording_id: str):
    recording = get_recording(session=session, recording_id=recording_id)

    if recording is None:
        return None

    if recording.recording_type != REACTION_RECORDING_TYPE:
        raise ValueError(
            "The specified recording is not a reaction recording."
        )

    return recording


# ============================================================
# START REACTION
# ============================================================

@reactions_bp.post("/start")
def start_reaction_route():
    """
    POST /api/v1/reactions/start
    """

    try:
        payload = _get_json_payload()

        session_id = payload.get("session_id")

        if session_id is None:
            raise ValueError("session_id is required.")

        session = _get_active_session(session_id)

        if session is None:
            return not_found(message="Session not found.")

        validated = validate_start_recording_request(
            {
                "session_id": session_id,
                "recording_type": REACTION_RECORDING_TYPE,
            }
        )

        recording = start_recording(
            session_id=validated["session_id"],
            recording_type=validated["recording_type"],
        )

        return success_response(
            data={"recording": _recording_response_data(recording)},
            status_code=201,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to start reaction recording.",
            status_code=500,
        )


# ============================================================
# STOP REACTION
# ============================================================

@reactions_bp.post("/stop")
def stop_reaction_route():
    """
    POST /api/v1/reactions/stop
    """

    try:
        payload = _get_json_payload()

        validated = validate_stop_recording_request(payload)

        session = _get_active_session(validated["session_id"])

        if session is None:
            return not_found(message="Session not found.")

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        recording = mark_recording_stopping(
            session=session,
            recording_id=validated["recording_id"],
        )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to stop reaction recording.",
            status_code=500,
        )


# ============================================================
# MARK REACTION UPLOAD PENDING
# ============================================================

@reactions_bp.post("/upload-pending")
def mark_reaction_upload_pending_route():
    """
    POST /api/v1/reactions/upload-pending
    """

    try:
        payload = _get_json_payload()

        validated = validate_upload_recording_request(payload)

        session = _get_active_session(validated["session_id"])

        if session is None:
            return not_found(message="Session not found.")

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        recording = mark_recording_upload_pending(
            session=session,
            recording_id=validated["recording_id"],
            duration_ms=validated.get("duration_ms"),
            file_size_bytes=validated.get("file_size_bytes"),
            content_type=validated.get("content_type"),
        )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to prepare reaction upload.",
            status_code=500,
        )


# ============================================================
# UPLOAD REACTION
# ============================================================

@reactions_bp.post("/upload")
def upload_reaction_route():
    """
    POST /api/v1/reactions/upload  (multipart/form-data)
    """

    try:
        if not request.content_type:
            raise ValueError("Content-Type is required.")

        if not request.content_type.startswith("multipart/form-data"):
            raise ValueError(
                "Upload request must use multipart/form-data."
            )

        session_id = request.form.get("session_id")
        recording_id = request.form.get("recording_id")

        if not session_id:
            raise ValueError("session_id is required.")

        if not recording_id:
            raise ValueError("recording_id is required.")

        session = _get_active_session(session_id)

        if session is None:
            return not_found(message="Session not found.")

        validated_id = validate_recording_id_request(
            {
                "session_id": session_id,
                "recording_id": recording_id,
            }
        )

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated_id["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        duration_raw = request.form.get("duration_ms")
        file_size_raw = request.form.get("file_size_bytes")
        content_type = request.form.get("content_type")

        duration_ms = None

        if duration_raw not in {None, ""}:
            try:
                duration_ms = int(duration_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "duration_ms must be a valid integer."
                ) from exc

        file_size_bytes = None

        if file_size_raw not in {None, ""}:
            try:
                file_size_bytes = int(file_size_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "file_size_bytes must be a valid integer."
                ) from exc

        video_file = request.files.get("file")

        if video_file is None:
            raise ValueError(
                "The reaction recording file is required."
            )

        if not video_file.filename:
            raise ValueError(
                "The reaction recording file has no filename."
            )

        recording = upload_recording(
            session=session,
            recording_id=validated_id["recording_id"],
            file_object=video_file,
            duration_ms=duration_ms,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to upload reaction recording.",
            status_code=500,
        )


# ============================================================
# VERIFY REACTION
# ============================================================

@reactions_bp.post("/verify")
def verify_reaction_route():
    """
    POST /api/v1/reactions/verify
    """

    try:
        payload = _get_json_payload()

        validated = validate_recording_id_request(payload)

        session = _get_active_session(validated["session_id"])

        if session is None:
            return not_found(message="Session not found.")

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        recording = verify_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to verify reaction recording.",
            status_code=500,
        )


# ============================================================
# STATUS
# ============================================================

@reactions_bp.post("/status")
def reaction_status_route():
    """
    POST /api/v1/reactions/status
    """

    try:
        payload = _get_json_payload()

        validated = validate_recording_id_request(payload)

        session = _get_active_session(validated["session_id"])

        if session is None:
            return not_found(message="Session not found.")

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except Exception:
        return error_response(
            message="Unable to retrieve reaction status.",
            status_code=500,
        )


# ============================================================
# FAILURE
# ============================================================

@reactions_bp.post("/failed")
def reaction_failed_route():
    """
    POST /api/v1/reactions/failed
    """

    try:
        payload = _get_json_payload()

        validated = validate_failed_recording_request(payload)

        session = _get_active_session(validated["session_id"])

        if session is None:
            return not_found(message="Session not found.")

        recording = _get_reaction_recording(
            session=session,
            recording_id=validated["recording_id"],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        recording = mark_recording_failed(
            session=session,
            recording_id=validated["recording_id"],
            reason=validated["reason"],
        )

        return success_response(
            data={"recording": _recording_response_data(recording)}
        )

    except (ValueError, TypeError) as exc:
        return bad_request(message=str(exc))

    except RuntimeError as exc:
        return error_response(message=str(exc), status_code=409)

    except Exception:
        return error_response(
            message="Unable to update reaction recording.",
            status_code=500,
        )
