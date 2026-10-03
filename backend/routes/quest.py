"""
Birthday Quest - Quest Routes

HTTP API endpoints for reading and progressing quest state.

Routes remain intentionally thin:

HTTP request
    -> schema validation
    -> session lookup
    -> quest service
    -> consistent API response

Business rules remain inside the service layer.
"""

from __future__ import annotations

from flask import Blueprint, request

from schemas.quest import (
    validate_collect_item_request,
    validate_complete_level_request,
    validate_discover_word_request,
    validate_get_quest_state_request,
)

from services.quest_service import (
    collect_item,
    complete_level,
    discover_word,
    get_or_create_quest,
    get_quest,
    unlock_final_reveal,
)

from services.session_service import get_session

from utils.responses import (
    bad_request,
    error_response,
    not_found,
    success_response,
)


# ============================================================
# BLUEPRINT
# ============================================================

quest_bp = Blueprint(
    "quest",
    __name__,
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_json_payload():
    """
    Require a JSON object from the request body.
    """

    if not request.is_json:
        raise ValueError(
            "Request body must be JSON."
        )

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Request body must be a JSON object."
        )

    return payload


def _get_active_session(
    session_id: str,
):
    """
    Load a session and ensure it is still active.

    Returns:
        Session object

    Raises:
        LookupError: session does not exist
        ValueError: session is inactive
    """

    session = get_session(
        session_id
    )

    if session is None:
        raise LookupError(
            "Session not found."
        )

    if not session.active:
        raise ValueError(
            "The session is inactive."
        )

    return session


# ============================================================
# GET QUEST STATE
# ============================================================

@quest_bp.post("/state")
def get_quest_state_route():
    """
    Return the current quest state for a session.

    POST /api/v1/quest/state
    """

    try:
        payload = _get_json_payload()

        validated = validate_get_quest_state_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        quest = get_or_create_quest(
            session
        )

        return success_response(
            data={
                "quest": quest.to_dict(),
            },
            status_code=200,
        )

    except LookupError as exc:
        return not_found(
            message=str(exc)
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except Exception:
        return error_response(
            message="Unable to retrieve quest state.",
            status_code=500,
        )


# ============================================================
# COMPLETE LEVEL
# ============================================================

@quest_bp.post("/levels/complete")
def complete_level_route():
    """
    Complete one validated quest level.

    The submitted answer is passed to the service layer,
    where the authoritative server-side answer is checked.

    POST /api/v1/quest/levels/complete
    """

    try:
        payload = _get_json_payload()

        validated = validate_complete_level_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            return not_found(
                message="Quest not found for this session."
            )

        quest = complete_level(
            session=session,
            quest=quest,
            level=validated["level"],
            answer=validated["answer"],
        )

        return success_response(
            data={
                "quest": quest.to_dict(),
            },
            status_code=200,
        )

    except LookupError as exc:
        return not_found(
            message=str(exc)
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to complete quest level.",
            status_code=500,
        )


# ============================================================
# COLLECT ITEM
# ============================================================

@quest_bp.post("/items/collect")
def collect_item_route():
    """
    Collect one magical quest item.

    POST /api/v1/quest/items/collect
    """

    try:
        payload = _get_json_payload()

        validated = validate_collect_item_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            return not_found(
                message="Quest not found for this session."
            )

        quest = collect_item(
            session=session,
            quest=quest,
            item_id=validated["item_id"],
        )

        return success_response(
            data={
                "quest": quest.to_dict(),
            },
            status_code=200,
        )

    except LookupError as exc:
        return not_found(
            message=str(exc)
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to collect quest item.",
            status_code=500,
        )


# ============================================================
# DISCOVER HIDDEN WORD
# ============================================================

@quest_bp.post("/words/discover")
def discover_word_route():
    """
    Submit a discovered hidden word.

    The actual word is validated by the quest service.

    POST /api/v1/quest/words/discover
    """

    try:
        payload = _get_json_payload()

        validated = validate_discover_word_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            return not_found(
                message="Quest not found for this session."
            )

        quest = discover_word(
            session=session,
            quest=quest,
            word=validated["word"],
        )

        return success_response(
            data={
                "quest": quest.to_dict(),
            },
            status_code=200,
        )

    except LookupError as exc:
        return not_found(
            message=str(exc)
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to discover hidden word.",
            status_code=500,
        )


# ============================================================
# UNLOCK FINAL REVEAL
# ============================================================

@quest_bp.post("/final-reveal/unlock")
def unlock_final_reveal_route():
    """
    Unlock the final reveal after all required quest conditions
    have been satisfied.

    POST /api/v1/quest/final-reveal/unlock
    """

    try:
        payload = _get_json_payload()

        validated = validate_get_quest_state_request(
            payload
        )

        session = _get_active_session(
            validated["session_id"]
        )

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            return not_found(
                message="Quest not found for this session."
            )

        quest = unlock_final_reveal(
            session=session,
            quest=quest,
        )

        return success_response(
            data={
                "quest": quest.to_dict(),
            },
            status_code=200,
        )

    except LookupError as exc:
        return not_found(
            message=str(exc)
        )

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )

    except RuntimeError as exc:
        return error_response(
            message=str(exc),
            status_code=409,
        )

    except Exception:
        return error_response(
            message="Unable to unlock final reveal.",
            status_code=500,
    )
