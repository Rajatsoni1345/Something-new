"""
Birthday Quest - Recording Service

Centralized recording lifecycle management.

Architecture:

    Browser MediaRecorder
            |
            v
    Recording Service
            |
            +---- Firestore -> recording metadata/status
            |
            +---- Cloudinary -> permanent video storage
            |
            v
    Quest State Machine

The browser owns camera/microphone access and MediaRecorder.
The backend owns authorization, lifecycle state, metadata
validation, Cloudinary storage, and verification.
"""

from __future__ import annotations

from typing import Any

from constants import (
    ALLOWED_RECORDING_CONTENT_TYPES,
    ALLOWED_RECORDING_TYPES,
    CLOUDINARY_FOLDER as CONST_CLOUDINARY_FOLDER,
    FIRESTORE_COLLECTION_RECORDINGS,
    MAX_RECORDING_DURATION_MS,
    MAX_RECORDING_FILE_SIZE_BYTES,
    QUEST_STATE_BIRTHDAY_SCENE,
    QUEST_STATE_FINAL_VIDEO_COMPLETED,
    QUEST_STATE_REACTION_RECORDING,
    QUEST_STATE_VIDEO_1_RECORDING,
    QUEST_STATE_VIDEO_1_STOPPING,
    QUEST_STATE_VIDEO_1_UPLOAD_PENDING,
    QUEST_STATE_VIDEO_1_UPLOADED,
    QUEST_STATE_VIDEO_1_VERIFIED,
    QUEST_STATE_VIDEO_2_READY,
    QUEST_STATE_VIDEO_2_RECORDING,
    RECORDING_STATUS_FAILED,
    RECORDING_STATUS_RECORDING,
    RECORDING_STATUS_STOPPING,
    RECORDING_STATUS_UPLOADED,
    RECORDING_STATUS_UPLOADING,
    RECORDING_STATUS_UPLOAD_PENDING,
    RECORDING_STATUS_VERIFIED,
    RECORDING_TYPE_REACTION,
    RECORDING_TYPE_VIDEO_1,
    RECORDING_TYPE_VIDEO_2,
    SESSION_STATE_COMPLETE,
)

from models.recording import Recording
from models.session import Session

from services import cloudinary_service
from services.firebase_service import (
    get_document,
    get_document_data,
    get_firestore_client,
)
from services.quest_service import (
    get_quest,
    transition_quest,
)
from services.session_service import get_session
from services.validation_service import (
    ValidationError,
    validate_recording_type,
    validate_session_id,
)

from utils.ids import generate_recording_id
from utils.logging import (
    get_logger,
    log_error,
    log_info,
    log_warning,
)
from utils.timestamps import utc_now_iso


logger = get_logger(__name__)


# ============================================================
# FIRESTORE
# ============================================================

RECORDINGS_COLLECTION = FIRESTORE_COLLECTION_RECORDINGS


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_FOLDER = CONST_CLOUDINARY_FOLDER


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================
#
# These remain for callers that were written against the earlier
# names. They all point to the same values defined in
# constants.py, so there is exactly one source of truth.
# ============================================================

ALLOWED_CONTENT_TYPES = ALLOWED_RECORDING_CONTENT_TYPES
MAX_DURATION_MS = MAX_RECORDING_DURATION_MS
MAX_FILE_SIZE_BYTES = MAX_RECORDING_FILE_SIZE_BYTES


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_recording_document(recording_id: str):
    return get_document(RECORDINGS_COLLECTION, recording_id)


def _get_transaction():
    return get_firestore_client().transaction()


def _validate_session(session: Session) -> None:
    if not isinstance(session, Session):
        raise TypeError("session must be a Session instance.")

    validate_session_id(session.session_id)

    if not session.active:
        raise ValueError("The session is inactive.")

    if session.state == SESSION_STATE_COMPLETE:
        raise ValueError("The session is already complete.")


def _validate_recording_type_for_service(recording_type: Any) -> str:
    try:
        normalized = validate_recording_type(recording_type)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    if normalized not in ALLOWED_RECORDING_TYPES:
        raise ValueError("Unsupported recording type.")

    return normalized


