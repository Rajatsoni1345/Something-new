"""
Birthday Quest - Quest Service

Centralized quest state machine and progression logic.

IMPORTANT:
- The client cannot directly choose the next quest state.
- Every transition must be explicitly allowed.
- Level progression is validated server-side.
- Hidden words are validated server-side.
- Quest data is persisted through the Firebase service.
"""

from __future__ import annotations

from typing import Any

from models.quest import Quest
from models.session import Session

from services.firebase_service import (
    get_document_data,
    set_document_data,
    update_document_data,
)

from services.session_service import update_session_state

from utils.logging import (
    get_logger,
    log_info,
    log_warning,
)

from utils.timestamps import utc_now_iso


logger = get_logger(__name__)


# ============================================================
# FIRESTORE
# ============================================================

QUESTS_COLLECTION = "quests"


# ============================================================
# QUEST STATES
# ============================================================

STATE_NEW = "NEW"

STATE_INTRO_COMPLETE = "INTRO_COMPLETE"
STATE_GATE_ENTERED = "GATE_ENTERED"
STATE_MAGIC_VERIFIED = "MAGIC_VERIFIED"
STATE_BIRTHDAY_SCENE = "BIRTHDAY_SCENE"

STATE_VIDEO_1_RECORDING = "VIDEO_1_RECORDING"
STATE_CANDLE_TRIGGERED = "CANDLE_TRIGGERED"
STATE_VIDEO_1_STOPPING = "VIDEO_1_STOPPING"
STATE_VIDEO_1_UPLOAD_PENDING = "VIDEO_1_UPLOAD_PENDING"
STATE_VIDEO_1_UPLOADED = "VIDEO_1_UPLOADED"
STATE_VIDEO_1_VERIFIED = "VIDEO_1_VERIFIED"

STATE_VIDEO_2_READY = "VIDEO_2_READY"
STATE_VIDEO_2_RECORDING = "VIDEO_2_RECORDING"

STATE_WALL_UNLOCKED = "WALL_UNLOCKED"
STATE_COLLECTIBLES_COMPLETE = "COLLECTIBLES_COMPLETE"
STATE_TICKET_COLLECTED = "TICKET_COLLECTED"
STATE_TRAIN_COMPLETE = "TRAIN_COMPLETE"
STATE_SORTING_COMPLETE = "SORTING_COMPLETE"

STATE_LEVEL_1_COMPLETE = "LEVEL_1_COMPLETE"
STATE_LEVEL_2_COMPLETE = "LEVEL_2_COMPLETE"
STATE_LEVEL_3_COMPLETE = "LEVEL_3_COMPLETE"
STATE_LEVEL_4_COMPLETE = "LEVEL_4_COMPLETE"

STATE_FINAL_REVEAL = "FINAL_REVEAL"
STATE_FINAL_VIDEO_STARTED = "FINAL_VIDEO_STARTED"
STATE_FINAL_VIDEO_COMPLETED = "FINAL_VIDEO_COMPLETED"

STATE_REACTION_RECORDING = "REACTION_RECORDING"
STATE_REACTION_UPLOAD = "REACTION_UPLOAD"

STATE_SESSION_COMPLETE = "SESSION_COMPLETE"


# ============================================================
# LEVEL CONFIGURATION
# ============================================================

LEVEL_STATES = {
    1: STATE_LEVEL_1_COMPLETE,
    2: STATE_LEVEL_2_COMPLETE,
    3: STATE_LEVEL_3_COMPLETE,
    4: STATE_LEVEL_4_COMPLETE,
}


# These are temporary server-side placeholders.
#
# IMPORTANT:
# Actual hidden words will be finalized later as quest content.
# The frontend must never be treated as the authority for these.
LEVEL_HIDDEN_WORDS = {
    1: "LEVEL_ONE_WORD",
    2: "LEVEL_TWO_WORD",
    3: "LEVEL_THREE_WORD",
    4: "LEVEL_FOUR_WORD",
}


# ============================================================
# COLLECTIBLES
# ============================================================

ALLOWED_ITEMS = frozenset(
    {
        "owl",
        "wand",
        "broom",
    }
)


