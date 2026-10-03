import uuid
import logging
from datetime import datetime, timezone
from .firebase_service import get_db

logger = logging.getLogger(__name__)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def create_session():
    session_id = str(uuid.uuid4())
    doc = {
        "sessionId": session_id,
        "createdAt": now_iso(),
        "lastSeenAt": now_iso(),
        "currentScene": "INTRO",
        "currentLevel": 0,
        "quest": {
            "level": 0,
            "unlockedLevels": [1],
            "answers": {},
            "collectedWords": [],
            "collectibles": {"owl": False, "wand": False, "broom": False},
        },
        "recordings": {
            "video1": {"status": "NOT_STARTED", "url": None, "public_id": None},
            "reaction": {"status": "NOT_STARTED", "url": None, "public_id": None},
        },
        "completion": {
            "questCompleted": False,
            "finalVideoCompleted": False,
            "reactionCompleted": False,
            "completedAt": None,
        },
        "permissions": {"camera": False, "microphone": False},
        "flags": {
            "gateOpened": False,
            "spellCast": False,
            "candleBlown": False,
            "wallOpened": False,
            "ticketCollected": False,
            "hatSorted": False,
        },
    }
    get_db().collection("sessions").document(session_id).set(doc)
    logger.info(f"SESSION_CREATED {session_id}")
    return doc

def get_session(session_id):
    doc = get_db().collection("sessions").document(session_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()

def update_session(session_id, updates):
    updates["lastSeenAt"] = now_iso()
    get_db().collection("sessions").document(session_id).update(updates)
    return get_session(session_id)

def resume_session(session_id):
    s = get_session(session_id)
    if not s:
        return None
    update_session(session_id, {"lastSeenAt": now_iso()})
    return s

def list_sessions():
    docs = get_db().collection("sessions").stream()
    return [d.to_dict() for d in docs]
