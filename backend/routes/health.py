from flask import Blueprint
from ..middleware.errors import success_response

bp = Blueprint("health", __name__)

@bp.route("/api/v1/health", methods=["GET"])
def health():
    return success_response({"status": "alive", "magic": "flowing"})
