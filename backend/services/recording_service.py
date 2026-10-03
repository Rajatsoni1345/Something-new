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

IMPORTANT:
- The browser owns camera/microphone access and MediaRecorder.
- This service owns recording authorization, lifecycle state,
  metadata validation, Cloudinary upload, and verification.
- Permanent video files are stored in Cloudinary.
- Firestore stores metadata only.
- Render's filesystem is never used as permanent storage.
- Recording IDs are generated server-side.
- A recording belongs to exactly one session.
- Recording lifecycle operations are validated server-side.
- Uploads are designed to be retry-safe.
"""

from __future__ import annotations

from typing import Any

from models.recording import Recording
from models.session import Session

from services import cloudinary_service

from services.firebase_service import (
    get_document,
    get_document_data,
    get_firestore_client,
)

from services.quest_service import (
    STATE_BIRTHDAY_SCENE,
    STATE_CANDLE_TRIGGERED,
    STATE_FINAL_VIDEO_COMPLETED,
    STATE_REACTION_RECORDING,
    STATE_REACTION_UPLOAD,
    STATE_VIDEO_1_RECORDING,
    STATE_VIDEO_1_STOPPING,
    STATE_VIDEO_1_UPLOAD_PENDING,
    STATE_VIDEO_1_UPLOADED,
    STATE_VIDEO_1_VERIFIED,
    STATE_VIDEO_2_READY,
    STATE_VIDEO_2_RECORDING,
    transition_quest,
)

from services.validation_service import (
    validate_recording_content_type,
    validate_recording_duration,
    validate_recording_identifier,
    validate_recording_size,
    validate_recording_type,
    validate_session_identifier,
)

from utils.ids import generate_recording_id
from utils.logging import (
    get_logger,
    log_error,
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

RECORDINGS_COLLECTION = "recordings"


# ============================================================
# RECORDING TYPES
# ============================================================

RECORDING_TYPE_VIDEO_1 = "video_1"
RECORDING_TYPE_VIDEO_2 = "video_2"
RECORDING_TYPE_REACTION = "reaction"

ALLOWED_RECORDING_TYPES = frozenset(
    {
        RECORDING_TYPE_VIDEO_1,
        RECORDING_TYPE_VIDEO_2,
        RECORDING_TYPE_REACTION,
    }
)


# ============================================================
# RECORDING STATUSES
# ============================================================

STATUS_RECORDING = "recording"
STATUS_STOPPING = "stopping"
STATUS_UPLOAD_PENDING = "upload_pending"
STATUS_UPLOADING = "uploading"
STATUS_UPLOADED = "uploaded"
STATUS_VERIFIED = "verified"
STATUS_FAILED = "failed"


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_FOLDER = "birthday-quest/recordings"


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _get_recording_document(
    recording_id: str,
):
    """
    Return the Firestore document reference for a recording.
    """

    return get_document(
        RECORDINGS_COLLECTION,
        recording_id,
    )


def _get_transaction():
    """
    Create a Firestore transaction.
    """

    return get_firestore_client().transaction()


def _validate_session(
    session: Session,
) -> None:
    """
    Validate that a usable session object was supplied.
    """

    if not isinstance(
        session,
        Session,
    ):
        raise TypeError(
            "session must be a Session instance."
        )

    if not session.active:
        raise ValueError(
            "The session is inactive."
        )


def _validate_recording_type_for_service(
    recording_type: Any,
) -> str:
    """
    Validate and normalize recording type.
    """

    normalized = validate_recording_type(
        recording_type
    )

    if normalized not in ALLOWED_RECORDING_TYPES:
        raise ValueError(
            "Unsupported recording type."
        )

    return normalized


def _get_recording(
    recording_id: str,
) -> Recording | None:
    """
    Retrieve a recording from Firestore.
    """

    data = get_document_data(
        RECORDINGS_COLLECTION,
        recording_id,
    )

    if data is None:
        return None

    return Recording.from_dict(
        data
    )


def _validate_recording_ownership(
    recording: Recording,
    session: Session,
) -> None:
    """
    Ensure the recording belongs to the current session.
    """

    if recording.session_id != session.session_id:
        raise ValueError(
            "The recording does not belong to this session."
        )


def _validate_recording_version(
    supplied_recording: Recording,
    stored_recording: Recording,
) -> None:
    """
    Prevent stale recording objects from overwriting newer data.
    """

    if (
        supplied_recording.version
        != stored_recording.version
    ):
        raise RuntimeError(
            "Recording version conflict. "
            "The recording was modified by another request."
        )


def _build_cloudinary_public_id(
    recording_id: str,
) -> str:
    """
    Build the permanent Cloudinary public ID.

    The recording UUID remains the unique identifier.
    """

    recording_id = validate_recording_identifier(
        recording_id
    )

    return (
        f"{CLOUDINARY_FOLDER}/"
        f"{recording_id}"
    )


def _validate_upload_metadata(
    *,
    duration_ms: int | None,
    file_size_bytes: int | None,
    content_type: str | None,
) -> tuple[
    int | None,
    int | None,
    str | None,
]:
    """
    Validate optional upload metadata.

    The browser may supply these values, but the backend treats
    them as untrusted input.
    """

    validated_duration = None

    if duration_ms is not None:
        validated_duration = validate_recording_duration(
            duration_ms
        )

    validated_size = None

    if file_size_bytes is not None:
        validated_size = validate_recording_size(
            file_size_bytes
        )

    validated_content_type = None

    if content_type is not None:
        validated_content_type = (
            validate_recording_content_type(
                content_type
            )
        )

    return (
        validated_duration,
        validated_size,
        validated_content_type,
    )


def _validate_start_state(
    session: Session,
    recording_type: str,
) -> None:
    """
    Validate whether a recording of the requested type may
    start from the current quest/session state.

    Quest state itself is revalidated again by transition_quest()
    before the actual state change.
    """

    state = session.state

    if recording_type == RECORDING_TYPE_VIDEO_1:
        if state != STATE_BIRTHDAY_SCENE:
            raise ValueError(
                "Video 1 cannot be started from the current state."
            )
        return

    if recording_type == RECORDING_TYPE_VIDEO_2:
        if state != STATE_VIDEO_2_READY:
            raise ValueError(
                "Video 2 cannot be started from the current state."
            )
        return

    if recording_type == RECORDING_TYPE_REACTION:
        if state != STATE_FINAL_VIDEO_COMPLETED:
            raise ValueError(
                "Reaction recording cannot be started from the current state."
            )
        return

    raise ValueError(
        "Unsupported recording type."
    )


def _get_start_state(
    recording_type: str,
) -> str:
    """
    Return the quest state that represents an active recording.
    """

    mapping = {
        RECORDING_TYPE_VIDEO_1: STATE_VIDEO_1_RECORDING,
        RECORDING_TYPE_VIDEO_2: STATE_VIDEO_2_RECORDING,
        RECORDING_TYPE_REACTION: STATE_REACTION_RECORDING,
    }

    try:
        return mapping[recording_type]
    except KeyError as exc:
        raise ValueError(
            "Unsupported recording type."
        ) from exc


def _get_upload_pending_state(
    recording_type: str,
) -> str:
    """
    Return the quest state required before upload.
    """

    mapping = {
        RECORDING_TYPE_VIDEO_1: STATE_VIDEO_1_UPLOAD_PENDING,
        RECORDING_TYPE_VIDEO_2: STATE_VIDEO_2_RECORDING,
        RECORDING_TYPE_REACTION: STATE_REACTION_UPLOAD,
    }

    try:
        return mapping[recording_type]
    except KeyError as exc:
        raise ValueError(
            "Unsupported recording type."
        ) from exc


def _get_uploaded_state(
    recording_type: str,
) -> str | None:
    """
    Return the quest state after a successful upload.

    Video 2 intentionally remains in VIDEO_2_RECORDING until
    the later quest flow confirms the wall unlock transition.
    """

    mapping = {
        RECORDING_TYPE_VIDEO_1: STATE_VIDEO_1_UPLOADED,
        RECORDING_TYPE_VIDEO_2: None,
        RECORDING_TYPE_REACTION: None,
    }

    return mapping.get(
        recording_type
    )


def _get_verified_state(
    recording_type: str,
) -> str | None:
    """
    Return the quest state after Cloudinary verification.

    Only Video 1 has a dedicated verification state in the
    currently locked quest state machine.
    """

    mapping = {
        RECORDING_TYPE_VIDEO_1: STATE_VIDEO_1_VERIFIED,
        RECORDING_TYPE_VIDEO_2: None,
        RECORDING_TYPE_REACTION: None,
    }

    return mapping.get(
        recording_type
    )


# ============================================================
# CREATE / START RECORDING
# ============================================================

def start_recording(
    session: Session,
    recording_type: str,
) -> Recording:
    """
    Create and authorize a new recording.

    Flow:

        current quest state
                |
                v
        authorize recording
                |
                v
        create Firestore metadata
                |
                v
        transition quest state
                |
                v
        browser starts MediaRecorder

    The browser should only start recording after this function
    succeeds.
    """

    _validate_session(
        session
    )

    recording_type = (
        _validate_recording_type_for_service(
            recording_type
        )
    )

    _validate_start_state(
        session,
        recording_type,
    )

    recording_id = generate_recording_id()

    now = utc_now_iso()

    recording = Recording(
        recording_id=recording_id,
        session_id=session.session_id,
        recording_type=recording_type,
        status=STATUS_RECORDING,
        created_at=now,
        updated_at=now,
        cloudinary_public_id=None,
        secure_url=None,
        resource_type=None,
        duration_ms=None,
        file_size_bytes=None,
        content_type=None,
        completed_at=None,
        attempt=1,
        version=1,
        metadata={},
    )

    recording_document = _get_recording_document(
        recording_id
    )

    transaction = _get_transaction()

    snapshot = transaction.get(
        recording_document
    )

    if snapshot.exists:
        raise RuntimeError(
            "A generated recording identifier already exists. "
            "Please retry recording creation."
        )

    transaction.create(
        recording_document,
        recording.to_dict(),
    )

    transaction.commit()

    next_state = _get_start_state(
        recording_type
    )

    try:
        # The quest service performs server-side state
        # validation and version checks.
        from services.quest_service import (
            get_quest,
        )

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            raise ValueError(
                "Quest not found for this session."
            )

        transition_quest(
            session=session,
            quest=quest,
            next_state=next_state,
        )

    except Exception:
        # The recording metadata exists, but the quest transition
        # did not succeed. Mark the recording failed instead of
        # leaving a misleading active recording.
        try:
            fail_recording(
                session=session,
                recording_id=recording_id,
                reason="Quest state transition failed.",
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
        recording_id=recording.recording_id,
        recording_type=recording.recording_type,
    )

    return recording


# ============================================================
# STOP / MARK STOPPING
# ============================================================

def mark_recording_stopping(
    session: Session,
    recording_id: str,
) -> Recording:
    """
    Mark an active recording as stopping.

    This does not upload anything.

    The browser should:
        1. stop MediaRecorder
        2. create the final Blob
        3. send that Blob to the upload endpoint
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        raise ValueError(
            "Recording not found."
        )

    _validate_recording_ownership(
        recording,
        session,
    )

    if recording.status == STATUS_STOPPING:
        return recording

    if recording.status != STATUS_RECORDING:
        raise ValueError(
            "Only an active recording can be stopped."
        )

    transaction = _get_transaction()

    recording_document = _get_recording_document(
        recording_id
    )

    snapshot = transaction.get(
        recording_document
    )

    if not snapshot.exists:
        raise ValueError(
            "Recording no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored recording data is invalid."
        )

    stored_recording = Recording.from_dict(
        data
    )

    _validate_recording_ownership(
        stored_recording,
        session,
    )

    _validate_recording_version(
        recording,
        stored_recording,
    )

    if stored_recording.status == STATUS_STOPPING:
        return stored_recording

    if stored_recording.status != STATUS_RECORDING:
        raise ValueError(
            "Only an active recording can be stopped."
        )

    now = utc_now_iso()

    stored_recording.status = STATUS_STOPPING
    stored_recording.updated_at = now
    stored_recording.version += 1

    transaction.update(
        recording_document,
        stored_recording.to_dict(),
    )

    transaction.commit()

    recording.status = stored_recording.status
    recording.updated_at = stored_recording.updated_at
    recording.version = stored_recording.version

    # Video 1 has an explicit STOPPING state in the quest
    # state machine. Other recording types have their own
    # lifecycle states and are not forced through this state.
    if (
        recording.recording_type
        == RECORDING_TYPE_VIDEO_1
    ):
        from services.quest_service import get_quest

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            raise ValueError(
                "Quest not found for this session."
            )

        if quest.state == STATE_VIDEO_1_RECORDING:
            transition_quest(
                session=session,
                quest=quest,
                next_state=STATE_VIDEO_1_STOPPING,
            )

    log_info(
        logger,
        "recording_stopping",
        session_id=session.session_id,
        recording_id=recording.recording_id,
        recording_type=recording.recording_type,
    )

    return recording