def _validate_recording_id(recording_id: Any) -> str:
    if not isinstance(recording_id, str):
        raise ValueError("recording_id must be a string.")

    recording_id = recording_id.strip()

    if not recording_id:
        raise ValueError("recording_id is required.")

    if len(recording_id) > 128:
        raise ValueError("recording_id is too long.")

    return recording_id


def _get_recording(recording_id: str) -> Recording | None:
    data = get_document_data(RECORDINGS_COLLECTION, recording_id)

    if data is None:
        return None

    return Recording.from_dict(data)


def _validate_recording_ownership(
    recording: Recording,
    session: Session,
) -> None:
    if recording.session_id != session.session_id:
        raise ValueError(
            "The recording does not belong to this session."
        )


def _validate_recording_version(
    supplied_recording: Recording,
    stored_recording: Recording,
) -> None:
    if supplied_recording.version != stored_recording.version:
        raise RuntimeError(
            "Recording version conflict. "
            "The recording was modified by another request."
        )


def _build_cloudinary_public_id(recording_id: str) -> str:
    recording_id = _validate_recording_id(recording_id)
    return f"{CLOUDINARY_FOLDER}/{recording_id}"


def _validate_upload_metadata(
    *,
    duration_ms: int | None,
    file_size_bytes: int | None,
    content_type: str | None,
) -> tuple[int | None, int | None, str | None]:

    if duration_ms is not None:
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int):
            raise ValueError("duration_ms must be an integer.")

        if duration_ms <= 0:
            raise ValueError("duration_ms must be greater than zero.")

        if duration_ms > MAX_DURATION_MS:
            raise ValueError(
                "Recording duration exceeds the allowed limit."
            )

    if file_size_bytes is not None:
        if isinstance(file_size_bytes, bool) or not isinstance(
            file_size_bytes, int
        ):
            raise ValueError("file_size_bytes must be an integer.")

        if file_size_bytes <= 0:
            raise ValueError(
                "file_size_bytes must be greater than zero."
            )

        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                "Recording file exceeds the allowed size."
            )

    normalized_content_type = None

    if content_type is not None:
        if not isinstance(content_type, str):
            raise ValueError("content_type must be a string.")

        normalized_content_type = content_type.strip().lower()

        if normalized_content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                "Unsupported recording content type."
            )

    return duration_ms, file_size_bytes, normalized_content_type


def _get_start_state(recording_type: str) -> str:
    mapping = {
        RECORDING_TYPE_VIDEO_1: QUEST_STATE_VIDEO_1_RECORDING,
        RECORDING_TYPE_VIDEO_2: QUEST_STATE_VIDEO_2_RECORDING,
        RECORDING_TYPE_REACTION: QUEST_STATE_REACTION_RECORDING,
    }

    try:
        return mapping[recording_type]
    except KeyError as exc:
        raise ValueError("Unsupported recording type.") from exc


def _get_required_source_state(recording_type: str) -> str:
    """
    Source-of-truth state from which a recording may begin.

    NOTE:
        We validate against the QUEST state (not the session
        state), because the quest state is the authoritative
        source of progression. Session state is kept in sync,
        but must never be the deciding factor.
    """
    mapping = {
        RECORDING_TYPE_VIDEO_1: QUEST_STATE_BIRTHDAY_SCENE,
        RECORDING_TYPE_VIDEO_2: QUEST_STATE_VIDEO_2_READY,
        RECORDING_TYPE_REACTION: QUEST_STATE_FINAL_VIDEO_COMPLETED,
    }

    try:
        return mapping[recording_type]
    except KeyError as exc:
        raise ValueError("Unsupported recording type.") from exc


def _validate_start_state_from_quest(
    quest_state: str,
    recording_type: str,
) -> None:
    required = _get_required_source_state(recording_type)

    if quest_state != required:
        raise ValueError(
            f"{recording_type} cannot be started from state "
            f"{quest_state!r}. Expected {required!r}."
        )


def _update_recording_after_transaction(
    target: Recording,
    source: Recording,
) -> Recording:
    target.status = source.status
    target.updated_at = source.updated_at
    target.version = source.version
    target.cloudinary_public_id = source.cloudinary_public_id
    target.secure_url = source.secure_url
    target.resource_type = source.resource_type
    target.duration_ms = source.duration_ms
    target.file_size_bytes = source.file_size_bytes
    target.content_type = source.content_type
    target.completed_at = source.completed_at
    target.metadata = dict(source.metadata)

    return target


