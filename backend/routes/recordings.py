from flask import Blueprint, request
from ..middleware.errors import success_response, error_response
from ..services.recording_service import (
    mark_recording_start, mark_recording_stop, upload_recording
)
from ..utils.validation import is_valid_uuid

bp = Blueprint("recordings", __name__)

@bp.route("/api/v1/recordings/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    rtype = data.get("type")
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    r = mark_recording_start(sid, rtype)
    if "error" in r:
        return error_response(r["error"], 400)
    return success_response(r)

@bp.route("/api/v1/recordings/stop", methods=["POST"])
def stop():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    rtype = data.get("type")
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    r = mark_recording_stop(sid, rtype)
    if "error" in r:
        return error_response(r["error"], 400)
    return success_response(r)

@bp.route("/api/v1/recordings/upload", methods=["POST"])
def upload():
    sid = request.form.get("session_id")
    rtype = request.form.get("type")
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    if rtype not in ["video1", "reaction"]:
        return error_response("INVALID_TYPE", 400)
    if "video" not in request.files:
        return error_response("INVALID_REQUEST", 400)
    f = request.files["video"]
    r = upload_recording(sid, rtype, f)
    if "error" in r:
        return error_response(r["error"], 500)
    return success_response(r)
