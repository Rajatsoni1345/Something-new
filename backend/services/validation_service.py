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


# ============================================================
# QUEST CONSTANTS
# ============================================================

MIN_NORMAL_LEVEL = 1
MAX_NORMAL_LEVEL = 4


# ============================================================
# SESSION / RECORDING IDENTIFIERS
# ============================================================

def validate_session_identifier(
    session_id: Any,
) -> str:
    """
    Validate and normalize a session identifier.
    """

    return validate_session_id(
        session_id
    )


def validate_recording_identifier(
    recording_id: Any,
) -> str:
    """
    Validate and normalize a recording identifier.
    """

    return validate_recording_id(
        recording_id
    )


# ============================================================
# RECORDING VALIDATION
# ============================================================

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
    Validate a supported recording MIME type.
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
    Validate the declared recording size.
    """

    if isinstance(
        file_size_bytes,
        bool,
    ):
        raise ValueError(
            "file_size_bytes must be an integer."
        )

    if not isinstance(
        file_size_bytes,
        int,
    ):
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
    Validate the declared recording duration.
    """

    if isinstance(
        duration_ms,
        bool,
    ):
        raise ValueError(
            "duration_ms must be an integer."
        )

    if not isinstance(
        duration_ms,
        int,
    ):
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


# ============================================================
# PUBLIC IDENTIFIERS
# ============================================================

def validate_public_identifier(
    value: Any,
    field_name: str,
) -> str:
    """
    Validate an external/public identifier.

    Used for identifiers that must never contain path
    separators.
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


# ============================================================
# QUEST LEVEL VALIDATION
# ============================================================

def validate_level(
    level: Any,
) -> int:
    """
    Validate a normal Birthday Quest level.

    Normal quest levels are strictly 1 through 4.

    Level 5 is reserved for the final reveal and is represented
    by the quest state machine rather than a normal level input.
    """

    if isinstance(
        level,
        bool,
    ) or not isinstance(
        level,
        int,
    ):
        raise ValueError(
            "level must be an integer."
        )

    if not (
        MIN_NORMAL_LEVEL
        <= level
        <= MAX_NORMAL_LEVEL
    ):
        raise ValueError(
            "level must be between "
            f"{MIN_NORMAL_LEVEL} and "
            f"{MAX_NORMAL_LEVEL}."
        )

    return level


# ============================================================
# ANSWER VALIDATION
# ============================================================

def validate_answer(
    answer: Any,
) -> str:
    """
    Validate a quest answer.
    """

    return require_string(
        answer,
        "answer",
        min_length=1,
        max_length=MAX_STRING_LENGTH,
    )


# ============================================================
# ITEM VALIDATION
# ============================================================

def validate_item_id(
    item_id: Any,
) -> str:
    """
    Validate a collectible/item identifier.
    """

    normalized = require_string(
        item_id,
        "item_id",
        min_length=1,
        max_length=128,
    )

    if (
        "/" in normalized
        or "\\" in normalized
    ):
        raise ValueError(
            "item_id contains invalid characters."
        )

    return normalized


# ============================================================
# HIDDEN WORD VALIDATION
# ============================================================

def validate_hidden_word(
    word: Any,
) -> str:
    """
    Normalize a discovered hidden word.

    Case differences should not create duplicate words.
    """

    normalized = require_string(
        word,
        "word",
        min_length=1,
        max_length=128,
    )

    return normalized.casefold()
