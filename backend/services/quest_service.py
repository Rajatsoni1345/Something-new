"""
Birthday Quest - Quest Service

Centralized quest state machine and progression logic.

Storage architecture:
- Firebase Firestore -> quest/session state and metadata
- Cloudinary -> permanent recorded videos
- Render filesystem -> never used for permanent recordings

IMPORTANT:
- The client cannot directly choose the next quest state.
- Every state transition is explicitly validated.
- Normal quest levels are strictly 1 through 4.
- Level answers are validated server-side.
- Hidden words are validated server-side.
- Quest/session state changes are performed transactionally.
- Quest creation is transaction-safe.
- Optimistic version checks prevent stale writes.
- SESSION_COMPLETE permanently deactivates the session.
- This service does not handle video uploads.

CONSTANTS:
    All state names, collections, levels, and item IDs are
    imported from constants.py — the single source of truth.
    Nothing here redefines them.
"""

from __future__ import annotations

from typing import Any

from constants import (
    ALLOWED_COLLECTIBLE_ITEMS as ALLOWED_ITEMS,
    FIRESTORE_COLLECTION_QUESTS as QUESTS_COLLECTION,
    FIRESTORE_COLLECTION_SESSIONS as SESSIONS_COLLECTION,
    NORMAL_QUEST_LEVELS,
    QUEST_STATE_BIRTHDAY_SCENE as STATE_BIRTHDAY_SCENE,
    QUEST_STATE_CANDLE_TRIGGERED as STATE_CANDLE_TRIGGERED,
    QUEST_STATE_COLLECTIBLES_COMPLETE as STATE_COLLECTIBLES_COMPLETE,
    QUEST_STATE_FINAL_REVEAL as STATE_FINAL_REVEAL,
    QUEST_STATE_FINAL_VIDEO_COMPLETED as STATE_FINAL_VIDEO_COMPLETED,
    QUEST_STATE_FINAL_VIDEO_STARTED as STATE_FINAL_VIDEO_STARTED,
    QUEST_STATE_GATE_ENTERED as STATE_GATE_ENTERED,
    QUEST_STATE_INTRO_COMPLETE as STATE_INTRO_COMPLETE,
    QUEST_STATE_LEVEL_1_COMPLETE as STATE_LEVEL_1_COMPLETE,
    QUEST_STATE_LEVEL_2_COMPLETE as STATE_LEVEL_2_COMPLETE,
    QUEST_STATE_LEVEL_3_COMPLETE as STATE_LEVEL_3_COMPLETE,
    QUEST_STATE_LEVEL_4_COMPLETE as STATE_LEVEL_4_COMPLETE,
    QUEST_STATE_MAGIC_VERIFIED as STATE_MAGIC_VERIFIED,
    QUEST_STATE_NEW as STATE_NEW,
    QUEST_STATE_REACTION_RECORDING as STATE_REACTION_RECORDING,
    QUEST_STATE_REACTION_UPLOAD as STATE_REACTION_UPLOAD,
    QUEST_STATE_SESSION_COMPLETE as STATE_SESSION_COMPLETE,
    QUEST_STATE_SORTING_COMPLETE as STATE_SORTING_COMPLETE,
    QUEST_STATE_TICKET_COLLECTED as STATE_TICKET_COLLECTED,
    QUEST_STATE_TRAIN_COMPLETE as STATE_TRAIN_COMPLETE,
    QUEST_STATE_VIDEO_1_RECORDING as STATE_VIDEO_1_RECORDING,
    QUEST_STATE_VIDEO_1_STOPPING as STATE_VIDEO_1_STOPPING,
    QUEST_STATE_VIDEO_1_UPLOADED as STATE_VIDEO_1_UPLOADED,
    QUEST_STATE_VIDEO_1_UPLOAD_PENDING as STATE_VIDEO_1_UPLOAD_PENDING,
    QUEST_STATE_VIDEO_1_VERIFIED as STATE_VIDEO_1_VERIFIED,
    QUEST_STATE_VIDEO_2_READY as STATE_VIDEO_2_READY,
    QUEST_STATE_VIDEO_2_RECORDING as STATE_VIDEO_2_RECORDING,
    QUEST_STATE_WALL_UNLOCKED as STATE_WALL_UNLOCKED,
)