# ============================================================
# STATE MACHINE
# ============================================================

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    STATE_NEW: frozenset(
        {
            STATE_INTRO_COMPLETE,
        }
    ),

    STATE_INTRO_COMPLETE: frozenset(
        {
            STATE_GATE_ENTERED,
        }
    ),

    STATE_GATE_ENTERED: frozenset(
        {
            STATE_MAGIC_VERIFIED,
        }
    ),

    STATE_MAGIC_VERIFIED: frozenset(
        {
            STATE_BIRTHDAY_SCENE,
        }
    ),

    STATE_BIRTHDAY_SCENE: frozenset(
        {
            STATE_VIDEO_1_RECORDING,
        }
    ),

    STATE_VIDEO_1_RECORDING: frozenset(
        {
            STATE_CANDLE_TRIGGERED,
        }
    ),

    STATE_CANDLE_TRIGGERED: frozenset(
        {
            STATE_VIDEO_1_STOPPING,
        }
    ),

    STATE_VIDEO_1_STOPPING: frozenset(
        {
            STATE_VIDEO_1_UPLOAD_PENDING,
        }
    ),

    STATE_VIDEO_1_UPLOAD_PENDING: frozenset(
        {
            STATE_VIDEO_1_UPLOADED,
        }
    ),

    STATE_VIDEO_1_UPLOADED: frozenset(
        {
            STATE_VIDEO_1_VERIFIED,
        }
    ),

    STATE_VIDEO_1_VERIFIED: frozenset(
        {
            STATE_VIDEO_2_READY,
        }
    ),

    STATE_VIDEO_2_READY: frozenset(
        {
            STATE_VIDEO_2_RECORDING,
        }
    ),

    STATE_VIDEO_2_RECORDING: frozenset(
        {
            STATE_WALL_UNLOCKED,
        }
    ),

    STATE_WALL_UNLOCKED: frozenset(
        {
            STATE_COLLECTIBLES_COMPLETE,
        }
    ),

    STATE_COLLECTIBLES_COMPLETE: frozenset(
        {
            STATE_TICKET_COLLECTED,
        }
    ),

    STATE_TICKET_COLLECTED: frozenset(
        {
            STATE_TRAIN_COMPLETE,
        }
    ),

    STATE_TRAIN_COMPLETE: frozenset(
        {
            STATE_SORTING_COMPLETE,
        }
    ),

    STATE_SORTING_COMPLETE: frozenset(
        {
            STATE_LEVEL_1_COMPLETE,
        }
    ),

    STATE_LEVEL_1_COMPLETE: frozenset(
        {
            STATE_LEVEL_2_COMPLETE,
        }
    ),

    STATE_LEVEL_2_COMPLETE: frozenset(
        {
            STATE_LEVEL_3_COMPLETE,
        }
    ),

    STATE_LEVEL_3_COMPLETE: frozenset(
        {
            STATE_LEVEL_4_COMPLETE,
        }
    ),

    STATE_LEVEL_4_COMPLETE: frozenset(
        {
            STATE_FINAL_REVEAL,
        }
    ),

    STATE_FINAL_REVEAL: frozenset(
        {
            STATE_FINAL_VIDEO_STARTED,
        }
    ),

    STATE_FINAL_VIDEO_STARTED: frozenset(
        {
            STATE_FINAL_VIDEO_COMPLETED,
        }
    ),

    STATE_FINAL_VIDEO_COMPLETED: frozenset(
        {
            STATE_REACTION_RECORDING,
        }
    ),

    STATE_REACTION_RECORDING: frozenset(
        {
            STATE_REACTION_UPLOAD,
        }
    ),

    STATE_REACTION_UPLOAD: frozenset(
        {
            STATE_SESSION_COMPLETE,
        }
    ),

    STATE_SESSION_COMPLETE: frozenset(),
}


# ============================================================
# INTERNAL VALIDATION
# ============================================================

def _validate_session(session: Session) -> None:
    if not isinstance(session, Session):
        raise TypeError(
            "session must be a Session instance."
        )

    if not session.active:
        raise ValueError(
            "The session is inactive."
        )

    if session.state == STATE_SESSION_COMPLETE:
        raise ValueError(
            "The session is already complete."
        )


def _validate_quest(
    session: Session,
    quest: Quest,
) -> None:
    if not isinstance(quest, Quest):
        raise TypeError(
            "quest must be a Quest instance."
        )

    if quest.session_id != session.session_id:
        raise ValueError(
            "Session and quest do not belong together."
        )


# ============================================================
# QUEST CREATION / RETRIEVAL
# ============================================================

def create_quest(
    session: Session,
) -> Quest:
    """
    Create a new quest for a session.

    If a quest already exists, the existing quest is returned.
    """

    _validate_session(session)

    existing = get_quest(
        session.session_id
    )

    if existing is not None:
        return existing

    quest = Quest(
        session_id=session.session_id,
        state=STATE_NEW,
        current_level=0,
        completed_levels=[],
        collected_items=[],
        discovered_words=[],
        collected_ticket=False,
        train_completed=False,
        final_reveal_unlocked=False,
        version=1,
        metadata={},
    )

    set_document_data(
        QUESTS_COLLECTION,
        session.session_id,
        quest.to_dict(),
    )

    log_info(
        logger,
        "quest_created",
        session_id=session.session_id,
        state=quest.state,
    )

    return quest


