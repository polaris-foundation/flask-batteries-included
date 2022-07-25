import logging
import os
from typing import Any, Dict, Generator
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from flask import Blueprint, Flask, Response, jsonify

from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import scopes_present

app_protected_routes = Blueprint("protected_routes", __name__)

os.environ["ENVIRONMENT"] = "DEVELOPMENT"


@app_protected_routes.route("/secured_development")
@protected_route(scopes_present(required_scopes="hello:world"))
def app_secured_development() -> Response:
    """Decorated in dev environment, tests can toggle security on/off"""
    return jsonify({"result": True})


os.environ["ENVIRONMENT"] = "PRODUCTION"


@app_protected_routes.route("/secured_production")
@protected_route(scopes_present(required_scopes="hello:world"))
def app_secured_production() -> Response:
    """Decorated in production environment, security is always enabled"""
    return jsonify({"result": True})


os.environ["ENVIRONMENT"] = "DEVELOPMENT"


@pytest.fixture
def app_protected(app: Flask) -> None:
    app.register_blueprint(app_protected_routes)


@pytest.fixture
def mock_bearer_authorization(jwt_scopes: str) -> Dict:
    from jose import jwt

    claims = {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1_516_239_022,
        "iss": "http://localhost/",
        "scope": jwt_scopes,
    }
    token = jwt.encode(claims, "secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ignore_validation(
    app: Flask, request: Any, mocker: Any
) -> Generator[bool, None, None]:
    saved = app.config["IGNORE_JWT_VALIDATION"]
    app.config["IGNORE_JWT_VALIDATION"] = request.param
    yield request.param
    app.config["IGNORE_JWT_VALIDATION"] = saved


@pytest.mark.parametrize(
    "endpoint,ignore_validation,jwt_scopes,expect_status",
    [
        ("/secured_development", True, "foo:bar", 200),
        ("/secured_development", False, "foo:bar", 403),
        ("/secured_development", True, "hello:world", 200),
        ("/secured_development", False, "hello:world", 200),
        ("/secured_production", True, "foo:bar", 403),
        ("/secured_production", False, "foo:bar", 403),
        ("/secured_production", True, "hello:world", 200),
        ("/secured_production", False, "hello:world", 200),
    ],
    indirect=["ignore_validation"],
)
def test_protection(
    client: Any,
    caplog: LogCaptureFixture,
    app_protected: None,
    mock_bearer_authorization: Mock,
    endpoint: str,
    ignore_validation: bool,
    jwt_scopes: str,
    expect_status: int,
) -> None:
    with caplog.at_level(logging.DEBUG):
        response = client.get(endpoint, headers=mock_bearer_authorization)

    assert response.status_code == expect_status

    if expect_status == 200 and not ignore_validation:
        assert caplog.text == "", "Expected no jwt logging on security success"

    if expect_status == 200:
        assert response.json == {"result": True}
    else:
        assert "missing required scopes: ['hello:world']" in caplog.text
