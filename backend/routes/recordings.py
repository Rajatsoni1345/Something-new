"""
Birthday Quest - Recording Routes

HTTP API endpoints for the recording lifecycle.

Routes remain intentionally thin:

HTTP request
    -> request/schema validation
    -> session lookup
    -> recording service
    -> consistent API response

IMPORTANT:
- Camera and microphone access remain in the browser.
- Actual video files are handled by the recording service.
- Cloudinary credentials are never exposed here.
- Recording ownership is checked through the session.
- Only verified recordings expose their permanent secure URL.
"""

from __future__ import annotations

from flask import Blueprint, request

from schemas.recording import (
    validate_recording_id_request,
    validate_start_recording_request,
    validate_stop_recording_request,
    validate_upload_recording_request,
)

from schemas.common import validate_session_id

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

recordings_bp = Blueprint(
    "recordings",
    __name__,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_active_session(
    session_id: str,
):
    """
    Validate the session ID and retrieve the active session.

    Routes use this helper so every recording endpoint applies
    the same session checks.
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
    Build the frontend-safe representation of a recording.

    Sensitive/internal fields are intentionally not exposed.

    The permanent Cloudinary URL is returned only after the
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
    Read a JSON body safely.

    Recording upload itself uses multipart/form-data, so this
    helper is used only by JSON endpoints.
    """

    payload = request.get_json(
        silent=True
    )

    if payload is None:
        return {}

    return payload


# ============================================================
# START RECORDING
# ============================================================

@recordings_bp.post("/start")
def start_recording_route():
    """
    Start a new server-authorized recording.

    Request JSON:

        {
            "session_id": "...",
            "recording_type": "video_1"
        }

    The browser should begin MediaRecorder only after receiving
    a successful response.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_start_recording_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
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
# STOP RECORDING
# ============================================================

@recordings_bp.post("/stop")
def stop_recording_route():
    """
    Mark an active recording as stopping.

    The browser should call this when MediaRecorder.stop()
    is about to happen.
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
# UPLOAD PENDING
# ============================================================

@recordings_bp.post("/upload-pending")
def mark_upload_pending_route():
    """
    Mark a stopped recording as ready for Cloudinary upload.

    This endpoint receives JSON metadata only.

    The actual video Blob is uploaded through /upload.
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
# ACTUAL VIDEO UPLOAD
# ============================================================

@recordings_bp.post("/upload")
def upload_recording_route():
    """
    Upload the browser-generated video Blob to Cloudinary.

    Expected multipart/form-data:

        session_id
        recording_id
        duration_ms        optional
        file_size_bytes    optional
        content_type       optional
        file                required

    The field name for the actual video is:

        file
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

        # ----------------------------------------------------
        # Validate recording ID.
        # ----------------------------------------------------

        validated_id = validate_recording_id_request(
            {
                "session_id": session_id,
                "recording_id": recording_id,
            }
        )

        # ----------------------------------------------------
        # Validate optional metadata.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Actual video file.
        # ----------------------------------------------------

        video_file = request.files.get(
            "file"
        )

        if video_file is None:
            return bad_request(
                message=(
                    "The recording file is required."
                )
            )

        if not video_file.filename:
            return bad_request(
                message=(
                    "The recording file has no filename."
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
# VERIFY RECORDING
# ============================================================

@recordings_bp.post("/verify")
def verify_recording_route():
    """
    Verify that the recording exists as a video in Cloudinary.

    This endpoint should be called after upload succeeds.
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
# GET RECORDING STATUS
# ============================================================

@recordings_bp.post("/status")
def get_recording_status_route():
    """
    Return the current status of a recording.

    POST is used instead of a public GET path so the session ID
    remains inside the request body rather than being placed in
    a URL.
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
                message="Recording not found."
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
# MARK FAILED
# ============================================================

@recordings_bp.post("/failed")
def mark_recording_failed_route():
    """
    Mark a recording as failed.

    This is intended for controlled recovery/error handling.
    The frontend cannot arbitrarily change a verified recording
    back to failed.
    """

    try:
        payload = _get_json_or_empty()

        validated = validate_recording_id_request(
            payload
        )

        reason = payload.get(
            "reason",
            "Recording operation failed.",
        )

        if not isinstance(
            reason,
            str,
        ):
            return bad_request(
                message="reason must be a string."
            )

        if len(reason.strip()) > 512:
            return bad_request(
                message="reason is too long."
            )

        session = _get_active_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        recording = mark_recording_failed(
            session=session,
            recording_id=validated[
                "recording_id"
            ],
            reason=reason,
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
