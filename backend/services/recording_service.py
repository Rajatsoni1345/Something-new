import logging
from datetime import datetime, timezone
from .session_service import get_session, update_session
from .cloudinary_service import upload_video

logger = logging.getLogger(__name__)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def mark_recording_start(session_id, recording_type):
    if recording_type not in ["video1", "reaction"]:
        return {"error": "INVALID_TYPE"}
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    if recording_type == "reaction":
        if s["recordings"]["video1"]["status"] != "UPLOADED":
            return {"error": "VIDEO1_NOT_UPLOADED"}
    updates = {
        f"recordings.{recording_type}.status": "RECORDING",
        f"recordings.{recording_type}.startedAt": now_iso()
    }
    update_session(session_id, updates)
    logger.info(f"RECORDING_STARTED session={session_id} type={recording_type}")
    return {"state": get_session(session_id)}

def mark_recording_stop(session_id, recording_type):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    updates = {f"recordings.{recording_type}.status": "STOPPING"}
    update_session(session_id, updates)
    logger.info(f"RECORDING_STOPPED session={session_id} type={recording_type}")
    return {"state": get_session(session_id)}

def upload_recording(session_id, recording_type, file_obj):
    s = get_session(session_id)
    if not s:
        return {"error": "SESSION_NOT_FOUND"}
    
    existing = s["recordings"][recording_type]
    if existing.get("status") == "UPLOADED" and existing.get("url"):
        logger.info(f"UPLOAD_IDEMPOTENT session={session_id} type={recording_type}")
        return {"already_uploaded": True, "url": existing["url"], "state": s}
    
    update_session(session_id, {f"recordings.{recording_type}.status": "UPLOADING"})
    logger.info(f"UPLOAD_STARTED session={session_id} type={recording_type}")
    
    try:
        result = upload_video(file_obj, session_id, recording_type)
        updates = {
            f"recordings.{recording_type}.status": "UPLOADED",
            f"recordings.{recording_type}.url": result["secure_url"],
            f"recordings.{recording_type}.public_id": result["public_id"],
            f"recordings.{recording_type}.duration": result["duration"],
            f"recordings.{recording_type}.size": result["size"],
            f"recordings.{recording_type}.format": result["format"],
            f"recordings.{recording_type}.uploadedAt": now_iso(),
        }
        if recording_type == "video1":
            updates["recordings.reaction.status"] = "NOT_STARTED"
        if recording_type == "reaction":
            updates["completion.reactionCompleted"] = True
            updates["completion.completedAt"] = now_iso()
            updates["currentScene"] = "COMPLETE"
        
        update_session(session_id, updates)
        logger.info(f"UPLOAD_SUCCESS session={session_id} type={recording_type}")
        return {"url": result["secure_url"], "state": get_session(session_id)}
    except Exception as e:
        update_session(session_id, {f"recordings.{recording_type}.status": "FAILED"})
        logger.error(f"UPLOAD_FAILED session={session_id} type={recording_type} err={e}")
        return {"error": "UPLOAD_FAILED"}
