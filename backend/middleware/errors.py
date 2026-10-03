import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "SESSION_NOT_FOUND": "This magical session could not be found.",
    "LEVEL_LOCKED": "This part of the journey is not unlocked yet.",
    "WRONG_ANSWER": "The magic resists... try again.",
    "ALREADY_ANSWERED": "This level has already been completed.",
    "INVALID_ITEM": "That item doesn't belong here.",
    "INVALID_TYPE": "Invalid recording type.",
    "VIDEO1_NOT_UPLOADED": "The first recording must be uploaded first.",
    "UPLOAD_FAILED": "The magic connection flickered... Try again.",
    "INVALID_REQUEST": "The spell was malformed.",
    "UNAUTHORIZED": "You are not permitted here.",
    "NOT_FOUND": "The path does not exist.",
    "INTERNAL": "Something stirred in the darkness... Try again.",
}

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http(e):
        code = e.code or 500
        key = "NOT_FOUND" if code == 404 else "INTERNAL"
        return jsonify({
            "success": False,
            "error": {"code": key, "message": ERROR_MESSAGES.get(key, e.description)}
        }), code
    
    @app.errorhandler(Exception)
    def handle_generic(e):
        logger.exception(f"Unhandled error: {e}")
        return jsonify({
            "success": False,
            "error": {"code": "INTERNAL", "message": ERROR_MESSAGES["INTERNAL"]}
        }), 500

def error_response(code, status=400):
    return jsonify({
        "success": False,
        "error": {"code": code, "message": ERROR_MESSAGES.get(code, "Something went wrong.")}
    }), status

def success_response(data=None, status=200):
    return jsonify({"success": True, "data": data or {}}), status
