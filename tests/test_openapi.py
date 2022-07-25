from datetime import datetime
from pathlib import Path

import pytest
import yaml
from _pytest.logging import LogCaptureFixture
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Blueprint, Flask, Response, jsonify, make_response
from flask.testing import FlaskClient
from marshmallow import EXCLUDE, Schema, fields

from flask_batteries_included import init_metrics, init_monitoring
from flask_batteries_included.helpers.apispec import (
    FlaskBatteriesPlugin,
    initialise_apispec,
    openapi_schema,
)
from flask_batteries_included.helpers.routes import deprecated_route

test_blueprint = Blueprint("test", __name__)
bad_blueprint = Blueprint("bad", __name__)


fbi_test_spec: APISpec = APISpec(
    version="1.0.0",
    openapi_version="3.0.3",
    title="FBI test",
    info={"description": "A service for testing our api spec generation"},
    plugins=[FlaskPlugin(), MarshmallowPlugin(), FlaskBatteriesPlugin()],
)

initialise_apispec(fbi_test_spec)


@test_blueprint.route("/undocumented", methods=["GET"])
def undocumented_route() -> Response:
    return make_response("", 204)


@openapi_schema(fbi_test_spec)
class ResponseSchema(Schema):
    class Meta:
        ordered = True
        unknown = EXCLUDE

    something = fields.Boolean(
        required=True, metadata={"description": "A flag", "example": True}
    )


@test_blueprint.route("/documented", methods=["GET"])
def documented_route() -> Response:
    """
    ---
    get:
      summary: Some route
      responses:
        '200':
          description: Some response
          content:
            application/json:
              schema: ResponseSchema
    """
    return jsonify({"something": True})


@test_blueprint.route("/deprecated", methods=["GET"])
@deprecated_route(superseded_by="GET /documented", deprecated=datetime(2020, 9, 23))
def deprecated_test_route() -> Response:
    """
    ---
    get:
      summary: Some route
      responses:
        '204':
          description: Some response
    """
    return make_response("", 204)


@pytest.fixture
def app_with_test(app: Flask) -> Flask:
    # Add the test paths to the app
    init_monitoring(app)
    init_metrics(app)
    app.register_blueprint(test_blueprint)
    return app


def test_openapi(
    tmp_path: str, app_with_test: Flask, caplog: LogCaptureFixture
) -> None:
    from flask_batteries_included.helpers.apispec import generate_openapi_spec

    new_spec_path = Path(tmp_path) / "testapi.yaml"

    spec: APISpec = APISpec(
        version="1.0.0",
        openapi_version="3.0.2",
        title="Test",
        info={"description": "unit test"},
        plugins=[FlaskPlugin(), MarshmallowPlugin(), FlaskBatteriesPlugin()],
    )

    generate_openapi_spec(spec, new_spec_path, test_blueprint)
    new_spec = yaml.safe_load(new_spec_path.read_bytes())

    assert new_spec["openapi"] == "3.0.2"
    assert sorted(new_spec["paths"]) == [
        "/deprecated",
        "/documented",
        "/running",
        "/version",
    ]
    assert new_spec["paths"]["/deprecated"]["get"]["deprecated"] is True
    assert "Skipping endpoint test.undocumented_route" in caplog.text
    assert (
        "Marking tests.test_openapi.deprecated_test_route as deprecated" in caplog.text
    )


def test_monitoring_endpoints(
    app_with_test: Flask,
    client: FlaskClient,
) -> None:
    with pytest.warns(DeprecationWarning) as record:
        response = client.get("/deprecated")

    message = record[0].message
    assert isinstance(message, Warning)
    assert (
        message.args[0]
        == "Endpoint deprecated_test_route is deprecated, use GET /documented"
    )
    assert response.status_code == 204
    assert response.headers["Deprecation"] == "2020-09-23T00:00:00.000+00:00"
    assert response.headers["Link"] == '</documented>; rel="successor-version"'