from models.quest import Quest
from models.session import Session

from services.firebase_service import (
    get_document,
    get_document_data,
    run_transaction,
)

from utils.logging import (
    get_logger,
    log_info,
    log_warning,
)

from utils.timestamps import utc_now_iso


# ============================================================
# LOGGER
# ============================================================

logger = get_logger(__name__)


# ============================================================
# LEVEL CONFIGURATION
# ============================================================

LEVEL_STATES = {
    1: STATE_LEVEL_1_COMPLETE,
    2: STATE_LEVEL_2_COMPLETE,
    3: STATE_LEVEL_3_COMPLETE,
    4: STATE_LEVEL_4_COMPLETE,
}


# ============================================================
# SERVER-SIDE QUEST ANSWERS
# ============================================================
#
# IMPORTANT:
# The frontend must NEVER be treated as the authority for
# whether an answer is correct. Only these server-side values
# are authoritative.
#
# Replace the placeholder strings when the actual quest
# content is finalized. Case-insensitive matching is applied
# at comparison time.
# ============================================================

LEVEL_ANSWERS = {
    1: "LEVEL_ONE_ANSWER",
    2: "LEVEL_TWO_ANSWER",
    3: "LEVEL_THREE_ANSWER",
    4: "LEVEL_FOUR_ANSWER",
}


# ============================================================
# SERVER-SIDE HIDDEN WORDS
# ============================================================
#
# The four hidden words, when revealed together, form:
#     "You somehow became home."
#
# Word 1 belongs to Level 1, Word 2 to Level 2, and so on.
# ============================================================

LEVEL_HIDDEN_WORDS = {
    1: "LEVEL_ONE_WORD",
    2: "LEVEL_TWO_WORD",
    3: "LEVEL_THREE_WORD",
    4: "LEVEL_FOUR_WORD",
}


# ============================================================
# STATE MACHINE
# ============================================================
#
# Every legal quest transition is declared exactly once.
# The client can never invent a new state or skip a step.
# ============================================================

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    STATE_NEW: frozenset({STATE_INTRO_COMPLETE}),

    STATE_INTRO_COMPLETE: frozenset({
        STATE_GATE_ENTERED,
    }),

    STATE_GATE_ENTERED: frozenset({
        STATE_MAGIC_VERIFIED,
    }),

    STATE_MAGIC_VERIFIED: frozenset({
        STATE_BIRTHDAY_SCENE,
    }),

    STATE_BIRTHDAY_SCENE: frozenset({
        STATE_VIDEO_1_RECORDING,
    }),

    STATE_VIDEO_1_RECORDING: frozenset({
        STATE_CANDLE_TRIGGERED,
    }),

    STATE_CANDLE_TRIGGERED: frozenset({
        STATE_VIDEO_1_STOPPING,
    }),

    STATE_VIDEO_1_STOPPING: frozenset({
        STATE_VIDEO_1_UPLOAD_PENDING,
    }),

    STATE_VIDEO_1_UPLOAD_PENDING: frozenset({
        STATE_VIDEO_1_UPLOADED,
    }),

    STATE_VIDEO_1_UPLOADED: frozenset({
        STATE_VIDEO_1_VERIFIED,
    }),

    STATE_VIDEO_1_VERIFIED: frozenset({
        STATE_VIDEO_2_READY,
    }),

    STATE_VIDEO_2_READY: frozenset({
        STATE_VIDEO_2_RECORDING,
    }),

    STATE_VIDEO_2_RECORDING: frozenset({
        STATE_WALL_UNLOCKED,
    }),

    STATE_WALL_UNLOCKED: frozenset({
        STATE_COLLECTIBLES_COMPLETE,
    }),

    STATE_COLLECTIBLES_COMPLETE: frozenset({
        STATE_TICKET_COLLECTED,
    }),

    STATE_TICKET_COLLECTED: frozenset({
        STATE_TRAIN_COMPLETE,
    }),

    STATE_TRAIN_COMPLETE: frozenset({
        STATE_SORTING_COMPLETE,
    }),

    STATE_SORTING_COMPLETE: frozenset({
        STATE_LEVEL_1_COMPLETE,
    }),

    STATE_LEVEL_1_COMPLETE: frozenset({
        STATE_LEVEL_2_COMPLETE,
    }),

    STATE_LEVEL_2_COMPLETE: frozenset({
        STATE_LEVEL_3_COMPLETE,
    }),

    STATE_LEVEL_3_COMPLETE: frozenset({
        STATE_LEVEL_4_COMPLETE,
    }),

    STATE_LEVEL_4_COMPLETE: frozenset({
        STATE_FINAL_REVEAL,
    }),

    STATE_FINAL_REVEAL: frozenset({
        STATE_FINAL_VIDEO_STARTED,
    }),

    STATE_FINAL_VIDEO_STARTED: frozenset({
        STATE_FINAL_VIDEO_COMPLETED,
    }),

    STATE_FINAL_VIDEO_COMPLETED: frozenset({
        STATE_REACTION_RECORDING,
    }),

    STATE_REACTION_RECORDING: frozenset({
        STATE_REACTION_UPLOAD,
    }),

    STATE_REACTION_UPLOAD: frozenset({
        STATE_SESSION_COMPLETE,
    }),

    STATE_SESSION_COMPLETE: frozenset(),
}