def get_quest(
    session_id: str,
) -> Quest | None:
    """
    Retrieve a quest by session ID.
    """

    data = get_document_data(
        QUESTS_COLLECTION,
        session_id,
    )

    if data is None:
        return None

    return Quest.from_dict(data)


def get_or_create_quest(
    session: Session,
) -> Quest:
    """
    Return an existing quest or create one.
    """

    _validate_session(session)

    existing = get_quest(
        session.session_id
    )

    if existing is not None:
        return existing

    return create_quest(session)


# ============================================================
# STATE TRANSITIONS
# ============================================================

def can_transition(
    current_state: str,
    next_state: str,
) -> bool:
    """
    Return True when the requested state transition is legal.
    """

    allowed_states = ALLOWED_TRANSITIONS.get(
        current_state,
        frozenset(),
    )

    return next_state in allowed_states


def transition_quest(
    session: Session,
    quest: Quest,
    next_state: str,
) -> Quest:
    """
    Perform one validated quest state transition.

    The client cannot freely choose an arbitrary state.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if not isinstance(next_state, str):
        raise TypeError(
            "next_state must be a string."
        )

    next_state = next_state.strip()

    if not next_state:
        raise ValueError(
            "next_state cannot be empty."
        )

    previous_state = quest.state

    if not can_transition(
        previous_state,
        next_state,
    ):
        log_warning(
            logger,
            "invalid_quest_transition",
            session_id=session.session_id,
            current_state=previous_state,
            requested_state=next_state,
        )

        raise ValueError(
            f"Invalid quest transition: "
            f"{previous_state} -> {next_state}"
        )

    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "state": next_state,
            "version": next_version,
        },
    )

    quest.state = next_state
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "quest_transition",
        session_id=session.session_id,
        previous_state=previous_state,
        next_state=next_state,
    )

    return quest


# ============================================================
# LEVEL PROGRESSION
# ============================================================

def complete_level(
    session: Session,
    quest: Quest,
    level: int,
) -> Quest:
    """
    Complete one of the four normal quest levels.

    Level 5 is intentionally not accepted here.
    Final Reveal has its own dedicated function.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError(
            "level must be an integer."
        )

    if level not in LEVEL_STATES:
        raise ValueError(
            "Invalid quest level. "
            "Only levels 1 through 4 are valid."
        )

    expected_current_level = level - 1

    if quest.current_level != expected_current_level:
        raise ValueError(
            "This level is not currently available."
        )

    if level in quest.completed_levels:
        raise ValueError(
            "This level has already been completed."
        )

    next_state = LEVEL_STATES[level]

    if not can_transition(
        quest.state,
        next_state,
    ):
        raise ValueError(
            f"Quest state does not allow "
            f"completion of level {level}."
        )

    completed_levels = list(
        quest.completed_levels
    )

    completed_levels.append(level)

    completed_levels = sorted(
        set(completed_levels)
    )

    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "state": next_state,
            "current_level": level,
            "completed_levels": completed_levels,
            "version": next_version,
        },
    )

    quest.state = next_state
    quest.current_level = level
    quest.completed_levels = completed_levels
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "level_completed",
        session_id=session.session_id,
        level=level,
        state=next_state,
    )

    return quest


# ============================================================
# COLLECTIBLES
# ============================================================

def collect_item(
    session: Session,
    quest: Quest,
    item_id: str,
) -> Quest:
    """
    Collect one of the three magical quest items.

    The quest advances automatically after all three are collected.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if quest.state != STATE_WALL_UNLOCKED:
        raise ValueError(
            "Collectibles are not currently available."
        )

    if not isinstance(item_id, str):
        raise TypeError(
            "item_id must be a string."
        )

    item_id = item_id.strip().casefold()

    if not item_id:
        raise ValueError(
            "item_id cannot be empty."
        )

    if item_id not in ALLOWED_ITEMS:
        raise ValueError(
            "Unknown quest item."
        )

    if item_id in quest.collected_items:
        return quest

    collected_items = list(
        quest.collected_items
    )

    collected_items.append(
        item_id
    )

    collected_items = sorted(
        set(collected_items)
    )

    if ALLOWED_ITEMS.issubset(
        set(collected_items)
    ):
        next_state = STATE_COLLECTIBLES_COMPLETE
    else:
        next_state = STATE_WALL_UNLOCKED

    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "collected_items": collected_items,
            "state": next_state,
            "version": next_version,
        },
    )

    quest.collected_items = collected_items
    quest.state = next_state
    quest.version = next_version

    if next_state != session.state:
        update_session_state(
            session,
            next_state,
        )

    log_info(
        logger,
        "quest_item_collected",
        session_id=session.session_id,
        item_id=item_id,
        items_collected=len(collected_items),
    )

    return quest


# ============================================================
# RAILWAY TICKET
# ============================================================

def collect_ticket(
    session: Session,
    quest: Quest,
) -> Quest:
    """
    Collect the railway ticket after all collectibles are complete.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if quest.state != STATE_COLLECTIBLES_COMPLETE:
        raise ValueError(
            "The railway ticket is not currently available."
        )

    if quest.collected_ticket:
        return quest

    next_state = STATE_TICKET_COLLECTED
    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "collected_ticket": True,
            "state": next_state,
            "version": next_version,
        },
    )

    quest.collected_ticket = True
    quest.state = next_state
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "ticket_collected",
        session_id=session.session_id,
    )

    return quest


