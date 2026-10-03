"""
Birthday Quest - Audit Service

Centralized audit-event persistence.

Audit events are stored in Firestore and are intended for:
- recording lifecycle diagnostics
- quest progression diagnostics
- session lifecycle tracking
- security/recovery investigation
- production troubleshooting

IMPORTANT:
- Secrets are never stored.
- Raw video files are never stored here.
- Cloudinary API secrets are never stored.
- Audit records contain identifiers and safe metadata only.
- Audit writes are best-effort by default so a diagnostic failure
  does not unnecessarily break the primary user flow.
"""

from __future__ import annotations

from typing import Any

from services.firebase_service import (
    get_collection,
    get_document,
)

from utils.ids import generate_uuid
from utils.logging import (
    get_logger,
    log_error,
)
from utils.timestamps import utc_now_iso


logger = get_logger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

AUDIT_COLLECTION = "audit_events"

MAX_EVENT_TYPE_LENGTH = 128
MAX_SESSION_ID_LENGTH = 64
MAX_RECORDING_ID_LENGTH = 64
MAX_REQUEST_ID_LENGTH = 128
MAX_METADATA_KEYS = 32
MAX_METADATA_STRING_LENGTH = 512


# ============================================================
# SAFE VALUE VALIDATION
# ============================================================

def _validate_optional_identifier(
    value: Any,
    field_name: str,
    max_length: int,
) -> str | None:
    """
    Validate an optional identifier used in an audit record.
    """

    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{field_name} must be a string or None."
        )

    normalized = value.strip()

    if not normalized:
        return None

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} is too long."
        )

    if "/" in normalized:
        raise ValueError(
            f"{field_name} cannot contain '/'."
        )

    return normalized


def _validate_event_type(
    event_type: Any,
) -> str:
    """
    Validate the audit event type.
    """

    if not isinstance(
        event_type,
        str,
    ):
        raise TypeError(
            "event_type must be a string."
        )

    normalized = event_type.strip()

    if not normalized:
        raise ValueError(
            "event_type cannot be empty."
        )

    if len(normalized) > MAX_EVENT_TYPE_LENGTH:
        raise ValueError(
            "event_type is too long."
        )

    return normalized


def _sanitize_metadata(
    metadata: Any,
) -> dict[str, Any]:
    """
    Validate and sanitize audit metadata.

    Only JSON-compatible primitive values and shallow lists/dicts
    are accepted.

    This intentionally rejects arbitrary Python objects.
    """

    if metadata is None:
        return {}

    if not isinstance(
        metadata,
        dict,
    ):
        raise TypeError(
            "metadata must be a dictionary or None."
        )

    if len(metadata) > MAX_METADATA_KEYS:
        raise ValueError(
            "metadata contains too many keys."
        )

    sanitized: dict[str, Any] = {}

    for key, value in metadata.items():
        if not isinstance(
            key,
            str,
        ):
            raise ValueError(
                "Audit metadata keys must be strings."
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "Audit metadata keys cannot be empty."
            )

        if len(normalized_key) > 128:
            raise ValueError(
                "Audit metadata key is too long."
            )

        sanitized[
            normalized_key
        ] = _sanitize_metadata_value(
            value
        )

    return sanitized


def _sanitize_metadata_value(
    value: Any,
) -> Any:
    """
    Recursively sanitize supported metadata values.

    Supported values:
    - None
    - bool
    - int
    - float
    - short strings
    - shallow lists
    - shallow dictionaries
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        float,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        if len(value) > MAX_METADATA_STRING_LENGTH:
            raise ValueError(
                "Audit metadata string value is too long."
            )
        return value

    if isinstance(
        value,
        list,
    ):
        if len(value) > 32:
            raise ValueError(
                "Audit metadata list is too large."
            )

        return [
            _sanitize_metadata_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        if len(value) > 32:
            raise ValueError(
                "Audit metadata object is too large."
            )

        sanitized_object: dict[str, Any] = {}

        for key, nested_value in value.items():
            if not isinstance(
                key,
                str,
            ):
                raise ValueError(
                    "Audit metadata object keys must be strings."
                )

            normalized_key = key.strip()

            if not normalized_key:
                raise ValueError(
                    "Audit metadata object keys cannot be empty."
                )

            if len(normalized_key) > 128:
                raise ValueError(
                    "Audit metadata object key is too long."
                )

            sanitized_object[
                normalized_key
            ] = _sanitize_metadata_value(
                nested_value
            )

        return sanitized_object

    raise ValueError(
        "Audit metadata contains an unsupported value type."
    )


# ============================================================
# AUDIT EVENT CREATION
# ============================================================

def create_audit_event(
    *,
    event_type: str,
    session_id: str | None = None,
    recording_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Create a single audit event.

    Returns:
        The generated audit event ID.

    The function performs strict validation before writing.
    """

    event_type = _validate_event_type(
        event_type
    )

    session_id = _validate_optional_identifier(
        session_id,
        "session_id",
        MAX_SESSION_ID_LENGTH,
    )

    recording_id = _validate_optional_identifier(
        recording_id,
        "recording_id",
        MAX_RECORDING_ID_LENGTH,
    )

    request_id = _validate_optional_identifier(
        request_id,
        "request_id",
        MAX_REQUEST_ID_LENGTH,
    )

    safe_metadata = _sanitize_metadata(
        metadata
    )

    audit_event_id = generate_uuid()

    now = utc_now_iso()

    event_data = {
        "audit_event_id": audit_event_id,
        "event_type": event_type,
        "session_id": session_id,
        "recording_id": recording_id,
        "request_id": request_id,
        "metadata": safe_metadata,
        "created_at": now,
    }

    document = get_document(
        AUDIT_COLLECTION,
        audit_event_id,
    )

    document.create(
        event_data
    )

    return audit_event_id