# ============================================================
# INTERNAL VALIDATION
# ============================================================

def _validate_session(session: Session) -> None:
    """
    Validate the supplied session object.
    """

    if not isinstance(session, Session):
        raise TypeError("session must be a Session instance.")

    if not session.active:
        raise ValueError("The session is inactive.")

    if session.state == STATE_SESSION_COMPLETE:
        raise ValueError("The session is already complete.")


def _validate_quest(session: Session, quest: Quest) -> None:
    """
    Ensure the quest belongs to the supplied session.
    """

    if not isinstance(quest, Quest):
        raise TypeError("quest must be a Quest instance.")

    if quest.session_id != session.session_id:
        raise ValueError(
            "Session and quest do not belong together."
        )


def _normalize_answer(answer: Any) -> str:
    """
    Normalize an answer for case-insensitive comparison.
    """

    if not isinstance(answer, str):
        raise TypeError("answer must be a string.")

    normalized = answer.strip().casefold()

    if not normalized:
        raise ValueError("answer cannot be empty.")

    if len(normalized) > 512:
        raise ValueError("answer is too long.")

    return normalized


def _normalize_word(word: Any) -> str:
    """
    Normalize a hidden word for case-insensitive comparison.
    """

    if not isinstance(word, str):
        raise TypeError("word must be a string.")

    normalized = word.strip().casefold()

    if not normalized:
        raise ValueError("word cannot be empty.")

    if len(normalized) > 128:
        raise ValueError("word is too long.")

    return normalized


# ============================================================
# FIRESTORE REFERENCES
# ============================================================

def _get_quest_document(session_id: str):
    """
    Return the Firestore quest document reference.
    """

    return get_document(QUESTS_COLLECTION, session_id)


def _get_session_document(session_id: str):
    """
    Return the Firestore session document reference.
    """

    return get_document(SESSIONS_COLLECTION, session_id)


# ============================================================
# TRANSACTION HELPERS
# ============================================================

def _read_transaction_documents(transaction, session_id: str):
    """
    Read both quest and session documents inside the same
    Firestore transaction.

    All reads happen before transaction writes.
    """

    session_document = _get_session_document(session_id)
    quest_document = _get_quest_document(session_id)

    session_snapshot = transaction.get(session_document)
    quest_snapshot = transaction.get(quest_document)

    return session_snapshot, quest_snapshot