# ============================================================
# PREPARE UPLOAD
# ============================================================

def mark_recording_upload_pending(
    session: Session,
    recording_id: str,
    *,
    duration_ms: int | None = None,
    file_size_bytes: int | None = None,
    content_type: str | None = None,
) -> Recording:
    """
    Mark a recording as ready for upload.

    This validates metadata but does not contact Cloudinary.

    Expected browser flow:

        MediaRecorder.stop()
                |
                v
        Blob created
                |
                v
        mark upload pending
                |
                v
        upload_recording()
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    (
        duration_ms,
        file_size_bytes,
        content_type,
    ) = _validate_upload_metadata(
        duration_ms=duration_ms,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
    )

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        raise ValueError(
            "Recording not found."
        )

    _validate_recording_ownership(
        recording,
        session,
    )

    if recording.status == STATUS_UPLOAD_PENDING:
        return recording

    if recording.status not in {
        STATUS_STOPPING,
        STATUS_RECORDING,
    }:
        raise ValueError(
            "The recording is not ready to enter the upload stage."
        )

    transaction = _get_transaction()

    recording_document = _get_recording_document(
        recording_id
    )

    snapshot = transaction.get(
        recording_document
    )

    if not snapshot.exists:
        raise ValueError(
            "Recording no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored recording data is invalid."
        )

    stored_recording = Recording.from_dict(
        data
    )

    _validate_recording_ownership(
        stored_recording,
        session,
    )

    _validate_recording_version(
        recording,
        stored_recording,
    )

    if stored_recording.status == STATUS_UPLOAD_PENDING:
        return stored_recording

    if stored_recording.status not in {
        STATUS_STOPPING,
        STATUS_RECORDING,
    }:
        raise ValueError(
            "The recording is not ready to enter the upload stage."
        )

    now = utc_now_iso()

    stored_recording.status = STATUS_UPLOAD_PENDING
    stored_recording.updated_at = now
    stored_recording.version += 1

    if duration_ms is not None:
        stored_recording.duration_ms = duration_ms

    if file_size_bytes is not None:
        stored_recording.file_size_bytes = file_size_bytes

    if content_type is not None:
        stored_recording.content_type = content_type

    transaction.update(
        recording_document,
        stored_recording.to_dict(),
    )

    transaction.commit()

    recording.status = stored_recording.status
    recording.updated_at = stored_recording.updated_at
    recording.version = stored_recording.version
    recording.duration_ms = stored_recording.duration_ms
    recording.file_size_bytes = stored_recording.file_size_bytes
    recording.content_type = stored_recording.content_type

    # Video 1 must explicitly reach UPLOAD_PENDING before
    # Cloudinary upload.
    if (
        recording.recording_type
        == RECORDING_TYPE_VIDEO_1
    ):
        from services.quest_service import get_quest

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            raise ValueError(
                "Quest not found for this session."
            )

        if quest.state == STATE_VIDEO_1_STOPPING:
            transition_quest(
                session=session,
                quest=quest,
                next_state=STATE_VIDEO_1_UPLOAD_PENDING,
            )

    log_info(
        logger,
        "recording_upload_pending",
        session_id=session.session_id,
        recording_id=recording.recording_id,
    )

    return recording


# ============================================================
# CLOUDINARY UPLOAD
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
    """
    Upload a recording to Cloudinary.

    This method is retry-safe at the application level:

    - If the recording is already verified, it returns the
      existing verified metadata.
    - If Cloudinary already contains the expected public ID,
      the existing asset is reused rather than creating another
      permanent asset.
    - Firestore remains the source of recording lifecycle state.
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    if file_object is None:
        raise ValueError(
            "file_object cannot be None."
        )

    (
        duration_ms,
        file_size_bytes,
        content_type,
    ) = _validate_upload_metadata(
        duration_ms=duration_ms,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
    )

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        raise ValueError(
            "Recording not found."
        )

    _validate_recording_ownership(
        recording,
        session,
    )

    if recording.status == STATUS_VERIFIED:
        return recording

    if recording.status not in {
        STATUS_UPLOAD_PENDING,
        STATUS_UPLOADING,
    }:
        raise ValueError(
            "The recording is not ready for upload."
        )

    # --------------------------------------------------------
    # Persist metadata before external upload.
    # --------------------------------------------------------

    transaction = _get_transaction()

    recording_document = _get_recording_document(
        recording_id
    )

    snapshot = transaction.get(
        recording_document
    )

    if not snapshot.exists:
        raise ValueError(
            "Recording no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored recording data is invalid."
        )

    stored_recording = Recording.from_dict(
        data
    )

    _validate_recording_ownership(
        stored_recording,
        session,
    )

    _validate_recording_version(
        recording,
        stored_recording,
    )

    if stored_recording.status == STATUS_VERIFIED:
        return stored_recording

    if stored_recording.status not in {
        STATUS_UPLOAD_PENDING,
        STATUS_UPLOADING,
    }:
        raise ValueError(
            "The recording is not ready for upload."
        )

    now = utc_now_iso()

    stored_recording.status = STATUS_UPLOADING
    stored_recording.updated_at = now
    stored_recording.version += 1

    if duration_ms is not None:
        stored_recording.duration_ms = duration_ms

    if file_size_bytes is not None:
        stored_recording.file_size_bytes = file_size_bytes

    if content_type is not None:
        stored_recording.content_type = content_type

    transaction.update(
        recording_document,
        stored_recording.to_dict(),
    )

    transaction.commit()

    recording.status = stored_recording.status
    recording.updated_at = stored_recording.updated_at
    recording.version = stored_recording.version
    recording.duration_ms = stored_recording.duration_ms
    recording.file_size_bytes = stored_recording.file_size_bytes
    recording.content_type = stored_recording.content_type

    # --------------------------------------------------------
    # Cloudinary
    # --------------------------------------------------------

    public_id = _build_cloudinary_public_id(
        recording_id
    )

    try:
        # First attempt to find an already uploaded asset.
        existing_asset = None

        try:
            existing_asset = (
                cloudinary_service.verify_video(
                    public_id
                )
            )
        except Exception:
            existing_asset = None

        if existing_asset:
            upload_result = existing_asset

            log_info(
                logger,
                "existing_cloudinary_asset_reused",
                session_id=session.session_id,
                recording_id=recording_id,
                public_id=public_id,
            )

        else:
            upload_result = (
                cloudinary_service.upload_video(
                    file_object=file_object,
                    public_id=recording_id,
                    folder=CLOUDINARY_FOLDER,
                )
            )

        returned_public_id = upload_result.get(
            "public_id"
        )

        secure_url = upload_result.get(
            "secure_url"
        )

        resource_type = upload_result.get(
            "resource_type"
        )

        if not returned_public_id:
            returned_public_id = public_id

        if not secure_url:
            raise RuntimeError(
                "Cloudinary did not return a secure URL."
            )

        if not isinstance(
            secure_url,
            str,
        ) or not secure_url.startswith(
            "https://"
        ):
            raise RuntimeError(
                "Cloudinary returned an invalid secure URL."
            )

        if resource_type != "video":
            raise RuntimeError(
                "Cloudinary returned an unexpected resource type."
            )

        # ----------------------------------------------------
        # Persist uploaded state.
        # ----------------------------------------------------

        transaction = _get_transaction()

        snapshot = transaction.get(
            recording_document
        )

        if not snapshot.exists:
            raise RuntimeError(
                "Recording disappeared during upload."
            )

        latest_data = snapshot.to_dict()

        if not isinstance(
            latest_data,
            dict,
        ):
            raise RuntimeError(
                "Stored recording data is invalid."
            )

        latest_recording = Recording.from_dict(
            latest_data
        )

        _validate_recording_ownership(
            latest_recording,
            session,
        )

        if latest_recording.status == STATUS_VERIFIED:
            return latest_recording

        now = utc_now_iso()

        latest_recording.cloudinary_public_id = (
            returned_public_id
        )

        latest_recording.secure_url = secure_url
        latest_recording.resource_type = resource_type
        latest_recording.status = STATUS_UPLOADED
        latest_recording.updated_at = now
        latest_recording.version += 1

        transaction.update(
            recording_document,
            latest_recording.to_dict(),
        )

        transaction.commit()

        recording.cloudinary_public_id = (
            latest_recording.cloudinary_public_id
        )
        recording.secure_url = (
            latest_recording.secure_url
        )
        recording.resource_type = (
            latest_recording.resource_type
        )
        recording.status = latest_recording.status
        recording.updated_at = latest_recording.updated_at
        recording.version = latest_recording.version

        # Video 1 explicitly advances to UPLOADED.
        if (
            recording.recording_type
            == RECORDING_TYPE_VIDEO_1
        ):
            from services.quest_service import get_quest

            quest = get_quest(
                session.session_id
            )

            if quest is None:
                raise ValueError(
                    "Quest not found for this session."
                )

            if quest.state == STATE_VIDEO_1_UPLOAD_PENDING:
                transition_quest(
                    session=session,
                    quest=quest,
                    next_state=STATE_VIDEO_1_UPLOADED,
                )

        log_info(
            logger,
            "recording_uploaded",
            session_id=session.session_id,
            recording_id=recording_id,
            public_id=returned_public_id,
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
        except Exception:
            log_error(
                logger,
                "recording_failure_persistence_failed",
                session_id=session.session_id,
                recording_id=recording_id,
            )

        raise


# ============================================================
# CLOUDINARY VERIFICATION
# ============================================================

def verify_recording(
    session: Session,
    recording_id: str,
) -> Recording:
    """
    Verify that the uploaded recording actually exists in
    Cloudinary as a video.

    Verification is separate from upload so the backend never
    assumes that a successful upload call alone is sufficient.
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        raise ValueError(
            "Recording not found."
        )

    _validate_recording_ownership(
        recording,
        session,
    )

    if recording.status == STATUS_VERIFIED:
        return recording

    if recording.status != STATUS_UPLOADED:
        raise ValueError(
            "Only an uploaded recording can be verified."
        )

    if not recording.cloudinary_public_id:
        raise ValueError(
            "The recording has no Cloudinary public ID."
        )

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

    secure_url = asset.get(
        "secure_url"
    )

    resource_type = asset.get(
        "resource_type"
    )

    if not secure_url:
        raise RuntimeError(
            "Verified Cloudinary asset has no secure URL."
        )

    if not isinstance(
        secure_url,
        str,
    ) or not secure_url.startswith(
        "https://"
    ):
        raise RuntimeError(
            "Verified Cloudinary asset returned an invalid URL."
        )

    if resource_type != "video":
        raise RuntimeError(
            "Verified Cloudinary asset is not a video."
        )

    transaction = _get_transaction()

    recording_document = _get_recording_document(
        recording_id
    )

    snapshot = transaction.get(
        recording_document
    )

    if not snapshot.exists:
        raise ValueError(
            "Recording no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored recording data is invalid."
        )

    stored_recording = Recording.from_dict(
        data
    )

    _validate_recording_ownership(
        stored_recording,
        session,
    )

    if stored_recording.status == STATUS_VERIFIED:
        return stored_recording

    if stored_recording.status != STATUS_UPLOADED:
        raise ValueError(
            "The recording is no longer in an uploadable verification state."
        )

    now = utc_now_iso()

    stored_recording.secure_url = secure_url
    stored_recording.resource_type = resource_type
    stored_recording.status = STATUS_VERIFIED
    stored_recording.completed_at = now
    stored_recording.updated_at = now
    stored_recording.version += 1

    transaction.update(
        recording_document,
        stored_recording.to_dict(),
    )

    transaction.commit()

    recording.secure_url = (
        stored_recording.secure_url
    )
    recording.resource_type = (
        stored_recording.resource_type
    )
    recording.status = stored_recording.status
    recording.completed_at = (
        stored_recording.completed_at
    )
    recording.updated_at = (
        stored_recording.updated_at
    )
    recording.version = stored_recording.version

    # Video 1 has a dedicated verified state.
    if (
        recording.recording_type
        == RECORDING_TYPE_VIDEO_1
    ):
        from services.quest_service import get_quest

        quest = get_quest(
            session.session_id
        )

        if quest is None:
            raise ValueError(
                "Quest not found for this session."
            )

        if quest.state == STATE_VIDEO_1_UPLOADED:
            transition_quest(
                session=session,
                quest=quest,
                next_state=STATE_VIDEO_1_VERIFIED,
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
    """
    Mark a recording as failed.

    Failure information is kept in metadata without exposing
    internal exception details to the frontend.
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    if not isinstance(
        reason,
        str,
    ):
        raise TypeError(
            "reason must be a string."
        )

    reason = reason.strip()

    if not reason:
        reason = "Recording operation failed."

    if len(reason) > 512:
        reason = reason[:512]

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        raise ValueError(
            "Recording not found."
        )

    _validate_recording_ownership(
        recording,
        session,
    )

    if recording.status == STATUS_VERIFIED:
        return recording

    transaction = _get_transaction()

    recording_document = _get_recording_document(
        recording_id
    )

    snapshot = transaction.get(
        recording_document
    )

    if not snapshot.exists:
        raise ValueError(
            "Recording no longer exists."
        )

    data = snapshot.to_dict()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Stored recording data is invalid."
        )

    stored_recording = Recording.from_dict(
        data
    )

    _validate_recording_ownership(
        stored_recording,
        session,
    )

    if stored_recording.status == STATUS_VERIFIED:
        return stored_recording

    now = utc_now_iso()

    metadata = dict(
        stored_recording.metadata
    )

    metadata["failure_reason"] = reason

    stored_recording.metadata = metadata
    stored_recording.status = STATUS_FAILED
    stored_recording.updated_at = now
    stored_recording.version += 1

    transaction.update(
        recording_document,
        stored_recording.to_dict(),
    )

    transaction.commit()

    recording.metadata = dict(
        stored_recording.metadata
    )
    recording.status = stored_recording.status
    recording.updated_at = stored_recording.updated_at
    recording.version = stored_recording.version

    log_warning(
        logger,
        "recording_failed",
        session_id=session.session_id,
        recording_id=recording_id,
    )

    return recording


