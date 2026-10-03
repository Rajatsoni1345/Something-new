"""
Birthday Quest - Quest Schemas

Request validation for quest-related API endpoints.

IMPORTANT:
- Normal quest levels are strictly 1 through 4.
- Level 5 is not accepted by the normal level-completion endpoint.
- Final Reveal has its own dedicated endpoint.
- External input is validated before reaching the service layer.
"""

from __future__ import annotations

from typing import Any

from schemas.common import (
    reject_unknown_fields,
    require_dict,
    require_integer,
    require_string,
    validate_session_id,
)


# ============================================================
# QUEST CONSTANTS
# ============================================================

MIN_NORMAL_LEVEL = 1
MAX_NORMAL_LEVEL = 4


# ============================================================
# ALLOWED REQUEST FIELDS
# ============================================================

GET_QUEST_STATE_FIELDS = frozenset(
    {
        "session_id",
    }
)

COMPLETE_LEVEL_FIELDS = frozenset(
    {
        "session_id",
        "level",
        "answer",
    }
)

COLLECT_ITEM_FIELDS = frozenset(
    {
        "session_id",
        "item_id",
    }
)

DISCOVER_WORD_FIELDS = frozenset(
    {
        "session_id",
        "word",
    }
)


# ============================================================
# GET QUEST STATE
# ============================================================

def validate_get_quest_state_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request that asks for the current quest state.
    """

    payload = require_dict(
        data
    )

    reject_unknown_fields(
        payload,
        GET_QUEST_STATE_FIELDS,
    )

    if "session_id" not in payload:
        raise ValueError(
            "session_id is required."
        )

    return {
        "session_id": validate_session_id(
            payload["session_id"]
        )
    }


# ============================================================
# COMPLETE LEVEL
# ============================================================

def validate_complete_level_request(
    data: Any,
) -> dict[str, Any]:
    """
    Validate a normal quest-level completion request.

    Only Levels 1 through 4 are accepted here.

    Level 5 is intentionally excluded because the final reveal
    has a separate server-side progression flow.
    """

    payload = require_dict(
        data
    )

    reject_unknown_fields(
        payload,
        COMPLETE_LEVEL_FIELDS,
    )

    required_fields = {
        "session_id",
        "level",
        "answer",
    }

    missing_fields = (
        required_fields
        - set(payload)
    )

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(
                sorted(missing_fields)
            )
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    level = require_integer(
        payload["level"],
        "level",
        minimum=MIN_NORMAL_LEVEL,
        maximum=MAX_NORMAL_LEVEL,
    )

    answer = require_string(
        payload["answer"],
        "answer",
        min_length=1,
        max_length=512,
    )

    return {
        "session_id": session_id,
        "level": level,
        "answer": answer,
    }


# ============================================================
# COLLECT ITEM
# ============================================================

def validate_collect_item_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a magical collectible submission.
    """

    payload = require_dict(
        data
    )

    reject_unknown_fields(
        payload,
        COLLECT_ITEM_FIELDS,
    )

    required_fields = {
        "session_id",
        "item_id",
    }

    missing_fields = (
        required_fields
        - set(payload)
    )

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(
                sorted(missing_fields)
            )
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    item_id = require_string(
        payload["item_id"],
        "item_id",
        min_length=1,
        max_length=128,
    )

    if "/" in item_id or "\\" in item_id:
        raise ValueError(
            "item_id contains invalid characters."
        )

    return {
        "session_id": session_id,
        "item_id": item_id,
    }


# ============================================================
# DISCOVER HIDDEN WORD
# ============================================================

def validate_discover_word_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a hidden-word discovery submission.

    The actual authoritative word is checked later by the
    quest service.
    """

    payload = require_dict(
        data
    )

    reject_unknown_fields(
        payload,
        DISCOVER_WORD_FIELDS,
    )

    required_fields = {
        "session_id",
        "word",
    }

    missing_fields = (
        required_fields
        - set(payload)
    )

    if missing_fields:
        raise ValueError(
            "Missing required field(s): "
            + ", ".join(
                sorted(missing_fields)
            )
            + "."
        )

    session_id = validate_session_id(
        payload["session_id"]
    )

    word = require_string(
        payload["word"],
        "word",
        min_length=1,
        max_length=128,
    )

    return {
        "session_id": session_id,
        "word": word,
    }