def _load_transaction_state(transaction, session_id: str):
    """
    Read and validate the current session and quest from a
    transaction.

    Returns:
        transaction,
        session_document,
        quest_document,
        session,
        quest
    """

    session_snapshot, quest_snapshot = _read_transaction_documents(
        transaction,
        session_id,
    )

    if not session_snapshot.exists:
        raise ValueError("Session no longer exists.")

    if not quest_snapshot.exists:
        raise ValueError(
            "Quest no longer exists for this session."
        )

    session_data = session_snapshot.to_dict()
    quest_data = quest_snapshot.to_dict()

    if not isinstance(session_data, dict):
        raise RuntimeError("Stored session data is invalid.")

    if not isinstance(quest_data, dict):
        raise RuntimeError("Stored quest data is invalid.")

    session = Session.from_dict(session_data)
    quest = Quest.from_dict(quest_data)

    _validate_session(session)
    _validate_quest(session, quest)

    return (
        transaction,
        _get_session_document(session_id),
        _get_quest_document(session_id),
        session,
        quest,
    )


def _validate_expected_versions(
    supplied_session: Session,
    supplied_quest: Quest,
    stored_session: Session,
    stored_quest: Quest,
) -> None:
    """
    Prevent stale service objects from overwriting newer data.
    """

    if supplied_session.version != stored_session.version:
        raise RuntimeError(
            "Session version conflict. "
            "The session was modified by another request."
        )

    if supplied_quest.version != stored_quest.version:
        raise RuntimeError(
            "Quest version conflict. "
            "The quest was modified by another request."
        )


def _copy_session_values(target: Session, source: Session) -> None:
    """
    Synchronize a caller's Session model with the persisted
    transaction result.
    """

    target.state = source.state
    target.updated_at = source.updated_at
    target.last_activity_at = source.last_activity_at
    target.completed_at = source.completed_at
    target.version = source.version
    target.active = source.active


def _copy_quest_values(target: Quest, source: Quest) -> None:
    """
    Synchronize a caller's Quest model with the persisted
    transaction result.
    """

    target.state = source.state
    target.current_level = source.current_level
    target.completed_levels = list(source.completed_levels)
    target.collected_items = list(source.collected_items)
    target.discovered_words = list(source.discovered_words)
    target.collected_ticket = source.collected_ticket
    target.train_completed = source.train_completed
    target.final_reveal_unlocked = source.final_reveal_unlocked
    target.version = source.version
    target.metadata = dict(source.metadata)


# ============================================================
# QUEST CREATION
# ============================================================

def create_quest(session: Session) -> Quest:
    """
    Create a new quest for a session.

    Creation is transaction-safe.

    If another request creates the quest between the initial
    request and transaction execution, the already-created
    quest is returned instead of overwriting it.
    """

    _validate_session(session)

    quest_document = _get_quest_document(session.session_id)

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

    def create_operation(transaction):
        snapshot = transaction.get(quest_document)

        if snapshot.exists:
            existing_data = snapshot.to_dict()

            if not isinstance(existing_data, dict):
                raise RuntimeError("Stored quest data is invalid.")

            return Quest.from_dict(existing_data)

        transaction.create(quest_document, quest.to_dict())

        return quest

    result = run_transaction(create_operation)

    if result is not quest:
        log_info(
            logger,
            "quest_already_exists",
            session_id=session.session_id,
            state=result.state,
        )
        return result

    log_info(
        logger,
        "quest_created",
        session_id=session.session_id,
        state=result.state,
    )

    return result


# ============================================================
# QUEST RETRIEVAL
# ============================================================

def get_quest(session_id: str) -> Quest | None:
    """
    Retrieve a quest by session ID.
    """

    data = get_document_data(QUESTS_COLLECTION, session_id)

    if data is None:
        return None

    return Quest.from_dict(data)


def get_or_create_quest(session: Session) -> Quest:
    """
    Return an existing quest or create one.

    The creation path itself is transaction-safe, so concurrent
    callers cannot overwrite one another's quest.
    """

    _validate_session(session)

    existing = get_quest(session.session_id)

    if existing is not None:
        _validate_quest(session, existing)
        return existing

    return create_quest(session)


# ============================================================
# STATE MACHINE HELPERS
# ============================================================

