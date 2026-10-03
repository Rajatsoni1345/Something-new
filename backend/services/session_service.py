"""
Birthday Quest - Session Service

Business logic for creating, recovering, reading, updating, and
completing Birthday Quest sessions.

IMPORTANT:
- Session persistence is handled through Firebase/Firestore.
- Version updates use Firestore transactions where a read-modify-
  write operation is required.
- Session state is never accepted directly from the client.
- Routes must use this service instead of manipulating Firestore
  directly.
"""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from models.session import Session

from services.firebase_service import (
    get_document,
    get_document_data,
    get_firestore_client,
    set_document_data,
)

from utils.ids import generate_session_id

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
# FIRESTORE
# ============================================================

SESSIONS_COLLECTION = "sessions"


# ============================================================
# SESSION STATES
# ============================================================

INITIAL_SESSION_STATE = "NEW"

COMPLETED_SESSION_STATE = "SESSION_COMPLETE"


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _validate_session(
    session: Session,
) -> None:
    """
    Validate that the supplied object is a Session instance.
    """

    if not isinstance(
        session,
        Session,
    ):
        raise TypeError(
            "session must be a Session instance."
        )


def _validate_new_state(
    new_state: str,
) -> str:
    """
    Validate and normalize a requested session state.
    """

    if not isinstance(
        new_state,
        str,
    ):
        raise TypeError(
            "new_state must be a string."
        )

    new_state = new_state.strip()

    if not new_state:
        raise ValueError(
            "new_state cannot be empty."
        )

    if len(new_state) > 128:
        raise ValueError(
            "new_state cannot exceed 128 characters."
        )

    return new_state


def _get_transaction():
    """
    Create a new Firestore transaction.

    A fresh transaction is intentionally created for each atomic
    read-modify-write operation.
    """

    client = get_firestore_client()

    return client.transaction()


# ============================================================
# CREATE SESSION
# ============================================================

def create_session(
    metadata: dict[str, Any] | None = None,
) -> Session:
    """
    Create a new Birthday Quest session.

    A UUID v4 session ID is generated server-side.

    The initial session is persisted before being returned.
    """

    if metadata is None:
        metadata = {}

    if not isinstance(
        metadata,
        dict,
    ):
        raise TypeError(
            "metadata must be a dictionary."
        )

    session_id = generate_session_id()

    now = utc_now_iso()

    session = Session(
        session_id=session_id,
        state=INITIAL_SESSION_STATE,
        created_at=now,
        updated_at=now,
        last_activity_at=now,
        completed_at=None,
        version=1,
        active=True,
        metadata=dict(metadata),
    )

    document = get_document(
        SESSIONS_COLLECTION,
        session.session_id,
    )

    # --------------------------------------------------------
    # Collision protection
    # --------------------------------------------------------
    #
    # UUID v4 collision is extraordinarily unlikely, but the
    # write still uses a transaction so that an already-existing
    # document can never silently be overwritten.
    #

    transaction = _get_transaction()

    snapshot = document.get(
        transaction=transaction
    )

    if snapshot.exists:
        raise RuntimeError(
            "A generated session identifier already exists. "
            "Please retry session creation."
        )

    transaction.set(
        document,
        session.to_dict(),
    )

    transaction.commit()

    log_info(
        logger,
        "session_created",
        session_id=session.session_id,
        state=session.state,
    )

    return session


# ============================================================
# GET SESSION
# ============================================================

def get_session(
    session_id: str,
) -> Session | None:
    """
    Retrieve a session by its ID.

    Returns None when the session does not exist.
    """

    data = get_document_data(
        SESSIONS_COLLECTION,
        session_id,
    )

    if data is None:
        return None

    return Session.from_dict(
        data
    )


# ============================================================
# RECOVER SESSION
# ============================================================

def recover_session(
    session_id: str,
) -> Session | None:
    """
    Recover an existing active session.

    Recovery updates activity information atomically.

    A completed or inactive session cannot be recovered.
    """

    document = get_document(
        SESSIONS_COLLECTION,
        session_id,
    )

    transaction = _get_transaction()

    snapshot = document.get(
        transaction=transaction
    )

    if not snapshot.exists:
        log_warning(
            logger,
            "session_not_found",
            session_id=session_id,
        )
        return None

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored session data is invalid."
        )

    session = Session.from_dict(
        data
    )

    if not session.active:
        log_warning(
            logger,
            "inactive_session_recovery_attempt",
            session_id=session.session_id,
            state=session.state,
        )
        return None

    if session.state == COMPLETED_SESSION_STATE:
        log_warning(
            logger,
            "completed_session_recovery_attempt",
            session_id=session.session_id,
        )
        return None

    now = utc_now_iso()

    next_version = session.version + 1

    transaction.update(
        document,
        {
            "updated_at": now,
            "last_activity_at": now,
            "version": next_version,
        },
    )

    transaction.commit()

    session.updated_at = now
    session.last_activity_at = now
    session.version = next_version

    log_info(
        logger,
        "session_recovered",
        session_id=session.session_id,
        state=session.state,
        version=session.version,
    )

    return session