# ============================================================
# START RECORDING
# ============================================================

def start_recording(
    session_id: str,
    recording_type: str,
) -> Recording:
    """
    Create a new recording for the given session.

    Signature note:
        The session is loaded inside this function from
        session_id. This keeps the API layer thin and lets
        tests mock a single, simple call signature.

    Raises:
        ValueError: session not found, inactive, or wrong state
        RuntimeError: transient Firestore conflict
    """

    session_id = validate_session_id(session_id)
    recording_type = _validate_recording_type_for_service(recording_type)

    session = get_session(session_id)

    if session is None:
        raise ValueError("Session not found.")

    _validate_session(session)

    quest = get_quest(session.session_id)

    if quest is None:
        raise ValueError("Quest not found for this session.")

    _validate_start_state_from_quest(quest.state, recording_type)

    recording_id = generate_recording_id()
    now = utc_now_iso()

    recording = Recording(
        recording_id=recording_id,
        session_id=session.session_id,
        recording_type=recording_type,
        status=RECORDING_STATUS_RECORDING,
        created_at=now,
        updated_at=now,
    )

    recording_document = _get_recording_document(recording_id)

    transaction = _get_transaction()

    snapshot = transaction.get(recording_document)

    if snapshot.exists:
        raise RuntimeError(
            "Generated recording ID already exists."
        )

    transaction.create(recording_document, recording.to_dict())

    transaction.commit()

    try:
        transition_quest(
            session=session,
            quest=quest,
            next_state=_get_start_state(recording_type),
        )
    except Exception:
        try:
            mark_recording_failed(
                session=session,
                recording_id=recording_id,
                reason="Quest transition failed.",
            )
        except Exception:
            log_error(
                logger,
                "recording_cleanup_failed",
                session_id=session.session_id,
                recording_id=recording_id,
            )
        raise

    log_info(
        logger,
        "recording_started",
        session_id=session.session_id,
        recording_id=recording_id,
        recording_type=recording_type,
    )

    return recording


# ============================================================
# STOP RECORDING
# ============================================================

def mark_recording_stopping(
    session: Session,
    recording_id: str,
) -> Recording:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    recording = _get_recording(recording_id)

    if recording is None:
        raise ValueError("Recording not found.")

    _validate_recording_ownership(recording, session)

    if recording.status == RECORDING_STATUS_STOPPING:
        return recording

    if recording.status != RECORDING_STATUS_RECORDING:
        raise ValueError("Only an active recording can be stopped.")

    recording_document = _get_recording_document(recording_id)
    transaction = _get_transaction()
    snapshot = transaction.get(recording_document)

    if not snapshot.exists:
        raise ValueError("Recording no longer exists.")

    data = snapshot.to_dict()

    if not isinstance(data, dict):
        raise RuntimeError("Stored recording data is invalid.")

    stored = Recording.from_dict(data)

    _validate_recording_ownership(stored, session)
    _validate_recording_version(recording, stored)

    if stored.status == RECORDING_STATUS_STOPPING:
        return stored

    if stored.status != RECORDING_STATUS_RECORDING:
        raise ValueError("Only an active recording can be stopped.")

    now = utc_now_iso()

    stored.status = RECORDING_STATUS_STOPPING
    stored.updated_at = now
    stored.version += 1

    transaction.update(recording_document, stored.to_dict())
    transaction.commit()

    _update_recording_after_transaction(recording, stored)

    if recording.recording_type == RECORDING_TYPE_VIDEO_1:
        quest = get_quest(session.session_id)

        if quest is None:
            raise ValueError("Quest not found for this session.")

        if quest.state == QUEST_STATE_VIDEO_1_RECORDING:
            transition_quest(
                session=session,
                quest=quest,
                next_state=QUEST_STATE_VIDEO_1_STOPPING,
            )

    log_info(
        logger,
        "recording_stopping",
        session_id=session.session_id,
        recording_id=recording_id,
    )

    return recording


# ============================================================
# UPLOAD PENDING
# ============================================================

