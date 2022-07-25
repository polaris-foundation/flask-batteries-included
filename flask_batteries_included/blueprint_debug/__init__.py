from flask import Blueprint, Response, jsonify, request

debug_blueprint = Blueprint("debug", __name__)


@debug_blueprint.route("/debug", methods=["GET"])
def get_debug_headers() -> Response:
    """
    Echoes request headers in the response.
    """
    return jsonify(dict(request.headers))
