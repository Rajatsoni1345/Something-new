from flask import Blueprint, request
from ..middleware.errors import success_response, error_response
from ..services.session_service import create_session, get_session, resume_session
from ..utils.validation import is_valid_uuid

bp = Blueprint("session", __name__)

@bp.route("/api/v1/session/create", methods=["POST"])
def create():
    s = create_session()
    return success_response(s, 201)

@bp.route("/api/v1/session/<sid>", methods=["GET"])
def get(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    s = get_session(sid)
    if not s:
        return error_response("SESSION_NOT_FOUND", 404)
    return success_response(s)

@bp.route("/api/v1/session/<sid>/resume", methods=["POST"])
def resume(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    s = resume_session(sid)
    if not s:
        return error_response("SESSION_NOT_FOUND", 404)
    return success_response(s)
