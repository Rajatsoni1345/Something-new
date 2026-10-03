"""
Birthday Quest - Reaction Routes

HTTP API endpoints for the final reaction recording.

The reaction is a special recording stage that occurs after
the final birthday video has completed.

Architecture:

    Browser
        |
        v
    Reaction Route
        |
        v
    Recording Service
        |
        +---- Firestore -> metadata/state
        |
        +---- Cloudinary -> permanent video

IMPORTANT:
- Camera and microphone access remain browser-controlled.
- No Cloudinary credentials are exposed here.
- The reaction recording belongs to exactly one session.
- Recording lifecycle validation remains in recording_service.
- Routes do not directly access Firebase or Cloudinary.
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
    not_found,
    success_response,
)


# ============================================================
# BLUEPRINT
# ============================================================

reactions_bp = Blueprint(
    "reactions",
    __name__,
)


# ============================================================
# CONSTANTS
# ============================================================

REACTION_RECORDING_TYPE = "reaction"


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_active_session(
    session_id: str,
):
    """
    Validate and retrieve an active session.
    """

    validated_session_id = validate_session_id(
        session_id
    )

    session = get_session(
        validated_session_id
    )

    if session is None:
        return None

    if not session.active:
        raise ValueError(
            "The session is inactive."
        )

    return session


def _recording_response_data(
    recording,
) -> dict:
    """
    Return only frontend-safe recording information.

    The permanent Cloudinary URL is exposed only after the
    recording has been verified.
    """

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

    if (
        recording.status == "verified"
        and recording.secure_url
    ):
        data["secure_url"] = recording.secure_url

    return data


def _get_json_or_empty() -> dict:
    """
    Safely read a JSON request body.
    """

    payload = request.get_json(
        silent=True
    )

    if payload is None:
        return {}

    return payload


# ============================================================
# START REACTION
# ============================================================

@reactions_bp.post("/start")
def start_reaction_route():
    """
    Authorize and create the final reaction recording.

    Request:

        {
            "session_id": "..."
        }

    The frontend should start MediaRecorder only after this
    endpoint successfully returns a recording ID.
    """

    try:
        payload = _get_json_or_empty()

        session_id = payload.get(
            "session_id"
        )

        if session_id is None:
            return bad_request(
                message="session_id is required."
            )

        session = _get_active_session(
            session_id
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        validated = validate_start_recording_request(
            {
                "session_id": session_id,
                "recording_type": REACTION_RECORDING_TYPE,
            }
        )

        recording = start_recording(
            session=session,
            recording_type=validated[
                "recording_type"
            ],
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=201,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# STOP REACTION
# ============================================================

@reactions_bp.post("/stop")
def stop_reaction_route():
    """
    Mark the reaction recording as stopping.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_stop_recording_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = get_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        recording = mark_recording_stopping(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# MARK REACTION UPLOAD PENDING
# ============================================================

@reactions_bp.post("/upload-pending")
def mark_reaction_upload_pending_route():
    """
    Move a stopped reaction recording into the upload-pending
    state.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_upload_recording_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = get_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        recording = mark_recording_upload_pending(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
            duration_ms=validated.get(
                "duration_ms"
            ),
            file_size_bytes=validated.get(
                "file_size_bytes"
            ),
            content_type=validated.get(
                "content_type"
            ),
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# UPLOAD REACTION
# ============================================================

@reactions_bp.post("/upload")
def upload_reaction_route():
    """
    Upload the final reaction video.

    Expected multipart/form-data:

        session_id
        recording_id
        duration_ms        optional
        file_size_bytes    optional
        content_type       optional
        file                required
    """

    try:
        session_id = request.form.get(
            "session_id"
        )

        recording_id = request.form.get(
            "recording_id"
        )

        if not session_id:
            return bad_request(
                message="session_id is required."
            )

        if not recording_id:
            return bad_request(
                message="recording_id is required."
            )

        session = _get_active_session(
            session_id
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        validated_id = validate_recording_id_request(
            {
                "session_id": session_id,
                "recording_id": recording_id,
            }
        )

        recording = get_recording(
            session=session,
            recording_id=validated_id[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        duration_raw = request.form.get(
            "duration_ms"
        )

        file_size_raw = request.form.get(
            "file_size_bytes"
        )

        content_type = request.form.get(
            "content_type"
        )

        duration_ms = None

        if duration_raw not in {
            None,
            "",
        }:
            try:
                duration_ms = int(
                    duration_raw
                )
            except (TypeError, ValueError):
                return bad_request(
                    message=(
                        "duration_ms must be a valid integer."
                    )
                )

        file_size_bytes = None

        if file_size_raw not in {
            None,
            "",
        }:
            try:
                file_size_bytes = int(
                    file_size_raw
                )
            except (TypeError, ValueError):
                return bad_request(
                    message=(
                        "file_size_bytes must be a valid integer."
                    )
                )

        video_file = request.files.get(
            "file"
        )

        if video_file is None:
            return bad_request(
                message=(
                    "The reaction recording file is required."
                )
            )

        if not video_file.filename:
            return bad_request(
                message=(
                    "The reaction recording file "
                    "has no filename."
                )
            )

        recording = upload_recording(
            session=session,
            recording_id=validated_id[
                "recording_id"
            ],
            file_object=video_file,
            duration_ms=duration_ms,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# VERIFY REACTION
# ============================================================

@reactions_bp.post("/verify")
def verify_reaction_route():
    """
    Verify the reaction video in Cloudinary.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_recording_id_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = get_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        recording = verify_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# REACTION STATUS
# ============================================================

@reactions_bp.post("/status")
def reaction_status_route():
    """
    Return the current status of a reaction recording.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_recording_id_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = get_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )


# ============================================================
# REACTION FAILURE
# ============================================================

@reactions_bp.post("/failed")
def reaction_failed_route():
    """
    Mark a reaction recording as failed for controlled recovery.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_failed_recording_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = get_recording(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
        )

        if recording is None:
            return not_found(
                message="Reaction recording not found."
            )

        if recording.recording_type != REACTION_RECORDING_TYPE:
            return bad_request(
                message=(
                    "The specified recording is not "
                    "a reaction recording."
                )
            )

        recording = mark_recording_failed(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
            reason=validated["reason"],
        )

        return success_response(
            data={
                "recording": _recording_response_data(
                    recording
                )
            },
            status_code=200,
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
                  )
