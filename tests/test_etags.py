import uuid

import pytest
from _pytest.logging import LogCaptureFixture
from flask import Blueprint, Flask, Response, jsonify
from flask.testing import FlaskClient

from flask_batteries_included import init_metrics, init_monitoring

test_blueprint = Blueprint("test", __name__)


@test_blueprint.route("/resource", methods=["GET"])
def get_resource() -> Response:
    return jsonify({"key": "value", "number": 5})


@test_blueprint.route("/resource", methods=["POST"])
def post_resource() -> Response:
    return jsonify({"key": "value", "number": 5})


@test_blueprint.route("/random", methods=["GET"])
def random_value() -> Response:
    return jsonify({"random_value": str(uuid.uuid4())})


@pytest.fixture(autouse=True)
def app_with_test(app: Flask) -> Flask:
    # Add the test paths to the app
    init_monitoring(app)
    init_metrics(app)
    app.register_blueprint(test_blueprint)
    return app


def test_etag_added(client: FlaskClient, caplog: LogCaptureFixture) -> None:
    """
    Tests that requests have an ETag in the response headers.
    """
    response = client.get("/resource")
    assert response.status_code == 200
    etag: str = response.headers["ETag"]
    assert etag is not None


def test_conditional_response_get(
    client: FlaskClient, caplog: LogCaptureFixture
) -> None:
    """
    Tests that unchanging responses coupled with an ETag in the request result in an empty 304 response.
    """
    response_1 = client.get("/resource")
    etag: str = response_1.headers["ETag"]
    assert response_1.status_code == 200
    assert response_1.json is not None
    assert "304 Not Modified" not in caplog.text
    response_2 = client.get("/resource", headers={"If-None-Match": etag})
    assert response_2.status_code == 304
    assert response_2.json is None
    assert "304 Not Modified" in caplog.text
    assert response_2.headers["ETag"] == etag


def test_conditional_response_post(
    client: FlaskClient, caplog: LogCaptureFixture
) -> None:
    """
    Tests that POST requests are not affected by ETags.
    """
    response_1 = client.post("/resource")
    etag: str = response_1.headers["ETag"]
    assert response_1.status_code == 200
    assert response_1.json is not None
    assert "304 Not Modified" not in caplog.text
    response_2 = client.post("/resource", headers={"If-None-Match": etag})
    assert response_2.status_code == 200
    assert response_2.json is not None
    assert "304 Not Modified" not in caplog.text


def test_conditional_response_changing(
    client: FlaskClient, caplog: LogCaptureFixture
) -> None:
    """
    Tests that differing responses do not result in a 304.
    """
    response_1 = client.get("/random")
    etag: str = response_1.headers["ETag"]
    assert response_1.status_code == 200
    assert response_1.json is not None
    assert "304 Not Modified" not in caplog.text
    response_2 = client.get("/random", headers={"If-None-Match": etag})
    assert response_2.status_code == 200
    assert response_2.json is not None
    assert "304 Not Modified" not in caplog.text
    assert response_2.headers["ETag"] != etag
