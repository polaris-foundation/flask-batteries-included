from pathlib import Path

from flask import Blueprint, Flask, Response, jsonify
from healthcheck import HealthCheck

from flask_batteries_included.helpers.metrics import NO_METRICS_HEADER, set_no_metrics

healthcheck: HealthCheck = HealthCheck(
    success_headers={"Content-Type": "application/json", **NO_METRICS_HEADER}
)

app_monitor = Blueprint("app/monitor", __name__)


@app_monitor.route("/running")
def app_running() -> Response:
    """---
    get:
        summary: Verify service is running
        description: Verifies that the service is running. Used for monitoring in kubernetes.
        tags: ["monitoring"]
        responses:
            '200':
                description: "If we respond, we are running"
                content:
                    application/json:
                        schema:
                          type: object
                          properties:
                            running:
                                type: boolean
                                example: true
    """
    return set_no_metrics(jsonify({"running": True}))


@app_monitor.route("/version")
def app_version() -> Response:
    """---
    get:
        summary: Get version information
        description: Get the version number, circleci build number, and git hash.
        tags: ["monitoring"]
        responses:
            '200':
                description: "Version numbers"
                content:
                    application/json:
                        schema:
                          type: object
                          properties:
                            circle:
                                type: string
                                example: "1234"
                            hash:
                                type: string
                                example: "366c204"
    """
    file_to_data_map = {
        "circle": "build-circleci.txt",
        "hash": "build-githash.txt",
    }
    version = {}
    for key in file_to_data_map:
        try:
            version[key] = Path(f"/app/{file_to_data_map[key]}").read_text().strip()
        except OSError:
            version[key] = "unknown"
    return set_no_metrics(jsonify(version))


def init_monitoring(app: Flask) -> None:
    healthcheck.init_app(app_monitor, "/healthcheck")
    app.register_blueprint(app_monitor)
