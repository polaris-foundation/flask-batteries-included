from typing import Any, Dict, List, Tuple, Union

from jose import jwt as jose_jwt
from she_logging import logger

from flask_batteries_included.helpers.security import jwk


class JwtParser:

    title: str = "Base"

    def __init__(
        self,
        required_audience: str,
        required_issuer: str,
        allowed_algorithms: List[str],
        metadata_key: str = "",
        scope_key: str = "",
        verify: bool = True,
    ):
        self.required_audience: str = required_audience
        self.required_issuer: str = required_issuer
        self.allowed_algorithms: List[str] = allowed_algorithms
        self.metadata_key: str = metadata_key
        self.scope_key: str = scope_key
        self.decode_options: Dict[
            str, Union[bool, int]
        ] = self._construct_verification_options(verify)

    def decode_jwt(
        self, jwt_token: str, unverified_header: Dict
    ) -> Tuple[Dict[str, str], List[str]]:
        raise NotImplementedError()

    def parse_access_token(
        self, access_token: Dict
    ) -> Tuple[Dict[str, Any], List[str]]:

        # Custom claims
        if self.metadata_key in access_token:
            claims = self.extract_claims_from_token(access_token)
        else:
            claims = {}

        # Standard claims
        if "iss" in access_token:
            claims["iss"] = access_token["iss"]

        if "sub" in access_token:
            claims["sub"] = access_token["sub"]

        # Custom scopes/permissions
        if self.scope_key in access_token:
            raw_scopes = access_token[self.scope_key]
            if not isinstance(raw_scopes, str):
                raise PermissionError("Invalid scopes (must be string)")
            scopes: List[str] = access_token[self.scope_key].split(" ")
        else:
            scopes = []

        return claims, scopes

    def extract_claims_from_token(self, access_token: dict) -> Dict[str, Any]:
        claims: dict = {"raw": access_token}

        for claim in access_token[self.metadata_key]:
            if claim == "locations":
                # Special case
                claims["location_ids"] = [
                    location["id"]
                    for location in access_token[self.metadata_key][claim]
                ]
                continue
            claims[claim] = access_token[self.metadata_key][claim]

        return claims

    @staticmethod
    def _construct_verification_options(
        verify: bool,
    ) -> Dict[str, Union[bool, int]]:
        return {
            "verify_signature": verify,
            "verify_aud": verify,
            "verify_iat": verify,
            "verify_exp": verify,
            "verify_nbf": verify,
            "verify_iss": verify,
            "verify_sub": verify,
            "verify_jti": verify,
            "leeway": 0,
        }

    def __str__(self) -> str:
        return "%s JwtParser with domain %s" % (self.title, self.required_issuer)


class InternalJwtParser(JwtParser):
    def __init__(
        self,
        required_audience: str,
        required_issuer: str,
        allowed_algorithms: List[str],
        metadata_key: str = "metadata",
        scope_key: str = "scope",
        verify: bool = True,
        hs_key: str = None,
        title: str = "Internal",
    ):
        self.title = title
        self.hs_key = hs_key
        super(InternalJwtParser, self).__init__(
            required_audience,
            required_issuer,
            allowed_algorithms,
            metadata_key,
            scope_key,
            verify,
        )

    def decode_jwt(
        self, jwt_token: str, unverified_header: Dict
    ) -> Tuple[Dict[str, str], List[str]]:
        access_token = jose_jwt.decode(
            jwt_token,
            self.hs_key,
            audience=self.required_audience,
            algorithms=self.allowed_algorithms,
            options=self.decode_options,
            issuer=self.required_issuer,
        )
        return self.parse_access_token(access_token)


class Auth0LoginJwtParser(JwtParser):
    title = "Auth0 login"

    def __init__(
        self,
        required_audience: str,
        required_issuer: str,
        allowed_algorithms: List[str],
        metadata_key: str = "",
        scope_key: str = "scope",
        verify: bool = True,
        hs_key: str = None,
    ):
        self.hs_key = hs_key
        super(Auth0LoginJwtParser, self).__init__(
            required_audience,
            required_issuer,
            allowed_algorithms,
            metadata_key,
            scope_key,
            verify,
        )

    def decode_jwt(
        self, jwt_token: str, unverified_header: Dict
    ) -> Tuple[dict, List[str]]:
        access_token = jose_jwt.decode(
            jwt_token,
            self.hs_key,
            audience=self.required_audience,
            algorithms=self.allowed_algorithms,
            options=self.decode_options,
            issuer=self.required_issuer,
        )
        return self.parse_access_token(access_token)


class Auth0JwtParser(JwtParser):
    title = "Auth0 standard"

    def __init__(
        self,
        required_audience: str,
        required_issuer: str,
        allowed_algorithms: List[str],
        metadata_key: str = "",
        scope_key: str = "scope",
        verify: bool = True,
    ):
        super(Auth0JwtParser, self).__init__(
            required_audience,
            required_issuer,
            allowed_algorithms,
            metadata_key,
            scope_key,
            verify,
        )

    def decode_jwt(
        self, jwt_token: str, unverified_header: Dict
    ) -> Tuple[Dict[str, Any], List[str]]:
        kid = unverified_header.get("kid", None)
        if kid is None:
            logger.warning("JWT provided with no kid field in header")
            raise ValueError("Could not retrieve JWT kid from header")

        jwks = jwk.retrieve_auth0_jwks(unverified_header)
        rsa_key = jwk.retrieve_relevant_jwk(jwks, unverified_header)

        if not rsa_key:
            logger.info("Could not retrieve JWT key from header: %s", unverified_header)
            raise ValueError("Could not retrieve JWT key from header")

        access_token = jose_jwt.decode(
            jwt_token,
            rsa_key,
            audience=self.required_audience,
            algorithms=self.allowed_algorithms,
            options=self.decode_options,
            issuer=self.required_issuer,
        )
        return self.parse_access_token(access_token)
