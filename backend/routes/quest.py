"""
Birthday Quest - Quest Routes

HTTP API endpoints for reading and progressing quest state.

Routes remain intentionally thin:

HTTP request
    -> schema validation
    -> session lookup
    -> quest service
    -> consistent API response
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
# GET QUEST STATE
# ============================================================

@quest_bp.post("/state")
def get_quest_state_route():
    """
    Return the current quest state for a session.

    POST /api/v1/quest/state
    """

    try:
        payload = request.get_json(
            silent=True
        )

        validated = validate_get_quest_state_request(
            payload
        )

        session = get_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        if not session.active:
            return bad_request(
                message="The session is inactive."
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

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
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
        payload = request.get_json(
            silent=True
        )

        validated = validate_complete_level_request(
            payload
        )

        session = get_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        if not session.active:
            return bad_request(
                message="The session is inactive."
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

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
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
        payload = request.get_json(
            silent=True
        )

        validated = validate_collect_item_request(
            payload
        )

        session = get_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        if not session.active:
            return bad_request(
                message="The session is inactive."
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

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
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
        payload = request.get_json(
            silent=True
        )

        validated = validate_discover_word_request(
            payload
        )

        session = get_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        if not session.active:
            return bad_request(
                message="The session is inactive."
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

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
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
        payload = request.get_json(
            silent=True
        )

        validated = validate_get_quest_state_request(
            payload
        )

        session = get_session(
            validated["session_id"]
        )

        if session is None:
            return not_found(
                message="Session not found."
            )

        if not session.active:
            return bad_request(
                message="The session is inactive."
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

    except (ValueError, TypeError) as exc:
        return bad_request(
            message=str(exc)
        )
