import json
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import requests
from flask import Flask, g
from flask.testing import FlaskClient
from jose import jwt as jose_jwt
from pytest_mock import MockFixture
from requests_mock.mocker import Mocker

from flask_batteries_included.helpers.security import jwt_parsers
from flask_batteries_included.helpers.security.jwt import (
    _add_system_jwt_to_headers,
    add_system_jwt_to_headers,
    current_jwt_user,
    decode_hs_jwt,
)
from flask_batteries_included.helpers.security.jwt_parsers import JwtParser

SAMPLE_JWT_EXPIRED = r"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJtZXRhZGF0YSI6eyJzeXN0ZW1faWQiOiJkaG9zLXJvYm90In0sImlzcyI6Imh0dHA6Ly9lcHIvIiwiYXVkIjoiaHR0cDovL2xvY2FsaG9zdC8iLCJzY29wZSI6IlNPTUVUSElORyIsImV4cCI6MTU0NDU0OTE5MH0.JhtT_lhOMM86otB2uNMX4bP4VFuxu-r0pyzSSIc4RS5N6gb-l4vaXLgIMXHxJ7q49jLG8KxLng4Vdr8FBmhVlA"


@pytest.mark.usefixtures("app_context")
@pytest.mark.parametrize(
    "user_id_key", ["clinician_id", "device_id", "patient_id", "system_id"]
)
def test_current_jwt_user_clinician(user_id_key: str) -> None:
    g.jwt_claims = {user_id_key: "12345"}
    assert current_jwt_user() == "12345"


@pytest.mark.usefixtures("app_context")
def test_current_jwt_user_invalid() -> None:
    g.jwt_claims = {"something_id": "12345"}
    assert current_jwt_user() == "unknown"


@patch.object(requests, "get")
def test_add_system_id_to_headers(mockget: Any) -> None:
    mockresponse = Mock()
    mockresponse.json.return_value = {"jwt": "SOMESORTOFJWT"}

    mockget.return_value = mockresponse

    assert _add_system_jwt_to_headers(
        {"Accept": "application/json"}, "a-system-id", "http://localhost:7000"
    ) == {"Accept": "application/json", "Authorization": "Bearer SOMESORTOFJWT"}


def test_add_system_id_to_headers2(app: Flask, requests_mock: Mocker) -> None:
    requests_mock.get(
        "http://localhost:7000/dhos/v1/system/my-system-id/jwt",
        json={"jwt": "SOMESORTOFJWT"},
    )

    headers = {"Accept": "application/json"}
    add_system_jwt_to_headers(headers, "my-system-id")
    assert headers == {
        "Accept": "application/json",
        "Authorization": "Bearer SOMESORTOFJWT",
    }


def test_decode_hs_jwt_expired() -> None:
    options: dict = JwtParser._construct_verification_options(True)
    decoded = decode_hs_jwt(
        hs_key="secret2",
        jwt_token=SAMPLE_JWT_EXPIRED,
        algorithms=["HS512"],
        decode_options=options,
    )

    assert decoded is None


TEST_JWKS = {
    "keys": [
        {"kid": "foo", "kty": "oct", "use": 123, "n": 42, "e": 65535, "k": "hello"}
    ]
}


@pytest.mark.parametrize(
    "redis_values,auth0_called", [({}, 1), ({"AUTH0_JWKS": json.dumps(TEST_JWKS)}, 0)]
)
def test_jwt_parser(
    client: FlaskClient,
    requests_mock: Mocker,
    mock_dhosredis: None,
    mocker: MockFixture,
    redis_values: Dict[str, str],
    auth0_called: int,
) -> None:
    audience = "http://localhost/"
    metadata_key: str = "metadata"
    issuer_to_verify: str = "http://epr/"

    auth0_mock: Any = requests_mock.get(
        "https://draysonhealth.eu.auth0.com/.well-known/jwks.json",
        text=json.dumps(TEST_JWKS),
    )

    jwt_parser: JwtParser = jwt_parsers.Auth0JwtParser(
        required_audience=audience,
        required_issuer=issuer_to_verify,
        allowed_algorithms=["HS512"],
        metadata_key=metadata_key,
        verify=True,
    )

    mocked_decode = mocker.patch.object(
        jose_jwt,
        "decode",
        return_value={"metadata": {"system_id": "pytest id"}, "scope": "SOMETHING"},
    )

    claims, scopes = jwt_parser.decode_jwt(
        jwt_token=r"a.b.c", unverified_header={"kid": "foo"}
    )

    assert "system_id" in claims
    assert scopes == ["SOMETHING"]
    assert json.loads(redis_values["AUTH0_JWKS"]) == TEST_JWKS
    assert auth0_mock.call_count == auth0_called


def test_connexion_bearer_auth_success() -> None:
    from flask_batteries_included.helpers.security.connexion_bearerinfo import (
        decode_bearer_token,
    )

    decoded = decode_bearer_token(SAMPLE_JWT_EXPIRED)
    assert decoded == {
        "metadata": {"system_id": "dhos-robot"},
        "iss": "http://epr/",
        "aud": "http://localhost/",
        "scope": "SOMETHING",
        "exp": 1544549190,
    }


def test_connexion_bearer_auth_permission_error() -> None:
    from flask_batteries_included.helpers.security.connexion_bearerinfo import (
        decode_bearer_token,
    )

    with pytest.raises(PermissionError):
        decode_bearer_token("FOO.BAR")


@pytest.mark.usefixtures("app")
@pytest.mark.parametrize("claims", [None, {}, {"unknown": "key"}])
def test_connexion_bearer_auth_fails(claims: Any) -> None:
    g.jwt_claims = claims
    assert current_jwt_user() == "unknown"
