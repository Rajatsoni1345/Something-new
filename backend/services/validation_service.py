"""
Birthday Quest - Validation Service

Centralized validation rules shared by service and route layers.

This module contains validation that is broader than simple request
shape validation but does not perform database or external-service
operations.
"""

from __future__ import annotations

from typing import Any

from schemas.common import (
    MAX_STRING_LENGTH,
    require_string,
    validate_enum,
    validate_recording_id,
    validate_session_id,
)
from schemas.recording import (
    MAX_RECORDING_DURATION_MS,
    MAX_RECORDING_SIZE_BYTES,
    RECORDING_CONTENT_TYPES,
    RECORDING_TYPES,
)


def validate_session_identifier(
    session_id: Any,
) -> str:
    """
    Validate a session identifier at the service layer.
    """
    return validate_session_id(session_id)


def validate_recording_identifier(
    recording_id: Any,
) -> str:
    """
    Validate a recording identifier at the service layer.
    """
    return validate_recording_id(recording_id)


def validate_recording_type(
    recording_type: Any,
) -> str:
    """
    Validate a supported recording type.
    """
    return validate_enum(
        recording_type,
        "recording_type",
        RECORDING_TYPES,
    )


def validate_recording_content_type(
    content_type: Any,
) -> str:
    """
    Validate a supported browser video content type.
    """
    normalized = require_string(
        content_type,
        "content_type",
        max_length=128,
    ).lower()

    if normalized not in RECORDING_CONTENT_TYPES:
        raise ValueError(
            "Unsupported recording content type."
        )

    return normalized


def validate_recording_size(
    file_size_bytes: Any,
) -> int:
    """
    Validate the maximum accepted recording size.
    """
    if isinstance(file_size_bytes, bool):
        raise ValueError(
            "file_size_bytes must be an integer."
        )

    if not isinstance(file_size_bytes, int):
        raise ValueError(
            "file_size_bytes must be an integer."
        )

    if file_size_bytes <= 0:
        raise ValueError(
            "file_size_bytes must be greater than zero."
        )

    if file_size_bytes > MAX_RECORDING_SIZE_BYTES:
        raise ValueError(
            "The recording exceeds the maximum allowed size."
        )

    return file_size_bytes


def validate_recording_duration(
    duration_ms: Any,
) -> int:
    """
    Validate the maximum accepted recording duration.
    """
    if isinstance(duration_ms, bool):
        raise ValueError(
            "duration_ms must be an integer."
        )

    if not isinstance(duration_ms, int):
        raise ValueError(
            "duration_ms must be an integer."
        )

    if duration_ms < 0:
        raise ValueError(
            "duration_ms cannot be negative."
        )

    if duration_ms > MAX_RECORDING_DURATION_MS:
        raise ValueError(
            "The recording exceeds the maximum allowed duration."
        )

    return duration_ms


def validate_public_identifier(
    value: Any,
    field_name: str,
) -> str:
    """
    Validate an application-generated/public identifier.

    This is deliberately stricter than a generic string because
    identifiers are frequently used in persistence paths.
    """
    normalized = require_string(
        value,
        field_name,
        min_length=1,
        max_length=128,
    )

    if "/" in normalized:
        raise ValueError(
            f"{field_name} cannot contain '/'."
        )

    if "\\" in normalized:
        raise ValueError(
            f"{field_name} cannot contain '\\'."
        )

    return normalized


def validate_level(
    level: Any,
) -> int:
    """
    Validate a quest level.

    Level 0 represents the pre-level quest state.
    Levels 1 through 5 represent the four quest levels plus
    the final level.
    """
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError(
            "level must be an integer."
        )

    if not 0 <= level <= 5:
        raise ValueError(
            "level must be between 0 and 5."
        )

    return level


def validate_answer(
    answer: Any,
) -> str:
    """
    Validate a player's answer before it reaches quest logic.
    """
    return require_string(
        answer,
        "answer",
        min_length=1,
        max_length=MAX_STRING_LENGTH,
    )


def validate_item_id(
    item_id: Any,
) -> str:
    """
    Validate a quest item identifier.
    """
    normalized = require_string(
        item_id,
        "item_id",
        min_length=1,
        max_length=128,
    )

    if "/" in normalized or "\\" in normalized:
        raise ValueError(
            "item_id contains invalid characters."
        )

    return normalized


def validate_hidden_word(
    word: Any,
) -> str:
    """
    Normalize and validate a discovered quest word.

    The backend will later compare the normalized value against
    the configured answer for the relevant level.
    """
    normalized = require_string(
        word,
        "word",
        min_length=1,
        max_length=128,
    )

    return normalized.casefold()
