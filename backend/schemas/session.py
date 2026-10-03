"""
Birthday Quest - Session Schemas

Request validation for session-related API endpoints.
"""

from __future__ import annotations

from typing import Any

from schemas.common import (
    optional_string,
    reject_unknown_fields,
    require_dict,
)


CREATE_SESSION_FIELDS = frozenset(
    {
        "metadata",
    }
)

RECOVER_SESSION_FIELDS = frozenset(
    {
        "session_id",
    }
)


def validate_create_session_request(
    data: Any,
) -> dict[str, Any]:
    """
    Validate a request for creating a new quest session.

    The client is not allowed to provide:
    - session ID
    - quest state
    - timestamps
    - version
    - active/completion flags

    Those values are generated and controlled by the backend.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        CREATE_SESSION_FIELDS,
    )

    metadata = payload.get("metadata")

    if metadata is not None:
        if not isinstance(metadata, dict):
            raise ValueError(
                "metadata must be a JSON object."
            )

        # Metadata is intentionally limited to simple,
        # non-sensitive client-provided context.
        validated_metadata: dict[str, Any] = {}

        if len(metadata) > 16:
            raise ValueError(
                "metadata cannot contain more than 16 keys."
            )

        for key, value in metadata.items():
            if not isinstance(key, str):
                raise ValueError(
                    "Every metadata key must be a string."
                )

            normalized_key = key.strip()

            if not normalized_key:
                raise ValueError(
                    "Metadata keys cannot be empty."
                )

            if len(normalized_key) > 64:
                raise ValueError(
                    "Metadata keys cannot exceed 64 characters."
                )

            if isinstance(value, bool):
                validated_metadata[normalized_key] = value

            elif isinstance(value, (str, int, float)):
                if isinstance(value, str):
                    value = value.strip()

                    if len(value) > 256:
                        raise ValueError(
                            f"Metadata value for {normalized_key!r} "
                            "is too long."
                        )

                validated_metadata[normalized_key] = value

            else:
                raise ValueError(
                    f"Metadata value for {normalized_key!r} "
                    "must be a string, number, or boolean."
                )

        return {
            "metadata": validated_metadata,
        }

    return {
        "metadata": {},
    }


def validate_recover_session_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request for recovering an existing session.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        RECOVER_SESSION_FIELDS,
    )

    session_id = optional_string(
        payload.get("session_id"),
        "session_id",
        max_length=64,
    )

    if not session_id:
        raise ValueError(
            "session_id is required."
        )

    return {
        "session_id": session_id,
  }
