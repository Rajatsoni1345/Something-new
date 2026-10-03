"""
Birthday Quest - Common Schemas

Reusable validation helpers for API request data.

These helpers validate external input before it reaches the
service layer.
"""

from __future__ import annotations

import re
from typing import Any


SESSION_ID_PATTERN = re.compile(
    r"^[a-f0-9]{8}-"
    r"[a-f0-9]{4}-"
    r"4[a-f0-9]{3}-"
    r"[89ab][a-f0-9]{3}-"
    r"[a-f0-9]{12}$",
    re.IGNORECASE,
)

RECORDING_ID_PATTERN = SESSION_ID_PATTERN

MAX_STRING_LENGTH = 512
MAX_METADATA_KEYS = 32


def require_dict(
    value: Any,
    field_name: str = "request",
) -> dict[str, Any]:
    """
    Require a dictionary value.
    """
    if not isinstance(value, dict):
        raise ValueError(
            f"{field_name} must be a JSON object."
        )

    return value


def require_string(
    value: Any,
    field_name: str,
    *,
    min_length: int = 1,
    max_length: int = MAX_STRING_LENGTH,
) -> str:
    """
    Validate and normalize a required string.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if len(normalized) < min_length:
        raise ValueError(
            f"{field_name} is too short."
        )

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} is too long."
        )

    return normalized


def optional_string(
    value: Any,
    field_name: str,
    *,
    max_length: int = MAX_STRING_LENGTH,
) -> str | None:
    """
    Validate an optional string.

    None is accepted. Empty strings are normalized to None.
    """
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string or null."
        )

    normalized = value.strip()

    if not normalized:
        return None

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} is too long."
        )

    return normalized


def require_boolean(
    value: Any,
    field_name: str,
) -> bool:
    """
    Validate a required boolean.

    Python integers such as 0 and 1 are deliberately rejected.
    """
    if not isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a boolean."
        )

    return value


def require_integer(
    value: Any,
    field_name: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """
    Validate an integer while rejecting booleans.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{field_name} must be an integer."
        )

    if minimum is not None and value < minimum:
        raise ValueError(
            f"{field_name} must be at least {minimum}."
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"{field_name} must be at most {maximum}."
        )

    return value


def optional_integer(
    value: Any,
    field_name: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    """
    Validate an optional integer.
    """
    if value is None:
        return None

    return require_integer(
        value,
        field_name,
        minimum=minimum,
        maximum=maximum,
    )


def require_list(
    value: Any,
    field_name: str,
) -> list[Any]:
    """
    Validate a required JSON array.
    """
    if not isinstance(value, list):
        raise ValueError(
            f"{field_name} must be a JSON array."
        )

    return value


def require_string_list(
    value: Any,
    field_name: str,
    *,
    max_items: int = 32,
    max_item_length: int = MAX_STRING_LENGTH,
) -> list[str]:
    """
    Validate a list containing only non-empty strings.
    """
    values = require_list(value, field_name)

    if len(values) > max_items:
        raise ValueError(
            f"{field_name} cannot contain more than "
            f"{max_items} items."
        )

    normalized: list[str] = []

    for index, item in enumerate(values):
        item_name = f"{field_name}[{index}]"

        normalized_item = require_string(
            item,
            item_name,
            max_length=max_item_length,
        )

        if normalized_item not in normalized:
            normalized.append(normalized_item)

    return normalized


def validate_session_id(
    value: Any,
    field_name: str = "session_id",
) -> str:
    """
    Validate a UUID v4 session identifier.
    """
    session_id = require_string(
        value,
        field_name,
        max_length=64,
    )

    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError(
            f"{field_name} must be a valid UUID v4."
        )

    return session_id


def validate_recording_id(
    value: Any,
    field_name: str = "recording_id",
) -> str:
    """
    Validate a UUID v4 recording identifier.
    """
    recording_id = require_string(
        value,
        field_name,
        max_length=64,
    )

    if not RECORDING_ID_PATTERN.fullmatch(recording_id):
        raise ValueError(
            f"{field_name} must be a valid UUID v4."
        )

    return recording_id


def validate_enum(
    value: Any,
    field_name: str,
    allowed_values: set[str] | frozenset[str],
) -> str:
    """
    Validate that a value belongs to an explicit set of strings.
    """
    normalized = require_string(
        value,
        field_name,
        max_length=128,
    )

    if normalized not in allowed_values:
        allowed = ", ".join(
            sorted(allowed_values)
        )

        raise ValueError(
            f"Invalid {field_name}: {normalized!r}. "
            f"Allowed values: {allowed}."
        )

    return normalized


def validate_metadata(
    value: Any,
    field_name: str = "metadata",
) -> dict[str, Any]:
    """
    Validate a metadata object.

    Metadata is intentionally constrained because arbitrary,
    deeply nested client-controlled data should not be allowed
    into the backend without limits.
    """
    metadata = require_dict(
        value,
        field_name,
    )

    if len(metadata) > MAX_METADATA_KEYS:
        raise ValueError(
            f"{field_name} cannot contain more than "
            f"{MAX_METADATA_KEYS} keys."
        )

    for key in metadata:
        if not isinstance(key, str):
            raise ValueError(
                f"Every key in {field_name} must be a string."
            )

        if not key.strip():
            raise ValueError(
                f"{field_name} cannot contain an empty key."
            )

        if len(key) > 128:
            raise ValueError(
                f"Keys in {field_name} cannot exceed 128 characters."
            )

    return dict(metadata)


def reject_unknown_fields(
    data: dict[str, Any],
    allowed_fields: set[str] | frozenset[str],
) -> None:
    """
    Reject fields that the endpoint does not explicitly support.

    This prevents clients from silently injecting unexpected
    application fields.
    """
    unknown_fields = set(data) - set(allowed_fields)

    if unknown_fields:
        unknown = ", ".join(
            sorted(unknown_fields)
        )

        raise ValueError(
            f"Unknown request field(s): {unknown}."
        )


def require_fields(
    data: dict[str, Any],
    required_fields: set[str] | frozenset[str],
) -> None:
    """
    Ensure all required fields are present.
    """
    missing_fields = [
        field
        for field in sorted(required_fields)
        if field not in data
    ]

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(missing_fields)
            + "."
      )