# ============================================================
# BEST-EFFORT AUDIT WRITER
# ============================================================

def record_audit_event(
    *,
    event_type: str,
    session_id: str | None = None,
    recording_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """
    Write an audit event without allowing an audit failure to
    break the primary application operation.

    Returns:
        Audit event ID when successful, otherwise None.
    """

    try:
        return create_audit_event(
            event_type=event_type,
            session_id=session_id,
            recording_id=recording_id,
            request_id=request_id,
            metadata=metadata,
        )

    except Exception as exc:
        log_error(
            logger,
            "audit_event_write_failed",
            event_type=event_type,
            session_id=session_id,
            recording_id=recording_id,
            request_id=request_id,
            error=str(exc),
        )

        return None


# ============================================================
# COMMON AUDIT EVENTS
# ============================================================

def audit_session_created(
    *,
    session_id: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record session creation.
    """

    return record_audit_event(
        event_type="session_created",
        session_id=session_id,
        request_id=request_id,
    )


def audit_session_recovered(
    *,
    session_id: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record session recovery.
    """

    return record_audit_event(
        event_type="session_recovered",
        session_id=session_id,
        request_id=request_id,
    )


def audit_session_completed(
    *,
    session_id: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record session completion.
    """

    return record_audit_event(
        event_type="session_completed",
        session_id=session_id,
        request_id=request_id,
    )


def audit_quest_transition(
    *,
    session_id: str,
    previous_state: str,
    next_state: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record a quest state transition.
    """

    return record_audit_event(
        event_type="quest_state_transition",
        session_id=session_id,
        request_id=request_id,
        metadata={
            "previous_state": previous_state,
            "next_state": next_state,
        },
    )


def audit_recording_started(
    *,
    session_id: str,
    recording_id: str,
    recording_type: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record recording creation/start.
    """

    return record_audit_event(
        event_type="recording_started",
        session_id=session_id,
        recording_id=recording_id,
        request_id=request_id,
        metadata={
            "recording_type": recording_type,
        },
    )


def audit_recording_uploaded(
    *,
    session_id: str,
    recording_id: str,
    recording_type: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record successful permanent upload.

    Cloudinary URLs are intentionally not stored in audit metadata.
    """

    return record_audit_event(
        event_type="recording_uploaded",
        session_id=session_id,
        recording_id=recording_id,
        request_id=request_id,
        metadata={
            "recording_type": recording_type,
        },
    )


def audit_recording_verified(
    *,
    session_id: str,
    recording_id: str,
    recording_type: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record successful Cloudinary verification.
    """

    return record_audit_event(
        event_type="recording_verified",
        session_id=session_id,
        recording_id=recording_id,
        request_id=request_id,
        metadata={
            "recording_type": recording_type,
        },
    )


def audit_recording_failed(
    *,
    session_id: str,
    recording_id: str,
    recording_type: str,
    request_id: str | None = None,
) -> str | None:
    """
    Record a recording failure.

    Detailed failure messages are deliberately not copied into
    audit metadata because they may contain implementation
    details or third-party service information.
    """

    return record_audit_event(
        event_type="recording_failed",
        session_id=session_id,
        recording_id=recording_id,
        request_id=request_id,
        metadata={
            "recording_type": recording_type,
        },
  )
