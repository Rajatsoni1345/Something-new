from flask import Blueprint, request
from ..middleware.errors import success_response, error_response
from ..services.quest_service import submit_answer, collect_item, set_flag, set_scene
from ..utils.validation import is_valid_uuid, is_safe_answer

bp = Blueprint("quest", __name__)

@bp.route("/api/v1/quest/<sid>/answer", methods=["POST"])
def answer(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    data = request.get_json(silent=True) or {}
    level = data.get("level")
    ans = data.get("answer", "")
    if not isinstance(level, int) or not is_safe_answer(ans):
        return error_response("INVALID_REQUEST", 400)
    result = submit_answer(sid, level, ans)
    if "error" in result:
        return error_response(result["error"], 400)
    return success_response(result)

@bp.route("/api/v1/quest/<sid>/collect", methods=["POST"])
def collect(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    data = request.get_json(silent=True) or {}
    item = data.get("item")
    result = collect_item(sid, item)
    if "error" in result:
        return error_response(result["error"], 400)
    return success_response(result)

@bp.route("/api/v1/quest/<sid>/flag", methods=["POST"])
def flag(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    data = request.get_json(silent=True) or {}
    f = data.get("flag")
    v = bool(data.get("value", True))
    if not f:
        return error_response("INVALID_REQUEST", 400)
    result = set_flag(sid, f, v)
    if "error" in result:
        return error_response(result["error"], 400)
    return success_response(result)

@bp.route("/api/v1/quest/<sid>/scene", methods=["POST"])
def scene(sid):
    if not is_valid_uuid(sid):
        return error_response("SESSION_NOT_FOUND", 404)
    data = request.get_json(silent=True) or {}
    s = data.get("scene")
    if not s:
        return error_response("INVALID_REQUEST", 400)
    result = set_scene(sid, s)
    if "error" in result:
        return error_response(result["error"], 400)
    return success_response(result)
