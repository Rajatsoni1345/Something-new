"""
Birthday Quest - Session Service

Business logic for creating, recovering, reading, updating, and
completing Birthday Quest sessions.

Storage architecture:
- Firebase Firestore -> session/state/metadata
- Cloudinary -> recorded videos and permanent media
- Render filesystem -> NEVER used for permanent recordings

This service only handles session data. It does not upload or
store video files.

IMPORTANT:
- All read-modify-write session operations use Firestore
  transactions.
- Session versions provide optimistic concurrency protection.
- Session IDs are generated server-side.
- A completed session becomes permanently inactive.
"""

from __future__ import annotations

from typing import Any

from models.session import Session

from services.firebase_service import (
    create_transaction,
    get_document,
    get_document_data,
    run_transaction,
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


def _validate_session_id(
    session_id: str,
) -> str:
    """
    Validate a session ID before using it in Firestore.
    """

    if not isinstance(
        session_id,
        str,
    ):
        raise TypeError(
            "session_id must be a string."
        )

    session_id = session_id.strip()

    if not session_id:
        raise ValueError(
            "session_id cannot be empty."
        )

    if "/" in session_id:
        raise ValueError(
            "session_id cannot contain '/'."
        )

    return session_id


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


def _get_session_document(
    session_id: str,
):
    """
    Return the Firestore document reference for a session.
    """

    session_id = _validate_session_id(
        session_id
    )

    return get_document(
        SESSIONS_COLLECTION,
        session_id,
    )


def _read_session_from_snapshot(
    snapshot,
) -> Session:
    """
    Convert a Firestore document snapshot into a Session model.
    """

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

    return Session.from_dict(
        data
    )


# ============================================================
# CREATE SESSION
# ============================================================

def create_session(
    metadata: dict[str, Any] | None = None,
) -> Session:
    """
    Create a new Birthday Quest session.

    A UUID v4 session ID is generated server-side.

    Firestore transaction creation guarantees that an existing
    document cannot be silently overwritten.

    In the extremely unlikely event of a generated-ID collision,
    a new ID is generated and the operation is retried.
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

    metadata_copy = dict(
        metadata
    )

    # --------------------------------------------------------
    # UUID collision retry.
    #
    # UUID v4 collisions are extraordinarily unlikely, but the
    # service still handles the condition explicitly rather than
    # overwriting an existing session.
    # --------------------------------------------------------

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1,
    ):
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
            metadata=metadata_copy,
        )

        document = _get_session_document(
            session.session_id
        )

        def create_operation(
            transaction,
        ):
            snapshot = transaction.get(
                document
            )

            if snapshot.exists:
                raise RuntimeError(
                    "SESSION_ID_COLLISION"
                )

            transaction.create(
                document,
                session.to_dict(),
            )

            return session

        try:
            created_session = run_transaction(
                create_operation
            )

        except RuntimeError as exc:
            if (
                str(exc) == "SESSION_ID_COLLISION"
                and attempt < max_attempts
            ):
                log_warning(
                    logger,
                    "session_id_collision",
                    attempt=attempt,
                )
                continue

            if (
                str(exc) == "SESSION_ID_COLLISION"
            ):
                raise RuntimeError(
                    "Unable to generate a unique session identifier."
                ) from exc

            raise

        log_info(
            logger,
            "session_created",
            session_id=created_session.session_id,
            state=created_session.state,
        )

        return created_session

    raise RuntimeError(
        "Unable to create a unique session."
    )


# ============================================================
# GET SESSION
# ============================================================

def get_session(
    session_id: str,
) -> Session | None:
    """
    Retrieve a session by ID.

    Returns None when the session does not exist.
    """

    session_id = _validate_session_id(
        session_id
    )

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

    session_id = _validate_session_id(
        session_id
    )

    document = _get_session_document(
        session_id
    )

    def recovery_operation(
        transaction,
    ):
        snapshot = transaction.get(
            document
        )

        if not snapshot.exists:
            return None

        session = _read_session_from_snapshot(
            snapshot
        )

        if not session.active:
            return None

        if session.state == COMPLETED_SESSION_STATE:
            return None

        now = utc_now_iso()

        next_version = (
            session.version + 1
        )

        transaction.update(
            document,
            {
                "updated_at": now,
                "last_activity_at": now,
                "version": next_version,
            },
        )

        session.updated_at = now
        session.last_activity_at = now
        session.version = next_version

        return session

    recovered_session = run_transaction(
        recovery_operation
    )

    if recovered_session is None:
        existing_session = get_session(
            session_id
        )

        if existing_session is None:
            log_warning(
                logger,
                "session_not_found",
                session_id=session_id,
            )
            return None

        if not existing_session.active:
            log_warning(
                logger,
                "inactive_session_recovery_attempt",
                session_id=existing_session.session_id,
                state=existing_session.state,
            )
            return None

        if (
            existing_session.state
            == COMPLETED_SESSION_STATE
        ):
            log_warning(
                logger,
                "completed_session_recovery_attempt",
                session_id=existing_session.session_id,
            )
            return None

        # This should only be reachable if the document changed
        # between transaction behavior and the follow-up read.
        return None

    log_info(
        logger,
        "session_recovered",
        session_id=recovered_session.session_id,
        state=recovered_session.state,
        version=recovered_session.version,
    )

    return recovered_session


# ============================================================
# UPDATE SESSION ACTIVITY
# ============================================================

def update_session_activity(
    session: Session,
) -> Session:
    """
    Atomically update session activity and increment its version.

    The persisted version must match the supplied Session version.
    This prevents a stale Session object from overwriting newer
    session data.
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

    document = _get_session_document(
        session.session_id
    )

    def activity_operation(
        transaction,
    ):
        snapshot = transaction.get(
            document
        )

        persisted_session = (
            _read_session_from_snapshot(
                snapshot
            )
        )

        if (
            persisted_session.version
            != session.version
        ):
            raise RuntimeError(
                "Session version conflict. "
                "The session was modified by another request."
            )

        if not persisted_session.active:
            raise ValueError(
                "The session is inactive."
            )

        if (
            persisted_session.state
            == COMPLETED_SESSION_STATE
        ):
            raise ValueError(
                "The session is already complete."
            )

        now = utc_now_iso()

        next_version = (
            persisted_session.version + 1
        )

        transaction.update(
            document,
            {
                "updated_at": now,
                "last_activity_at": now,
                "version": next_version,
            },
        )

        persisted_session.updated_at = now
        persisted_session.last_activity_at = now
        persisted_session.version = next_version

        return persisted_session

    updated_session = run_transaction(
        activity_operation
    )

    session.updated_at = (
        updated_session.updated_at
    )
    session.last_activity_at = (
        updated_session.last_activity_at
    )
    session.version = (
        updated_session.version
    )

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

    This function does not decide whether the requested state
    transition is legal. Quest progression rules belong to
    quest_service.py.
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

    document = _get_session_document(
        session.session_id
    )

    def state_operation(
        transaction,
    ):
        snapshot = transaction.get(
            document
        )

        persisted_session = (
            _read_session_from_snapshot(
                snapshot
            )
        )

        if (
            persisted_session.version
            != session.version
        ):
            raise RuntimeError(
                "Session version conflict. "
                "The session was modified by another request."
            )

        if not persisted_session.active:
            raise ValueError(
                "The session is inactive."
            )

        if (
            persisted_session.state
            == COMPLETED_SESSION_STATE
        ):
            raise ValueError(
                "A completed session cannot change state."
            )

        now = utc_now_iso()

        next_version = (
            persisted_session.version + 1
        )

        transaction.update(
            document,
            {
                "state": new_state,
                "updated_at": now,
                "last_activity_at": now,
                "version": next_version,
            },
        )

        persisted_session.state = new_state
        persisted_session.updated_at = now
        persisted_session.last_activity_at = now
        persisted_session.version = next_version

        return persisted_session

    updated_session = run_transaction(
        state_operation
    )

    session.state = (
        updated_session.state
    )
    session.updated_at = (
        updated_session.updated_at
    )
    session.last_activity_at = (
        updated_session.last_activity_at
    )
    session.version = (
        updated_session.version
    )

    return session


# ============================================================
# COMPLETE SESSION
# ============================================================

def complete_session(
    session: Session,
) -> Session:
    """
    Atomically mark a session as complete and inactive.

    Calling this function with an already-completed stored
    session is idempotent.

    A stale active Session object cannot overwrite a newer
    session state because version validation occurs inside
    the Firestore transaction.
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

    document = _get_session_document(
        session.session_id
    )

    def completion_operation(
        transaction,
    ):
        snapshot = transaction.get(
            document
        )

        persisted_session = (
            _read_session_from_snapshot(
                snapshot
            )
        )

        # ----------------------------------------------------
        # Idempotent completion.
        #
        # If another request completed the session before this
        # transaction committed, simply return the persisted
        # completed session.
        # ----------------------------------------------------

        if (
            persisted_session.state
            == COMPLETED_SESSION_STATE
        ):
            return persisted_session

        if (
            persisted_session.version
            != session.version
        ):
            raise RuntimeError(
                "Session version conflict. "
                "The session was modified by another request."
            )

        if not persisted_session.active:
            raise ValueError(
                "Session is already inactive."
            )

        now = utc_now_iso()

        next_version = (
            persisted_session.version + 1
        )

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

        persisted_session.state = (
            COMPLETED_SESSION_STATE
        )
        persisted_session.active = False
        persisted_session.completed_at = now
        persisted_session.updated_at = now
        persisted_session.last_activity_at = now
        persisted_session.version = next_version

        return persisted_session

    completed_session = run_transaction(
        completion_operation
    )

    session.state = (
        completed_session.state
    )
    session.active = (
        completed_session.active
    )
    session.completed_at = (
        completed_session.completed_at
    )
    session.updated_at = (
        completed_session.updated_at
    )
    session.last_activity_at = (
        completed_session.last_activity_at
    )
    session.version = (
        completed_session.version
    )

    log_info(
        logger,
        "session_completed",
        session_id=session.session_id,
        version=session.version,
    )

    return session