# ============================================================
# UPDATE SESSION ACTIVITY
# ============================================================

def update_session_activity(
    session: Session,
) -> Session:
    """
    Atomically update the session's activity timestamp and
    increment its version.

    The persisted version must match the version supplied by the
    caller. This prevents stale session objects from silently
    overwriting newer session data.
    """

    _validate_session(
        session
    )

    if not session.active:
        raise ValueError(
            "Cannot update activity for an inactive session."
        )

    if session.state == COMPLETED_SESSION_STATE:
        raise ValueError(
            "Cannot update activity for a completed session."
        )

    document = get_document(
        SESSIONS_COLLECTION,
        session.session_id,
    )

    transaction = _get_transaction()

    snapshot = document.get(
        transaction=transaction
    )

    if not snapshot.exists:
        raise ValueError(
            "Session no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored session data is invalid."
        )

    persisted_session = Session.from_dict(
        data
    )

    if persisted_session.version != session.version:
        raise RuntimeError(
            "Session version conflict. "
            "The session was modified by another request."
        )

    if not persisted_session.active:
        raise ValueError(
            "The session is inactive."
        )

    if persisted_session.state == COMPLETED_SESSION_STATE:
        raise ValueError(
            "The session is already complete."
        )

    now = utc_now_iso()

    next_version = persisted_session.version + 1

    transaction.update(
        document,
        {
            "updated_at": now,
            "last_activity_at": now,
            "version": next_version,
        },
    )

    transaction.commit()

    session.updated_at = now
    session.last_activity_at = now
    session.version = next_version

    return session


# ============================================================
# UPDATE SESSION STATE
# ============================================================

def update_session_state(
    session: Session,
    new_state: str,
) -> Session:
    """
    Atomically change the session state.

    The persisted version must match the supplied Session object.

    This method does NOT decide whether the transition itself is
    legal. Quest progression rules belong to quest_service.py.
    """

    _validate_session(
        session
    )

    new_state = _validate_new_state(
        new_state
    )

    if not session.active:
        raise ValueError(
            "Cannot update an inactive session."
        )

    if session.state == COMPLETED_SESSION_STATE:
        raise ValueError(
            "A completed session cannot change state."
        )

    document = get_document(
        SESSIONS_COLLECTION,
        session.session_id,
    )

    transaction = _get_transaction()

    snapshot = document.get(
        transaction=transaction
    )

    if not snapshot.exists:
        raise ValueError(
            "Session no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored session data is invalid."
        )

    persisted_session = Session.from_dict(
        data
    )

    if persisted_session.version != session.version:
        raise RuntimeError(
            "Session version conflict. "
            "The session was modified by another request."
        )

    if not persisted_session.active:
        raise ValueError(
            "The session is inactive."
        )

    if persisted_session.state == COMPLETED_SESSION_STATE:
        raise ValueError(
            "A completed session cannot change state."
        )

    now = utc_now_iso()

    next_version = persisted_session.version + 1

    transaction.update(
        document,
        {
            "state": new_state,
            "updated_at": now,
            "last_activity_at": now,
            "version": next_version,
        },
    )

    transaction.commit()

    session.state = new_state
    session.updated_at = now
    session.last_activity_at = now
    session.version = next_version

    return session


# ============================================================
# COMPLETE SESSION
# ============================================================

def complete_session(
    session: Session,
) -> Session:
    """
    Atomically mark a session as complete and inactive.

    Calling this method on an already completed session simply
    returns the supplied session object.
    """

    _validate_session(
        session
    )

    if session.state == COMPLETED_SESSION_STATE:
        return session

    if not session.active:
        raise ValueError(
            "Session is already inactive."
        )

    document = get_document(
        SESSIONS_COLLECTION,
        session.session_id,
    )

    transaction = _get_transaction()

    snapshot = document.get(
        transaction=transaction
    )

    if not snapshot.exists:
        raise ValueError(
            "Session no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored session data is invalid."
        )

    persisted_session = Session.from_dict(
        data
    )

    if persisted_session.version != session.version:
        raise RuntimeError(
            "Session version conflict. "
            "The session was modified by another request."
        )

    if persisted_session.state == COMPLETED_SESSION_STATE:
        return Session.from_dict(
            data
        )

    if not persisted_session.active:
        raise ValueError(
            "Session is already inactive."
        )

    now = utc_now_iso()

    next_version = persisted_session.version + 1

    transaction.update(
        document,
        {
            "state": COMPLETED_SESSION_STATE,
            "active": False,
            "completed_at": now,
            "updated_at": now,
            "last_activity_at": now,
            "version": next_version,
        },
    )

    transaction.commit()

    session.state = COMPLETED_SESSION_STATE
    session.active = False
    session.completed_at = now
    session.updated_at = now
    session.last_activity_at = now
    session.version = next_version

    log_info(
        logger,
        "session_completed",
        session_id=session.session_id,
    )

    return session