def mark_recording_upload_pending(
    session: Session,
    recording_id: str,
    *,
    duration_ms: int | None = None,
    file_size_bytes: int | None = None,
    content_type: str | None = None,
) -> Recording:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    duration_ms, file_size_bytes, content_type = _validate_upload_metadata(
        duration_ms=duration_ms,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
    )

    recording = _get_recording(recording_id)

    if recording is None:
        raise ValueError("Recording not found.")

    _validate_recording_ownership(recording, session)

    if recording.status == RECORDING_STATUS_UPLOAD_PENDING:
        return recording

    if recording.status not in {
        RECORDING_STATUS_RECORDING,
        RECORDING_STATUS_STOPPING,
    }:
        raise ValueError("Recording is not ready for upload.")

    recording_document = _get_recording_document(recording_id)
    transaction = _get_transaction()
    snapshot = transaction.get(recording_document)

    if not snapshot.exists:
        raise ValueError("Recording no longer exists.")

    data = snapshot.to_dict()

    if not isinstance(data, dict):
        raise RuntimeError("Stored recording data is invalid.")

    stored = Recording.from_dict(data)

    _validate_recording_ownership(stored, session)
    _validate_recording_version(recording, stored)

    if stored.status == RECORDING_STATUS_UPLOAD_PENDING:
        return stored

    if stored.status not in {
        RECORDING_STATUS_RECORDING,
        RECORDING_STATUS_STOPPING,
    }:
        raise ValueError("Recording is not ready for upload.")

    now = utc_now_iso()

    stored.status = RECORDING_STATUS_UPLOAD_PENDING
    stored.updated_at = now
    stored.version += 1

    if duration_ms is not None:
        stored.duration_ms = duration_ms

    if file_size_bytes is not None:
        stored.file_size_bytes = file_size_bytes

    if content_type is not None:
        stored.content_type = content_type

    transaction.update(recording_document, stored.to_dict())
    transaction.commit()

    _update_recording_after_transaction(recording, stored)

    if recording.recording_type == RECORDING_TYPE_VIDEO_1:
        quest = get_quest(session.session_id)

        if quest is None:
            raise ValueError("Quest not found for this session.")

        if quest.state == QUEST_STATE_VIDEO_1_STOPPING:
            transition_quest(
                session=session,
                quest=quest,
                next_state=QUEST_STATE_VIDEO_1_UPLOAD_PENDING,
            )

    log_info(
        logger,
        "recording_upload_pending",
        session_id=session.session_id,
        recording_id=recording_id,
    )

    return recording


# ============================================================
# UPLOAD TO CLOUDINARY
# ============================================================

