"""
Birthday Quest - Quest Schemas

Request validation for quest-related API endpoints.
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


def validate_get_quest_state_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request for retrieving quest state.
    """
    payload = require_dict(data)

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
        ),
    }


def validate_complete_level_request(
    data: Any,
) -> dict[str, Any]:
    """
    Validate a request attempting to complete a level.

    The answer is treated as user input only. The backend will
    independently determine whether the answer is correct.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        COMPLETE_LEVEL_FIELDS,
    )

    required_fields = {
        "session_id",
        "level",
        "answer",
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

    level = require_integer(
        payload["level"],
        "level",
        minimum=1,
        maximum=5,
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


def validate_collect_item_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request to collect a quest item.

    The service layer will verify whether that item is actually
    available at the current quest state.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        COLLECT_ITEM_FIELDS,
    )

    required_fields = {
        "session_id",
        "item_id",
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

    item_id = require_string(
        payload["item_id"],
        "item_id",
        min_length=1,
        max_length=128,
    )

    return {
        "session_id": session_id,
        "item_id": item_id,
    }


def validate_discover_word_request(
    data: Any,
) -> dict[str, str]:
    """
    Validate a request to register a discovered hidden word.

    The backend will later verify that the word is actually
    associated with the current level and that the required
    progression has been completed.
    """
    payload = require_dict(data)

    reject_unknown_fields(
        payload,
        DISCOVER_WORD_FIELDS,
    )

    required_fields = {
        "session_id",
        "word",
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