# ============================================================
# TRAIN
# ============================================================

def complete_train(
    session: Session,
    quest: Quest,
) -> Quest:
    """
    Complete the magical train sequence.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if quest.state != STATE_TICKET_COLLECTED:
        raise ValueError(
            "The train sequence is not currently available."
        )

    if quest.train_completed:
        return quest

    next_state = STATE_TRAIN_COMPLETE
    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "train_completed": True,
            "state": next_state,
            "version": next_version,
        },
    )

    quest.train_completed = True
    quest.state = next_state
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "train_completed",
        session_id=session.session_id,
    )

    return quest


# ============================================================
# SORTING
# ============================================================

def complete_sorting(
    session: Session,
    quest: Quest,
) -> Quest:
    """
    Complete the magical sorting sequence and unlock Level 1.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if quest.state != STATE_TRAIN_COMPLETE:
        raise ValueError(
            "Sorting is not currently available."
        )

    next_state = STATE_SORTING_COMPLETE
    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "state": next_state,
            "version": next_version,
        },
    )

    quest.state = next_state
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "sorting_completed",
        session_id=session.session_id,
    )

    return quest


# ============================================================
# HIDDEN WORDS
# ============================================================

def discover_word(
    session: Session,
    quest: Quest,
    word: str,
) -> Quest:
    """
    Validate and record the next hidden quest word.

    The client cannot invent arbitrary hidden words.
    The backend determines which word is expected next.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    if not isinstance(word, str):
        raise TypeError(
            "word must be a string."
        )

    normalized_word = word.strip().casefold()

    if not normalized_word:
        raise ValueError(
            "word cannot be empty."
        )

    discovered_count = len(
        quest.discovered_words
    )

    if discovered_count >= 4:
        raise ValueError(
            "All hidden words have already been discovered."
        )

    expected_word = LEVEL_HIDDEN_WORDS.get(
        discovered_count + 1
    )

    if expected_word is None:
        raise ValueError(
            "No hidden word is configured "
            "for this progression step."
        )

    expected_word = expected_word.casefold()

    if normalized_word != expected_word:
        raise ValueError(
            "The submitted hidden word is not valid."
        )

    if normalized_word in {
        item.casefold()
        for item in quest.discovered_words
    }:
        return quest

    discovered_words = list(
        quest.discovered_words
    )

    discovered_words.append(
        normalized_word
    )

    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "discovered_words": discovered_words,
            "version": next_version,
        },
    )

    quest.discovered_words = discovered_words
    quest.version = next_version

    log_info(
        logger,
        "hidden_word_discovered",
        session_id=session.session_id,
        word_index=discovered_count + 1,
    )

    return quest


# ============================================================
# FINAL REVEAL
# ============================================================

def unlock_final_reveal(
    session: Session,
    quest: Quest,
) -> Quest:
    """
    Unlock the Final Reveal.

    Requirements:
    - All four levels completed.
    - All four hidden words discovered.
    - Current state must be LEVEL_4_COMPLETE.
    """

    _validate_session(session)
    _validate_quest(
        session,
        quest,
    )

    required_levels = {
        1,
        2,
        3,
        4,
    }

    if not required_levels.issubset(
        set(quest.completed_levels)
    ):
        raise ValueError(
            "All four quest levels must be completed first."
        )

    if quest.current_level != 4:
        raise ValueError(
            "The quest must be at level 4 before "
            "the final reveal can be unlocked."
        )

    if len(quest.discovered_words) != 4:
        raise ValueError(
            "All four hidden words must be discovered first."
        )

    if quest.state != STATE_LEVEL_4_COMPLETE:
        raise ValueError(
            "The final reveal is not currently available."
        )

    if quest.final_reveal_unlocked:
        return quest

    next_state = STATE_FINAL_REVEAL
    next_version = quest.version + 1

    update_document_data(
        QUESTS_COLLECTION,
        quest.session_id,
        {
            "final_reveal_unlocked": True,
            "state": next_state,
            "version": next_version,
        },
    )

    quest.final_reveal_unlocked = True
    quest.state = next_state
    quest.version = next_version

    update_session_state(
        session,
        next_state,
    )

    log_info(
        logger,
        "final_reveal_unlocked",
        session_id=session.session_id,
    )

    return quest