def upload_recording(
    session: Session,
    recording_id: str,
    file_object: Any,
    *,
    duration_ms: int | None = None,
    file_size_bytes: int | None = None,
    content_type: str | None = None,
) -> Recording:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    if file_object is None:
        raise ValueError("file_object cannot be None.")

    duration_ms, file_size_bytes, content_type = _validate_upload_metadata(
        duration_ms=duration_ms,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
    )

    recording = _get_recording(recording_id)

    if recording is None:
        raise ValueError("Recording not found.")

    _validate_recording_ownership(recording, session)

    if recording.status == RECORDING_STATUS_VERIFIED:
        return recording

    if recording.status not in {
        RECORDING_STATUS_UPLOAD_PENDING,
        RECORDING_STATUS_UPLOADING,
    }:
        raise ValueError("Recording is not ready for upload.")

    recording_document = _get_recording_document(recording_id)

    # Claim upload operation atomically.
    transaction = _get_transaction()
    snapshot = transaction.get(recording_document)

    if not snapshot.exists:
        raise ValueError("Recording no longer exists.")

    data = snapshot.to_dict()

    if not isinstance(data, dict):
        raise RuntimeError("Stored recording data is invalid.")

    stored = Recording.from_dict(data)

    _validate_recording_ownership(stored, session)

    if stored.status == RECORDING_STATUS_VERIFIED:
        return stored

    _validate_recording_version(recording, stored)

    if stored.status not in {
        RECORDING_STATUS_UPLOAD_PENDING,
        RECORDING_STATUS_UPLOADING,
    }:
        raise ValueError("Recording is not ready for upload.")

    now = utc_now_iso()

    stored.status = RECORDING_STATUS_UPLOADING
    stored.updated_at = now
    stored.version += 1

    if duration_ms is not None:
        stored.duration_ms = duration_ms

    if file_size_bytes is not None:
        stored.file_size_bytes = file_size_bytes

    if content_type is not None:
        stored.content_type = content_type

    transaction.update(recording_document, stored.to_dict())
    transaction.commit()

    _update_recording_after_transaction(recording, stored)

    public_id = _build_cloudinary_public_id(recording_id)

    try:
        upload_result = cloudinary_service.upload_video(
            file_object=file_object,
            public_id=recording_id,
            folder=CLOUDINARY_FOLDER,
        )

        if not isinstance(upload_result, dict):
            raise RuntimeError(
                "Cloudinary returned invalid upload data."
            )

        returned_public_id = upload_result.get("public_id") or public_id
        secure_url = upload_result.get("secure_url")
        resource_type = upload_result.get("resource_type")

        if not isinstance(secure_url, str) or not secure_url.startswith(
            "https://"
        ):
            raise RuntimeError(
                "Cloudinary returned an invalid secure URL."
            )

        if resource_type != "video":
            raise RuntimeError(
                "Cloudinary returned a non-video resource."
            )

        # Persist Cloudinary metadata.
        transaction = _get_transaction()
        snapshot = transaction.get(recording_document)

        if not snapshot.exists:
            raise RuntimeError("Recording disappeared during upload.")

        latest_data = snapshot.to_dict()

        if not isinstance(latest_data, dict):
            raise RuntimeError("Stored recording data is invalid.")

        latest = Recording.from_dict(latest_data)

        _validate_recording_ownership(latest, session)

        if latest.status == RECORDING_STATUS_VERIFIED:
            return latest

        if latest.status != RECORDING_STATUS_UPLOADING:
            raise RuntimeError(
                "Recording upload state changed unexpectedly."
            )

        latest.cloudinary_public_id = returned_public_id
        latest.secure_url = secure_url
        latest.resource_type = resource_type
        latest.status = RECORDING_STATUS_UPLOADED
        latest.updated_at = utc_now_iso()
        latest.version += 1

        transaction.update(recording_document, latest.to_dict())
        transaction.commit()

        _update_recording_after_transaction(recording, latest)

        if recording.recording_type == RECORDING_TYPE_VIDEO_1:
            quest = get_quest(session.session_id)

            if quest is None:
                raise ValueError("Quest not found for this session.")

            if quest.state == QUEST_STATE_VIDEO_1_UPLOAD_PENDING:
                transition_quest(
                    session=session,
                    quest=quest,
                    next_state=QUEST_STATE_VIDEO_1_UPLOADED,
                )

        log_info(
            logger,
            "recording_uploaded",
            session_id=session.session_id,
            recording_id=recording_id,
        )

        return recording

    except Exception as exc:
        log_error(
            logger,
            "recording_upload_failed",
            session_id=session.session_id,
            recording_id=recording_id,
            error=str(exc),
        )

        try:
            mark_recording_failed(
                session=session,
                recording_id=recording_id,
                reason="Cloudinary upload failed.",
            )
        except Exception as failure_exc:
            log_error(
                logger,
                "recording_failure_persistence_failed",
                session_id=session.session_id,
                recording_id=recording_id,
                error=str(failure_exc),
            )

        raise


# ============================================================
# VERIFY CLOUDINARY ASSET
# ============================================================