# ============================================================
# RECORDING RETRIEVAL
# ============================================================

def get_recording(
    session: Session,
    recording_id: str,
) -> Recording | None:
    """
    Retrieve a recording only if it belongs to the supplied
    session.
    """

    _validate_session(
        session
    )

    recording_id = validate_recording_identifier(
        recording_id
    )

    recording = _get_recording(
        recording_id
    )

    if recording is None:
        return None

    _validate_recording_ownership(
        recording,
        session,
    )

    return recording


# ============================================================
# RECORDING TYPE HELPERS
# ============================================================

def is_video_1(
    recording: Recording,
) -> bool:
    return (
        isinstance(
            recording,
            Recording,
        )
        and recording.recording_type
        == RECORDING_TYPE_VIDEO_1
    )


def is_video_2(
    recording: Recording,
) -> bool:
    return (
        isinstance(
            recording,
            Recording,
        )
        and recording.recording_type
        == RECORDING_TYPE_VIDEO_2
    )


def is_reaction(
    recording: Recording,
) -> bool:
    return (
        isinstance(
            recording,
            Recording,
        )
        and recording.recording_type
        == RECORDING_TYPE_REACTION
    )


# ============================================================
# COMPLETION CHECK
# ============================================================

def is_verified(
    recording: Recording,
) -> bool:
    """
    Return whether the recording has completed the permanent
    Cloudinary verification lifecycle.
    """

    return (
        isinstance(
            recording,
            Recording,
        )
        and recording.status
        == STATUS_VERIFIED
        and bool(
            recording.cloudinary_public_id
        )
        and bool(
            recording.secure_url
        )
        and recording.resource_type
        == "video"
)
