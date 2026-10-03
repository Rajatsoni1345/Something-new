from flask import Blueprint, request
from ..config import Config
from ..middleware.errors import success_response, error_response
from ..services.session_service import list_sessions, get_session
from ..utils.validation import is_valid_uuid

bp = Blueprint("admin", __name__)

def _auth():
    token = request.headers.get("X-Admin-Token", "")
    return token == Config.ADMIN_TOKEN

@bp.route("/api/v1/admin/sessions", methods=["GET"])
def sessions():
    if not _auth():
        return error_response("UNAUTHORIZED", 401)
    return success_response({"sessions": list_sessions()})

@bp.route("/api/v1/admin/session/<sid>", methods=["GET"])
def session_detail(sid):
    if not _auth():
        return error_response("UNAUTHORIZED", 401)
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    s = get_session(sid)
    if not s:
        return error_response("SESSION_NOT_FOUND", 404)
    return success_response(s)
