import pytest
from flask import Blueprint, Flask, Response
from flask.testing import FlaskClient

from flask_batteries_included import init_metrics, init_monitoring
from flask_batteries_included.helpers.error_handler import (
    AuthMissingException,
    DuplicateResourceException,
    EntityNotFoundException,
    ServiceUnavailableException,
    UnprocessibleEntityException,
)

dummy_blueprint = Blueprint("dummy", __name__)


@dummy_blueprint.route("/entity_not_found", methods=["GET"])
def entity_not_found_route() -> Response:
    raise EntityNotFoundException


@dummy_blueprint.route("/value_error", methods=["GET"])
def value_error_route() -> Response:
    raise ValueError


@dummy_blueprint.route("/duplicate_resource", methods=["GET"])
def duplicate_resource_route() -> Response:
    raise DuplicateResourceException


@dummy_blueprint.route("/auth_missing", methods=["GET"])
def auth_missing_route() -> Response:
    raise AuthMissingException


@dummy_blueprint.route("/permission", methods=["GET"])
def permission_error_route() -> Response:
    raise PermissionError


@dummy_blueprint.route("/service_unavailable", methods=["GET"])
def service_unavailable_route() -> Response:
    raise ServiceUnavailableException


@dummy_blueprint.route("/unprocessible_entity", methods=["GET"])
def unprocessible_entity_route() -> Response:
    raise UnprocessibleEntityException


@pytest.fixture
def app_with_test(app: Flask) -> Flask:
    # Add the test paths to the app
    init_monitoring(app)
    init_metrics(app)
    app.register_blueprint(dummy_blueprint)
    return app


def test_value_error(app_with_test: Flask, client: FlaskClient) -> None:
    response = client.get(f"/value_error")
    assert response.status_code == 400


def test_auth_missing_exception(app_with_test: Flask, client: FlaskClient) -> None:
    response = client.get(f"/auth_missing")
    assert response.status_code == 401


def test_permission_error(app_with_test: Flask, client: FlaskClient) -> None:
    response = client.get(f"/permission")
    assert response.status_code == 403


def test_entity_not_found_exception(app_with_test: Flask, client: FlaskClient) -> None:
    response = client.get(f"/entity_not_found")
    assert response.status_code == 404


def test_duplicate_resource_exception(
    app_with_test: Flask, client: FlaskClient
) -> None:
    response = client.get(f"/duplicate_resource")
    assert response.status_code == 409


def test_unprocessible_entity_exception(
    app_with_test: Flask, client: FlaskClient
) -> None:
    response = client.get(f"/unprocessible_entity")
    assert response.status_code == 422


def test_service_unavailable_exception(
    app_with_test: Flask, client: FlaskClient
) -> None:
    response = client.get(f"/service_unavailable")
    assert response.status_code == 503