def can_transition(current_state: str, next_state: str) -> bool:
    """
    Return True when the requested state transition is legal.
    """

    if not isinstance(current_state, str):
        return False

    if not isinstance(next_state, str):
        return False

    allowed_states = ALLOWED_TRANSITIONS.get(
        current_state,
        frozenset(),
    )

    return next_state in allowed_states


# ============================================================
# GENERIC QUEST TRANSITION
# ============================================================

def transition_quest(
    session: Session,
    quest: Quest,
    next_state: str,
) -> Quest:
    """
    Perform one validated quest state transition.

    Quest and session changes are committed atomically.

    SESSION_COMPLETE is special:
    - quest state becomes SESSION_COMPLETE
    - session state becomes SESSION_COMPLETE
    - session becomes inactive
    - completed_at is written

    This is the ONLY authoritative path that can set a session
    to SESSION_COMPLETE. session_service must not bypass it.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if not isinstance(next_state, str):
        raise TypeError("next_state must be a string.")

    next_state = next_state.strip()

    if not next_state:
        raise ValueError("next_state cannot be empty.")

    if len(next_state) > 128:
        raise ValueError(
            "next_state cannot exceed 128 characters."
        )

    if not can_transition(quest.state, next_state):
        log_warning(
            logger,
            "invalid_quest_transition",
            session_id=session.session_id,
            current_state=quest.state,
            requested_state=next_state,
        )

        raise ValueError(
            f"Invalid quest transition: "
            f"{quest.state} -> {next_state}"
        )

    requested_previous_state = quest.state

    def transition_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.state != quest.state:
            raise RuntimeError(
                "Quest state conflict. "
                "The quest was modified by another request."
            )

        if stored_session.state != session.state:
            raise RuntimeError(
                "Session state conflict. "
                "The session was modified by another request."
            )

        if not can_transition(stored_quest.state, next_state):
            raise ValueError(
                f"Invalid quest transition: "
                f"{stored_quest.state} -> {next_state}"
            )

        now = utc_now_iso()

        stored_quest.state = next_state
        stored_quest.version += 1

        stored_session.state = next_state
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        if next_state == STATE_SESSION_COMPLETE:
            stored_session.active = False
            stored_session.completed_at = now

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(
        transition_operation
    )

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "quest_transition",
        session_id=session.session_id,
        previous_state=requested_previous_state,
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
    answer: str,
) -> Quest:
    """
    Complete one of the four normal quest levels.

    Level 5 is intentionally not accepted here — the final
    reveal has its own dedicated flow.

    The answer is authoritative on the server.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError("level must be an integer.")

    if level not in NORMAL_QUEST_LEVELS:
        raise ValueError(
            "Invalid quest level. "
            "Only levels 1 through 4 are valid."
        )

    normalized_answer = _normalize_answer(answer)

    expected_answer = LEVEL_ANSWERS.get(level)

    if expected_answer is None:
        raise ValueError(
            "No answer is configured for this level."
        )

    if normalized_answer != expected_answer.casefold():
        log_warning(
            logger,
            "incorrect_level_answer",
            session_id=session.session_id,
            level=level,
        )

        raise ValueError(
            "The submitted answer is incorrect."
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

    if not can_transition(quest.state, next_state):
        raise ValueError(
            f"Quest state does not allow "
            f"completion of level {level}."
        )

    def level_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.current_level != expected_current_level:
            raise ValueError(
                "This level is not currently available."
            )

        if level in stored_quest.completed_levels:
            raise ValueError(
                "This level has already been completed."
            )

        if not can_transition(stored_quest.state, next_state):
            raise ValueError(
                f"Quest state does not allow "
                f"completion of level {level}."
            )

        completed_levels = list(stored_quest.completed_levels)
        completed_levels.append(level)
        completed_levels = sorted(set(completed_levels))

        now = utc_now_iso()

        stored_quest.state = next_state
        stored_quest.current_level = level
        stored_quest.completed_levels = completed_levels
        stored_quest.version += 1

        stored_session.state = next_state
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(
        level_operation
    )

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "level_completed",
        session_id=session.session_id,
        level=level,
        state=quest.state,
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

    The final collectible causes the quest to transition from
    WALL_UNLOCKED to COLLECTIBLES_COMPLETE.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if quest.state != STATE_WALL_UNLOCKED:
        raise ValueError(
            "Collectibles are not currently available."
        )

    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string.")

    item_id = item_id.strip().casefold()

    if not item_id:
        raise ValueError("item_id cannot be empty.")

    if item_id not in ALLOWED_ITEMS:
        raise ValueError("Unknown quest item.")

    def item_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.state != STATE_WALL_UNLOCKED:
            raise ValueError(
                "Collectibles are not currently available."
            )

        if item_id in stored_quest.collected_items:
            return stored_session, stored_quest

        collected_items = list(stored_quest.collected_items)
        collected_items.append(item_id)
        collected_items = sorted(set(collected_items))

        if ALLOWED_ITEMS.issubset(set(collected_items)):
            next_state = STATE_COLLECTIBLES_COMPLETE
        else:
            next_state = STATE_WALL_UNLOCKED

        now = utc_now_iso()

        stored_quest.collected_items = collected_items
        stored_quest.state = next_state
        stored_quest.version += 1

        stored_session.state = next_state
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(item_operation)

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "quest_item_collected",
        session_id=session.session_id,
        item_id=item_id,
        items_collected=len(quest.collected_items),
    )

    return quest


