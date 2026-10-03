"""
Birthday Quest - Recording Routes

HTTP API endpoints for the recording lifecycle.

The browser owns:
- camera permission
- microphone permission
- MediaRecorder
- Blob creation

The backend owns:
- session validation
- recording authorization
- recording lifecycle
- Cloudinary upload
- verification
- quest-state transitions
"""

from __future__ import annotations

from flask import Blueprint, request

from services.recording_service import (
    get_recording,
    mark_recording_failed,
    mark_recording_stopping,
    mark_recording_upload_pending,
    start_recording,
    upload_recording,
    verify_recording,
)

from services.session_service import (
    get_session,
)

from utils.responses import (
    error_response,
    success_response,
)


# ============================================================
# BLUEPRINT
# ============================================================

recordings_bp = Blueprint(
    "recordings",
    __name__,
    url_prefix="/api/v1/recordings",
)


# ============================================================
# REQUEST HELPERS
# ============================================================

def _get_json_body() -> dict:
    """
    Safely return a JSON request body.
    """

    if not request.is_json:
        raise ValueError(
            "Request body must be JSON."
        )

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        raise ValueError(
            "Request body must be a JSON object."
        )

    return data


def _require_session_id(
    data: dict,
) -> str:
    """
    Extract the session ID from a request.
    """

    session_id = data.get(
        "session_id"
    )

    if not isinstance(
        session_id,
        str,
    ):
        raise ValueError(
            "session_id is required."
        )

    session_id = session_id.strip()

    if not session_id:
        raise ValueError(
            "session_id is required."
        )

    return session_id


def _get_session_from_request(
    data: dict,
):
    """
    Load and validate the session referenced by the request.
    """

    session_id = _require_session_id(
        data
    )

    session = get_session(
        session_id
    )

    if session is None:
        raise ValueError(
            "Session not found."
        )

    if not session.active:
        raise ValueError(
            "Session is inactive."
        )

    return session


def _require_recording_id(
    data: dict,
) -> str:
    """
    Extract the recording ID from a request.
    """

    recording_id = data.get(
        "recording_id"
    )

    if not isinstance(
        recording_id,
        str,
    ):
        raise ValueError(
            "recording_id is required."
        )

    recording_id = recording_id.strip()

    if not recording_id:
        raise ValueError(
            "recording_id is required."
        )

    return recording_id


