"""
Birthday Quest - Recording Schemas

Request validation for recording-related API endpoints.

Actual file handling and Cloudinary operations belong to the
recording service layer.
"""

from __future__ import annotations

from typing import Any

from schemas.common import (
    optional_integer,
    optional_string,
    reject_unknown_fields,
    require_dict,
    require_integer,
    require_string,
    validate_enum,
    validate_recording_id,
    validate_session_id,
)


RECORDING_TYPES = frozenset(
    {
        "video_1",
        "video_2",
        "reaction",
    }
)

RECORDING_CONTENT_TYPES = frozenset(
    {
        "video/webm",
        "video/mp4",
        "video/quicktime",
        "video/x-matroska",
    }
)

MAX_RECORDING_SIZE_BYTES = 250 * 1024 * 1024
MAX_RECORDING_DURATION_MS = 15 * 60 * 1000


START_RECORDING_FIELDS = frozenset(
    {
        "session_id",
        "recording_type",
    }
)

STOP_RECORDING_FIELDS = frozenset(
    {
        "session_id",
        "recording_id",
    }
)

UPLOAD_RECORDING_FIELDS = frozenset(
    {
        "session_id",
        "recording_id",
        "duration_ms",
        "file_size_bytes",
        "content_type",
    }
)


def validate_start_recording_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request to start a recording lifecycle.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        START_RECORDING_FIELDS,
    )

    required_fields = {
        "session_id",
        "recording_type",
    }

    missing_fields = required_fields - set(payload)

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(sorted(missing_fields))
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    recording_type = validate_enum(
        payload["recording_type"],
        "recording_type",
        RECORDING_TYPES,
    )

    return {
        "session_id": session_id,
        "recording_type": recording_type,
    }


def validate_stop_recording_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request to stop an existing recording lifecycle.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        STOP_RECORDING_FIELDS,
    )

    required_fields = {
        "session_id",
        "recording_id",
    }

    missing_fields = required_fields - set(payload)

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(sorted(missing_fields))
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    recording_id = validate_recording_id(
        payload["recording_id"]
    )

    return {
        "session_id": session_id,
        "recording_id": recording_id,
    }


def validate_upload_recording_request(
    data: Any,
) -> dict[str, Any]:
    """
    Validate recording metadata accompanying a video upload.

    The actual multipart file must be validated separately from
    this JSON metadata.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        UPLOAD_RECORDING_FIELDS,
    )

    required_fields = {
        "session_id",
        "recording_id",
    }

    missing_fields = required_fields - set(payload)

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(sorted(missing_fields))
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    recording_id = validate_recording_id(
        payload["recording_id"]
    )

    duration_ms = optional_integer(
        payload.get("duration_ms"),
        "duration_ms",
        minimum=0,
        maximum=MAX_RECORDING_DURATION_MS,
    )

    file_size_bytes = optional_integer(
        payload.get("file_size_bytes"),
        "file_size_bytes",
        minimum=1,
        maximum=MAX_RECORDING_SIZE_BYTES,
    )

    content_type = optional_string(
        payload.get("content_type"),
        "content_type",
        max_length=128,
    )

    if content_type is not None:
        content_type = content_type.lower()

        if content_type not in RECORDING_CONTENT_TYPES:
            raise ValueError(
                "Unsupported recording content type."
            )

    return {
        "session_id": session_id,
        "recording_id": recording_id,
        "duration_ms": duration_ms,
        "file_size_bytes": file_size_bytes,
        "content_type": content_type,
    }


def validate_recording_id_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a generic request containing a session and recording ID.

    Useful for future recording-status/recovery endpoints.
    """
    payload = require_dict(data)

    allowed_fields = frozenset(
        {
            "session_id",
            "recording_id",
        }
    )

    reject_unknown_fields(
        payload,
        allowed_fields,
    )

    required_fields = {
        "session_id",
        "recording_id",
    }

    missing_fields = required_fields - set(payload)

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(sorted(missing_fields))
            + "."
        )

    return {
        "session_id": validate_session_id(
            payload["session_id"]
        ),
        "recording_id": validate_recording_id(
            payload["recording_id"]
        ),
  }