def verify_recording(
    session: Session,
    recording_id: str,
) -> Recording:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    recording = _get_recording(recording_id)

    if recording is None:
        raise ValueError("Recording not found.")

    _validate_recording_ownership(recording, session)

    if recording.status == RECORDING_STATUS_VERIFIED:
        return recording

    if recording.status != RECORDING_STATUS_UPLOADED:
        raise ValueError("Only an uploaded recording can be verified.")

    if not recording.cloudinary_public_id:
        raise ValueError("Recording has no Cloudinary public ID.")

    try:
        asset = cloudinary_service.verify_video(
            recording.cloudinary_public_id
        )
    except Exception as exc:
        log_error(
            logger,
            "recording_verification_failed",
            session_id=session.session_id,
            recording_id=recording_id,
            error=str(exc),
        )
        raise RuntimeError(
            "The recording could not be verified in Cloudinary."
        ) from exc

    if not isinstance(asset, dict):
        raise RuntimeError(
            "Cloudinary returned invalid verification data."
        )

    secure_url = asset.get("secure_url")
    resource_type = asset.get("resource_type")

    if not isinstance(secure_url, str) or not secure_url.startswith(
        "https://"
    ):
        raise RuntimeError(
            "Verified Cloudinary asset has an invalid URL."
        )

    if resource_type != "video":
        raise RuntimeError(
            "Verified Cloudinary asset is not a video."
        )

    recording_document = _get_recording_document(recording_id)
    transaction = _get_transaction()
    snapshot = transaction.get(recording_document)

    if not snapshot.exists:
        raise ValueError("Recording no longer exists.")

    data = snapshot.to_dict()

    if not isinstance(data, dict):
        raise RuntimeError("Stored recording data is invalid.")

    stored = Recording.from_dict(data)

    _validate_recording_ownership(stored, session)

    if stored.status == RECORDING_STATUS_VERIFIED:
        return stored

    if stored.status != RECORDING_STATUS_UPLOADED:
        raise ValueError(
            "Recording is no longer awaiting verification."
        )

    now = utc_now_iso()

    stored.secure_url = secure_url
    stored.resource_type = resource_type
    stored.status = RECORDING_STATUS_VERIFIED
    stored.completed_at = now
    stored.updated_at = now
    stored.version += 1

    transaction.update(recording_document, stored.to_dict())
    transaction.commit()

    _update_recording_after_transaction(recording, stored)

    if recording.recording_type == RECORDING_TYPE_VIDEO_1:
        quest = get_quest(session.session_id)

        if quest is None:
            raise ValueError("Quest not found for this session.")

        if quest.state == QUEST_STATE_VIDEO_1_UPLOADED:
            transition_quest(
                session=session,
                quest=quest,
                next_state=QUEST_STATE_VIDEO_1_VERIFIED,
            )

    log_info(
        logger,
        "recording_verified",
        session_id=session.session_id,
        recording_id=recording_id,
    )

    return recording


# ============================================================
# FAILURE HANDLING
# ============================================================

def mark_recording_failed(
    session: Session,
    recording_id: str,
    *,
    reason: str = "Recording operation failed.",
) -> Recording:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    if not isinstance(reason, str):
        raise TypeError("reason must be a string.")

    reason = reason.strip() or "Recording operation failed."
    reason = reason[:512]

    recording = _get_recording(recording_id)

    if recording is None:
        raise ValueError("Recording not found.")

    _validate_recording_ownership(recording, session)

    if recording.status == RECORDING_STATUS_VERIFIED:
        return recording

    recording_document = _get_recording_document(recording_id)
    transaction = _get_transaction()
    snapshot = transaction.get(recording_document)

    if not snapshot.exists:
        raise ValueError("Recording no longer exists.")

    data = snapshot.to_dict()

    if not isinstance(data, dict):
        raise RuntimeError("Stored recording data is invalid.")

    stored = Recording.from_dict(data)

    _validate_recording_ownership(stored, session)

    if stored.status == RECORDING_STATUS_VERIFIED:
        return stored

    metadata = dict(stored.metadata)
    metadata["failure_reason"] = reason

    stored.metadata = metadata
    stored.status = RECORDING_STATUS_FAILED
    stored.updated_at = utc_now_iso()
    stored.version += 1

    transaction.update(recording_document, stored.to_dict())
    transaction.commit()

    _update_recording_after_transaction(recording, stored)

    log_warning(
        logger,
        "recording_failed",
        session_id=session.session_id,
        recording_id=recording_id,
    )

    return recording


# ============================================================
# RETRIEVAL
# ============================================================

def get_recording(
    session: Session,
    recording_id: str,
) -> Recording | None:

    _validate_session(session)
    recording_id = _validate_recording_id(recording_id)

    recording = _get_recording(recording_id)

    if recording is None:
        return None

    _validate_recording_ownership(recording, session)

    return recording


# ============================================================
# TYPE HELPERS
# ============================================================

def is_video_1(recording: Recording) -> bool:
    return (
        isinstance(recording, Recording)
        and recording.recording_type == REC