# ============================================================
# RAILWAY TICKET
# ============================================================

def collect_ticket(session: Session, quest: Quest) -> Quest:
    """
    Collect the railway ticket after all collectibles are
    complete.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if quest.state != STATE_COLLECTIBLES_COMPLETE:
        raise ValueError(
            "The railway ticket is not currently available."
        )

    def ticket_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.state != STATE_COLLECTIBLES_COMPLETE:
            raise ValueError(
                "The railway ticket is not currently available."
            )

        if stored_quest.collected_ticket:
            return stored_session, stored_quest

        now = utc_now_iso()

        stored_quest.collected_ticket = True
        stored_quest.state = STATE_TICKET_COLLECTED
        stored_quest.version += 1

        stored_session.state = STATE_TICKET_COLLECTED
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(ticket_operation)

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "ticket_collected",
        session_id=session.session_id,
    )

    return quest


# ============================================================
# TRAIN
# ============================================================

def complete_train(session: Session, quest: Quest) -> Quest:
    """
    Complete the magical train sequence.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if quest.state != STATE_TICKET_COLLECTED:
        raise ValueError(
            "The train sequence is not currently available."
        )

    def train_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.state != STATE_TICKET_COLLECTED:
            raise ValueError(
                "The train sequence is not currently available."
            )

        if stored_quest.train_completed:
            return stored_session, stored_quest

        now = utc_now_iso()

        stored_quest.train_completed = True
        stored_quest.state = STATE_TRAIN_COMPLETE
        stored_quest.version += 1

        stored_session.state = STATE_TRAIN_COMPLETE
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(train_operation)

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "train_completed",
        session_id=session.session_id,
    )

    return quest


# ============================================================
# SORTING
# ============================================================

