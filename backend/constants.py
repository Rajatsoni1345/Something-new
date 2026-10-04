"""
Birthday Quest - Application Constants

Single source of truth for all magic strings, sets, and
configuration values shared across layers.

WHY THIS FILE EXISTS:
    Previously, constants like SESSION_COMPLETE were duplicated
    in session_service.py and quest_service.py, and
    ALLOWED_RECORDING_TYPES was inconsistent between
    validation_service.py and recording_service.py.

    This file prevents that class of bug permanently.
"""

from __future__ import annotations


# ============================================================
# SESSION STATES
# ============================================================

SESSION_STATE_NEW = "NEW"
SESSION_STATE_COMPLETE = "SESSION_COMPLETE"


# ============================================================
# QUEST STATES
# ============================================================

QUEST_STATE_NEW = "NEW"
QUEST_STATE_INTRO_COMPLETE = "INTRO_COMPLETE"
QUEST_STATE_GATE_ENTERED = "GATE_ENTERED"
QUEST_STATE_MAGIC_VERIFIED = "MAGIC_VERIFIED"
QUEST_STATE_BIRTHDAY_SCENE = "BIRTHDAY_SCENE"

QUEST_STATE_VIDEO_1_RECORDING = "VIDEO_1_RECORDING"
QUEST_STATE_CANDLE_TRIGGERED = "CANDLE_TRIGGERED"
QUEST_STATE_VIDEO_1_STOPPING = "VIDEO_1_STOPPING"
QUEST_STATE_VIDEO_1_UPLOAD_PENDING = "VIDEO_1_UPLOAD_PENDING"
QUEST_STATE_VIDEO_1_UPLOADED = "VIDEO_1_UPLOADED"
QUEST_STATE_VIDEO_1_VERIFIED = "VIDEO_1_VERIFIED"

QUEST_STATE_VIDEO_2_READY = "VIDEO_2_READY"
QUEST_STATE_VIDEO_2_RECORDING = "VIDEO_2_RECORDING"

QUEST_STATE_WALL_UNLOCKED = "WALL_UNLOCKED"
QUEST_STATE_COLLECTIBLES_COMPLETE = "COLLECTIBLES_COMPLETE"
QUEST_STATE_TICKET_COLLECTED = "TICKET_COLLECTED"
QUEST_STATE_TRAIN_COMPLETE = "TRAIN_COMPLETE"
QUEST_STATE_SORTING_COMPLETE = "SORTING_COMPLETE"

QUEST_STATE_LEVEL_1_COMPLETE = "LEVEL_1_COMPLETE"
QUEST_STATE_LEVEL_2_COMPLETE = "LEVEL_2_COMPLETE"
QUEST_STATE_LEVEL_3_COMPLETE = "LEVEL_3_COMPLETE"
QUEST_STATE_LEVEL_4_COMPLETE = "LEVEL_4_COMPLETE"

QUEST_STATE_FINAL_REVEAL = "FINAL_REVEAL"
QUEST_STATE_FINAL_VIDEO_STARTED = "FINAL_VIDEO_STARTED"
QUEST_STATE_FINAL_VIDEO_COMPLETED = "FINAL_VIDEO_COMPLETED"

QUEST_STATE_REACTION_RECORDING = "REACTION_RECORDING"
QUEST_STATE_REACTION_UPLOAD = "REACTION_UPLOAD"

QUEST_STATE_SESSION_COMPLETE = "SESSION_COMPLETE"


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

RECORDING_STATUS_RECORDING = "recording"
RECORDING_STATUS_STOPPING = "stopping"
RECORDING_STATUS_UPLOAD_PENDING = "upload_pending"
RECORDING_STATUS_UPLOADING = "uploading"
RECORDING_STATUS_UPLOADED = "uploaded"
RECORDING_STATUS_VERIFIED = "verified"
RECORDING_STATUS_FAILED = "failed"

ALLOWED_RECORDING_STATUSES = frozenset(
    {
        RECORDING_STATUS_RECORDING,
        RECORDING_STATUS_STOPPING,
        RECORDING_STATUS_UPLOAD_PENDING,
        RECORDING_STATUS_UPLOADING,
        RECORDING_STATUS_UPLOADED,
        RECORDING_STATUS_VERIFIED,
        RECORDING_STATUS_FAILED,
    }
)


# ============================================================
# RECORDING LIMITS
# ============================================================

MAX_RECORDING_DURATION_MS = 30 * 60 * 1000          # 30 min
MAX_RECORDING_FILE_SIZE_BYTES = 250 * 1024 * 1024   # 250 MB

ALLOWED_RECORDING_CONTENT_TYPES = frozenset(
    {
        "video/webm",
        "video/mp4",
        "video/quicktime",
        "video/x-matroska",
        "video/ogg",
    }
)


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_FOLDER = "birthday-quest/recordings"


# ============================================================
# FIRESTORE COLLECTIONS
# ============================================================

FIRESTORE_COLLECTION_SESSIONS = "sessions"
FIRESTORE_COLLECTION_QUESTS = "quests"
FIRESTORE_COLLECTION_RECORDINGS = "recordings"
FIRESTORE_COLLECTION_AUDIT = "audit_events"


# ============================================================
# COLLECTIBLES
# ============================================================

COLLECTIBLE_OWL = "owl"
COLLECTIBLE_WAND = "wand"
COLLECTIBLE_BROOM = "broom"

ALLOWED_COLLECTIBLE_ITEMS = frozenset(
    {
        COLLECTIBLE_OWL,
        COLLECTIBLE_WAND,
        COLLECTIBLE_BROOM,
    }
)


# ============================================================
# QUEST LEVELS
# ============================================================

MIN_NORMAL_QUEST_LEVEL = 1
MAX_NORMAL_QUEST_LEVEL = 4

NORMAL_QUEST_LEVELS = frozenset(
    {1, 2, 3, 4}
)


# ============================================================
# REQUEST LIMITS
# ============================================================

MAX_SESSION_ID_LENGTH = 128
MAX_RECORDING_ID_LENGTH = 128
MAX_ANSWER_LENGTH = 512
MAX_WORD_LENGTH = 128
MAX_ITEM_ID_LENGTH = 128
MAX_FAILURE_REASON_LENGTH = 512
MAX_GENERIC_STRING_LENGTH = 512
MAX_METADATA_KEYS = 32
