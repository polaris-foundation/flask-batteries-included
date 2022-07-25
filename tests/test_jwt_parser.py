import uuid
from typing import Any, Dict, List, Optional

import pytest
from _pytest.logging import LogCaptureFixture
from jose import jwt as jose_jwt
from pytest_mock import MockFixture

from flask_batteries_included.helpers.security import jwk
from flask_batteries_included.helpers.security.jwt_parsers import (
    Auth0JwtParser,
    Auth0LoginJwtParser,
    InternalJwtParser,
    JwtParser,
)


class TestParsers:

    metadata_key = "http://source.uri/metadata"
    scope_key = "http://source.uri/scope"
    audience_issuer = "http://audience.uri/"
    allowed_algos = ["HS256"]

    hs_key = "secret"
    audience = "audience"
    issuer = "issuer"
    claims = {"aud": audience, "iss": issuer, "subdict": {}}

    @pytest.fixture
    def any_jwt_parser(self) -> JwtParser:
        return JwtParser(
            required_audience=self.audience_issuer,
            required_issuer=self.audience_issuer,
            metadata_key=self.metadata_key,
            scope_key=self.scope_key,
            allowed_algorithms=self.allowed_algos,
        )

    @pytest.fixture
    def internal_jwt_parser(self) -> InternalJwtParser:
        return InternalJwtParser(
            required_audience=self.audience,
            required_issuer=self.issuer,
            allowed_algorithms=["HS256"],
            metadata_key="subdict",
            scope_key="scope",
            verify=True,
            hs_key=self.hs_key,
        )

    @pytest.fixture
    def auth0_login_jwt_parser(self, mocker: MockFixture) -> Auth0LoginJwtParser:
        return Auth0LoginJwtParser(
            required_audience=self.audience,
            required_issuer=self.issuer,
            allowed_algorithms=["HS256"],
            metadata_key="subdict",
            scope_key="scope",
            verify=True,
            hs_key=self.hs_key,
        )

    @pytest.fixture
    def auth0_jwt_parser(self, mocker: MockFixture) -> Auth0JwtParser:
        mocker.patch.object(jwk, "retrieve_auth0_jwks", return_value={})
        mocker.patch.object(jwk, "retrieve_relevant_jwk", return_value=None)
        return Auth0JwtParser(
            required_audience=self.audience,
            required_issuer=self.issuer,
            allowed_algorithms=["HS256"],
            metadata_key="subdict",
            scope_key="scope",
            verify=True,
        )

    @pytest.fixture
    def scopes(self) -> str:
        return "read:foo write:foo"

    @pytest.fixture
    def access_token(self, scopes: Optional[str]) -> Dict[str, Any]:
        access_token = {
            "sub": "user:12345",
            "iss": "https://test.issuer.com/",
            self.metadata_key: {
                "clinician_id": "2543e23e-957e-4c85-8408-bff3dd0f775d",
                "locations": [
                    {"id": "L1", "name": "FlorenceWard"},
                    {"id": "L2", "name": "SouthWard"},
                ],
                "job_title": "Chief Carpal Tunnel Sufferer",
                "can_edit_ews": True,
            },
        }
        if scopes is not None:
            access_token[self.scope_key] = scopes

        return access_token

    def test_verification_options_true(self, any_jwt_parser: JwtParser) -> None:
        assert any_jwt_parser._construct_verification_options(True) == {
            "verify_signature": True,
            "verify_aud": True,
            "verify_iat": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iss": True,
            "verify_sub": True,
            "verify_jti": True,
            "leeway": 0,
        }

    def test_verification_options_false(self, any_jwt_parser: JwtParser) -> None:
        assert any_jwt_parser._construct_verification_options(False) == {
            "verify_signature": False,
            "verify_aud": False,
            "verify_iat": False,
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iss": False,
            "verify_sub": False,
            "verify_jti": False,
            "leeway": 0,
        }

    @pytest.mark.parametrize(
        "scopes,expected_scopes",
        [
            (None, []),
            ("read:foo", ["read:foo"]),
            ("read:foo write:foo", ["read:foo", "write:foo"]),
        ],
    )
    def test_parse_access_token(
        self,
        any_jwt_parser: JwtParser,
        access_token: Dict[str, Any],
        expected_scopes: List[str],
    ) -> None:

        parsed, parsed_scopes = any_jwt_parser.parse_access_token(access_token)

        assert parsed["clinician_id"] == "2543e23e-957e-4c85-8408-bff3dd0f775d"
        assert parsed["location_ids"] == ["L1", "L2"]
        assert parsed["can_edit_ews"] is True
        assert parsed["job_title"] == "Chief Carpal Tunnel Sufferer"
        assert parsed["raw"] == access_token
        assert parsed["sub"] == "user:12345"
        assert parsed["iss"] == "https://test.issuer.com/"
        assert parsed_scopes == expected_scopes

    def test_parse_access_token_custom_scope_key(self, mocker: MockFixture) -> None:
        mocker.patch.object(jwk, "retrieve_auth0_jwks", return_value={})
        mocker.patch.object(jwk, "retrieve_relevant_jwk", return_value=None)
        auth0_jwt_parser = Auth0JwtParser(
            required_audience=self.audience,
            required_issuer=self.issuer,
            allowed_algorithms=["HS256"],
            metadata_key="dummy",
            scope_key="permissions",
            verify=True,
        )
        access_token = {
            "sub": "user:12345",
            "iss": "https://test.issuer.com/",
            "permissions": "read:something write:something",
        }
        parsed, parsed_scopes = auth0_jwt_parser.parse_access_token(access_token)

        assert parsed["sub"] == "user:12345"
        assert parsed_scopes == ["read:something", "write:something"]

    @pytest.mark.parametrize("scopes", [(["read:foo", "write:foo"],)])
    def test_parse_invalid_scope(
        self, any_jwt_parser: JwtParser, access_token: Dict[str, Any]
    ) -> None:
        with pytest.raises(PermissionError):
            any_jwt_parser.parse_access_token(access_token)

    def test_internal_parse(self, internal_jwt_parser: InternalJwtParser) -> None:
        token: str = jose_jwt.encode(claims=self.claims, key=self.hs_key)
        claims, scopes = internal_jwt_parser.decode_jwt(
            jwt_token=token, unverified_header={}
        )
        assert claims["iss"] == self.issuer

    def test_internal_parse_unsigned(
        self, internal_jwt_parser: InternalJwtParser
    ) -> None:
        token: str = jose_jwt.encode(claims=self.claims, key="whoops")
        with pytest.raises(jose_jwt.JWTError):
            internal_jwt_parser.decode_jwt(jwt_token=token, unverified_header={})

    def test_auth0_login_parse(
        self, auth0_login_jwt_parser: Auth0LoginJwtParser, caplog: LogCaptureFixture
    ) -> None:
        token: str = jose_jwt.encode(
            claims=self.claims, key=self.hs_key, algorithm=self.allowed_algos[0]
        )
        unverified_header = jose_jwt.get_unverified_header(token)

        claims, scope = auth0_login_jwt_parser.decode_jwt(
            jwt_token=token, unverified_header=unverified_header
        )
        assert claims["iss"] == self.issuer

    @pytest.mark.usefixtures("app")
    def test_auth0_parse_missing_jwk(
        self, auth0_jwt_parser: Auth0JwtParser, caplog: LogCaptureFixture
    ) -> None:
        token: str = jose_jwt.encode(claims=self.claims, key=self.hs_key)
        with pytest.raises(ValueError):
            auth0_jwt_parser.decode_jwt(
                jwt_token=token, unverified_header={"kid": "12345"}
            )
        assert "Could not retrieve JWT key from header" in caplog.text

    @pytest.mark.usefixtures("app")
    def test_auth0_parse_missing_kid(
        self, auth0_jwt_parser: Auth0JwtParser, caplog: LogCaptureFixture
    ) -> None:
        token: str = jose_jwt.encode(claims=self.claims, key=self.hs_key)
        with pytest.raises(ValueError):
            auth0_jwt_parser.decode_jwt(jwt_token=token, unverified_header={})
        assert "JWT provided with no kid field in header" in caplog.text

    def test_must_subclass(self, any_jwt_parser: JwtParser) -> None:
        with pytest.raises(NotImplementedError):
            any_jwt_parser.decode_jwt("token", {})

    def test_str(
        self,
        any_jwt_parser: JwtParser,
        internal_jwt_parser: InternalJwtParser,
        auth0_jwt_parser: Auth0JwtParser,
        auth0_login_jwt_parser: Auth0LoginJwtParser,
    ) -> None:
        assert (
            str(any_jwt_parser) == f"Base JwtParser with domain {self.audience_issuer}"
        )
        assert str(internal_jwt_parser) == f"Internal JwtParser with domain issuer"
        assert str(auth0_jwt_parser) == f"Auth0 standard JwtParser with domain issuer"
        assert (
            str(auth0_login_jwt_parser) == f"Auth0 login JwtParser with domain issuer"
        )

    def test_all_claims_are_parsed(
        self,
        any_jwt_parser: JwtParser,
        access_token: Dict[str, Any],
    ) -> None:

        referring_device_id: str = str(uuid.uuid4())
        some_another_id: str = str(uuid.uuid4())
        access_token[self.metadata_key] = {
            **access_token[self.metadata_key],
            "referring_device_id": referring_device_id,
            "some_another_id": some_another_id,
        }

        parsed, _ = any_jwt_parser.parse_access_token(access_token)

        assert parsed["clinician_id"] == "2543e23e-957e-4c85-8408-bff3dd0f775d"
        assert parsed["location_ids"] == ["L1", "L2"]
        assert parsed["referring_device_id"] == referring_device_id
        assert parsed["some_another_id"] == some_another_id