def complete_sorting(session: Session, quest: Quest) -> Quest:
    """
    Complete the magical sorting sequence.

    This makes Level 1 available.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    if quest.state != STATE_TRAIN_COMPLETE:
        raise ValueError("Sorting is not currently available.")

    next_state = STATE_SORTING_COMPLETE

    def sorting_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if stored_quest.state != STATE_TRAIN_COMPLETE:
            raise ValueError("Sorting is not currently available.")

        if not can_transition(stored_quest.state, next_state):
            raise ValueError(
                "Sorting cannot be completed from the current state."
            )

        now = utc_now_iso()

        stored_quest.state = next_state
        stored_quest.version += 1

        stored_session.state = next_state
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(sorting_operation)

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

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

    Hidden words are stored in order:

        word 1 -> level 1
        word 2 -> level 2
        word 3 -> level 3
        word 4 -> level 4
    """

    _validate_session(session)
    _validate_quest(session, quest)

    normalized_word = _normalize_word(word)

    discovered_count = len(quest.discovered_words)

    if discovered_count >= 4:
        raise ValueError(
            "All hidden words have already been discovered."
        )

    expected_word = LEVEL_HIDDEN_WORDS.get(discovered_count + 1)

    if expected_word is None:
        raise ValueError(
            "No hidden word is configured for this progression step."
        )

    if normalized_word != expected_word.casefold():
        log_warning(
            logger,
            "incorrect_hidden_word",
            session_id=session.session_id,
            word_index=discovered_count + 1,
        )

        raise ValueError(
            "The submitted hidden word is not valid."
        )

    def word_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        stored_discovered_count = len(stored_quest.discovered_words)

        if stored_discovered_count >= 4:
            raise ValueError(
                "All hidden words have already been discovered."
            )

        expected_stored_word = LEVEL_HIDDEN_WORDS.get(
            stored_discovered_count + 1
        )

        if expected_stored_word is None:
            raise ValueError(
                "No hidden word is configured for this progression step."
            )

        if normalized_word != expected_stored_word.casefold():
            raise ValueError(
                "The submitted hidden word is not valid."
            )

        if normalized_word in {
            item.casefold() for item in stored_quest.discovered_words
        }:
            return stored_session, stored_quest

        discovered_words = list(stored_quest.discovered_words)
        discovered_words.append(normalized_word)

        stored_quest.discovered_words = discovered_words
        stored_quest.version += 1

        now = utc_now_iso()

        # Discovering a word does not advance the quest state,
        # but it is valid activity for the session.
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(word_operation)

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "hidden_word_discovered",
        session_id=session.session_id,
        word_index=len(quest.discovered_words),
    )

    return quest


# ============================================================
# FINAL REVEAL
# ============================================================

def unlock_final_reveal(session: Session, quest: Quest) -> Quest:
    """
    Unlock the Final Reveal.

    Requirements:
    - Levels 1 through 4 are complete.
    - Four hidden words are discovered.
    - Current level is 4.
    - Current state is LEVEL_4_COMPLETE.
    """

    _validate_session(session)
    _validate_quest(session, quest)

    required_levels = NORMAL_QUEST_LEVELS

    if not required_levels.issubset(set(quest.completed_levels)):
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

    def final_reveal_operation(transaction):
        (
            transaction,
            session_document,
            quest_document,
            stored_session,
            stored_quest,
        ) = _load_transaction_state(
            transaction,
            session.session_id,
        )

        _validate_expected_versions(
            session,
            quest,
            stored_session,
            stored_quest,
        )

        if not required_levels.issubset(
            set(stored_quest.completed_levels)
        ):
            raise ValueError(
                "All four quest levels must be completed first."
            )

        if stored_quest.current_level != 4:
            raise ValueError(
                "The quest must be at level 4 before "
                "the final reveal can be unlocked."
            )

        if len(stored_quest.discovered_words) != 4:
            raise ValueError(
                "All four hidden words must be discovered first."
            )

        if stored_quest.state != STATE_LEVEL_4_COMPLETE:
            raise ValueError(
                "The final reveal is not currently available."
            )

        if stored_quest.final_reveal_unlocked:
            return stored_session, stored_quest

        now = utc_now_iso()

        stored_quest.final_reveal_unlocked = True
        stored_quest.state = STATE_FINAL_REVEAL
        stored_quest.version += 1

        stored_session.state = STATE_FINAL_REVEAL
        stored_session.updated_at = now
        stored_session.last_activity_at = now
        stored_session.version += 1

        transaction.update(quest_document, stored_quest.to_dict())
        transaction.update(session_document, stored_session.to_dict())

        return stored_session, stored_quest

    updated_session, updated_quest = run_transaction(
        final_reveal_operation
    )

    _copy_session_values(session, updated_session)
    _copy_quest_values(quest, updated_quest)

    log_info(
        logger,
        "final_reveal_unlocked",
        session_id=session.session_id,
    )

    return quest