def _parse_optional_int(
    value,
    field_name: str,
):
    """
    Parse an optional integer without accepting booleans.
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{field_name} must be an integer."
        )

    if not isinstance(
        value,
        int,
    ):
        raise ValueError(
            f"{field_name} must be an integer."
        )

    return value


# ============================================================
# START RECORDING
# ============================================================

@recordings_bp.post("/start")
def start_recording_route():
    """
    Start an authorized recording.

    JSON:
    {
        "session_id": "...",
        "recording_type": "video_1"
    }
    """

    try:
        data = _get_json_body()

        session = _get_session_from_request(
            data
        )

        recording_type = data.get(
            "recording_type"
        )

        recording = start_recording(
            session=session,
            recording_type=recording_type,
        )

        return success_response(
            data=recording.to_dict(),
            status_code=201,
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to start recording.",
            status_code=500,
        )


# ============================================================
# MARK STOPPING
# ============================================================

@recordings_bp.post("/stop")
def stop_recording_route():
    """
    Mark an active recording as stopping.

    JSON:
    {
        "session_id": "...",
        "recording_id": "..."
    }
    """

    try:
        data = _get_json_body()

        session = _get_session_from_request(
            data
        )

        recording_id = _require_recording_id(
            data
        )

        recording = mark_recording_stopping(
            session=session,
            recording_id=recording_id,
        )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to stop recording.",
            status_code=500,
        )


# ============================================================
# MARK UPLOAD PENDING
# ============================================================

@recordings_bp.post("/upload-pending")
def upload_pending_route():
    """
    Mark a browser-generated recording Blob as ready for
    Cloudinary upload.

    JSON:
    {
        "session_id": "...",
        "recording_id": "...",
        "duration_ms": 12345,
        "file_size_bytes": 123456,
        "content_type": "video/webm"
    }
    """

    try:
        data = _get_json_body()

        session = _get_session_from_request(
            data
        )

        recording_id = _require_recording_id(
            data
        )

        duration_ms = _parse_optional_int(
            data.get("duration_ms"),
            "duration_ms",
        )

        file_size_bytes = _parse_optional_int(
            data.get("file_size_bytes"),
            "file_size_bytes",
        )

        content_type = data.get(
            "content_type"
        )

        if (
            content_type is not None
            and not isinstance(
                content_type,
                str,
            )
        ):
            raise ValueError(
                "content_type must be a string."
            )

        recording = mark_recording_upload_pending(
            session=session,
            recording_id=recording_id,
            duration_ms=duration_ms,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to prepare recording upload.",
            status_code=500,
        )


# ============================================================
# UPLOAD
# ============================================================

@recordings_bp.post("/upload")
def upload_recording_route():
    """
    Upload a recording Blob to Cloudinary.

    Expected multipart/form-data:

        session_id
        recording_id
        duration_ms          optional
        file_size_bytes      optional
        content_type         optional
        file                  required

    The file itself is never written to Render's filesystem.
    """

    try:
        content_type_header = request.content_type

        if content_type_header is None:
            raise ValueError(
                "Content-Type is required."
            )

        if not content_type_header.startswith(
            "multipart/form-data"
        ):
            raise ValueError(
                "Upload request must use multipart/form-data."
            )

        session_id = request.form.get(
            "session_id"
        )

        recording_id = request.form.get(
            "recording_id"
        )

        if (
            not isinstance(
                session_id,
                str,
            )
            or not session_id.strip()
        ):
            raise ValueError(
                "session_id is required."
            )

        if (
            not isinstance(
                recording_id,
                str,
            )
            or not recording_id.strip()
        ):
            raise ValueError(
                "recording_id is required."
            )

        session = get_session(
            session_id.strip()
        )

        if session is None:
            raise ValueError(
                "Session not found."
            )

        if not session.active:
            raise ValueError(
                "Session is inactive."
            )

        file_object = request.files.get(
            "file"
        )

        if file_object is None:
            raise ValueError(
                "Recording file is required."
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
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "duration_ms must be an integer."
                ) from exc

        file_size_bytes = None

        if file_size_raw not in {
            None,
            "",
        }:
            try:
                file_size_bytes = int(
                    file_size_raw
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "file_size_bytes must be an integer."
                ) from exc

        recording = upload_recording(
            session=session,
            recording_id=recording_id.strip(),
            file_object=file_object,
            duration_ms=duration_ms,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to upload recording.",
            status_code=500,
        )


# ============================================================
# VERIFY
# ============================================================

@recordings_bp.post("/verify")
def verify_recording_route():
    """
    Verify that a recording exists in Cloudinary as a video.

    JSON:
    {
        "session_id": "...",
        "recording_id": "..."
    }
    """

    try:
        data = _get_json_body()

        session = _get_session_from_request(
            data
        )

        recording_id = _require_recording_id(
            data
        )

        recording = verify_recording(
            session=session,
            recording_id=recording_id,
        )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to verify recording.",
            status_code=500,
        )


# ============================================================
# FAILURE
# ============================================================

@recordings_bp.post("/fail")
def fail_recording_route():
    """
    Mark a recording as failed.

    JSON:
    {
        "session_id": "...",
        "recording_id": "...",
        "reason": "..."
    }
    """

    try:
        data = _get_json_body()

        session = _get_session_from_request(
            data
        )

        recording_id = _require_recording_id(
            data
        )

        reason = data.get(
            "reason",
            "Recording operation failed.",
        )

        if not isinstance(
            reason,
            str,
        ):
            raise ValueError(
                "reason must be a string."
            )

        recording = mark_recording_failed(
            session=session,
            recording_id=recording_id,
            reason=reason,
        )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to update recording status.",
            status_code=500,
        )


# ============================================================
# GET RECORDING
# ============================================================

@recordings_bp.get("/<recording_id>")
def get_recording_route(
    recording_id: str,
):
    """
    Retrieve recording metadata for the owning session.

    session_id is intentionally required as a query parameter.
    """

    try:
        if not isinstance(
            recording_id,
            str,
        ):
            raise ValueError(
                "recording_id is required."
            )

        recording_id = recording_id.strip()

        if not recording_id:
            raise ValueError(
                "recording_id is required."
            )

        session_id = request.args.get(
            "session_id"
        )

        if (
            not isinstance(
                session_id,
                str,
            )
            or not session_id.strip()
        ):
            raise ValueError(
                "session_id is required."
            )

        session = get_session(
            session_id.strip()
        )

        if session is None:
            raise ValueError(
                "Session not found."
            )

        if not session.active:
            raise ValueError(
                "Session is inactive."
            )

        recording = get_recording(
            session=session,
            recording_id=recording_id,
        )

        if recording is None:
            return error_response(
                message="Recording not found.",
                status_code=404,
            )

        return success_response(
            data=recording.to_dict()
        )

    except ValueError as exc:
        return error_response(
            message=str(exc),
            status_code=400,
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to retrieve recording.",
            status_code=500,
        )
