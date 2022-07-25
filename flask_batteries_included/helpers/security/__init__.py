import os
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from flask import current_app, g, request
from jose import jwt as jose_jwt
from she_logging import logger

from flask_batteries_included.config import is_production_environment
from flask_batteries_included.helpers.security.endpoint_security import compare_keys
from flask_batteries_included.helpers.security.jwt_parsers import JwtParser

from . import connexion_bearerinfo, jwt_parsers

# TODO: this should be removed with our refactoring of the identifiers module.
SYSTEM_UUIDS: List[str] = [
    "dhos-robot",
    "dhos-activation-auth-adapter-worker",
    "dhos-aggregator-adapter-worker",
    "dhos-audit-adapter-worker",
    "dhos-connector-adapter-worker",
    "dhos-encounters-adapter-worker",
    "dhos-messages-adapter-worker",
    "dhos-notifications-adapter-worker",
    "dhos-observations-adapter-worker",
    "dhos-pdf-adapter-worker",
    "dhos-questions-adapter-worker",
    "dhos-rules-adapter-worker",
    "dhos-services-api",
    "dhos-services-adapter-worker",
    "dhos-sms-adapter-worker",
    "gdm-bg-readings-adapter-worker",
]


class _ProtectedRoute:
    def __init__(
        self,
        validation_function: Callable = None,
        verify: bool = True,
        allowed_issuers: Union[List[Optional[str]], str, None] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        self.hs_key: Optional[str] = None
        self.claims_map: dict = kwargs
        self.verify: bool = verify

        # allowed_issuers is allowed to be a string or a list of strings
        if isinstance(allowed_issuers, str):
            allowed_issuers = [allowed_issuers]
        self.allowed_issuers: Optional[List[Optional[str]]] = allowed_issuers

        self.validation_function: Callable = validation_function or compare_keys
        self.ignore_jwt_validation: Optional[bool] = None

    def __call__(self, f: Callable) -> Callable:
        if is_production_environment():
            validator = self._call_validation
        else:
            validator = self._call_validation_development

        @wraps(f)
        def decorated(*args: List[Any], **kwargs: Dict[str, Any]) -> Callable:
            validator(self.verify, **kwargs)
            return f(*args, **kwargs)

        def _fbi_apispec(operation: Dict) -> None:
            if hasattr(f, "_fbi_apispec"):
                f._fbi_apispec(operation)  # type:ignore
            operation["security"] = [{"bearerAuth": []}]

        setattr(decorated, "_fbi_apispec", _fbi_apispec)
        return decorated

    def _call_validation_development(
        self, verify: bool, /, **kwargs: Dict[str, Any]
    ) -> Any:
        with current_app.app_context():
            ignore_jwt_validation = current_app.config.get(
                "IGNORE_JWT_VALIDATION", False
            )

        self._call_validation((verify and not ignore_jwt_validation), **kwargs)

    def _call_validation(self, verify: bool, /, **kwargs: Dict[str, Any]) -> Any:
        jwt_claims, jwt_scopes = self._retrieve_jwt_claims(verify)

        valid = jwt_claims and self.validation_function(
            jwt_claims, self.claims_map, jwt_scopes=jwt_scopes, **kwargs
        )

        if verify and not valid:
            raise PermissionError(
                f"Claims {str(jwt_claims)} not valid for call to {request.url}"
            )

        g.jwt_claims = jwt_claims
        g.jwt_scopes = jwt_scopes

    def _log_token(self, jwt_token: str) -> None:
        logger.debug("JWT value: %s", jwt_token)

    def _retrieve_jwt_claims(
        self, verify: bool = True
    ) -> Tuple[Dict[str, str], List[str]]:
        auth_header: Optional[str] = request.headers.get("Authorization", None)
        if auth_header is None or not auth_header.startswith("Bearer "):
            return {}, []
        jwt_token: str = auth_header[7:]

        full_internal_domain: str = current_app.config["HS_ISSUER"]
        full_auth0_domain: Optional[str] = current_app.config.get("AUTH0_DOMAIN", None)
        full_customdb_auth0_domain: Optional[str] = current_app.config.get(
            "AUTH0_CUSTOM_DOMAIN", None
        )
        full_epr_service_adapter_domain: Optional[str] = current_app.config.get(
            "EPR_SERVICE_ADAPTER_ISSUER", None
        )
        algorithms: List[str] = current_app.config["VALID_JWT_ALGORITHMS"]
        internal_audience: str = current_app.config["HS_ISSUER"]

        # Now decode it either as Auth0 or an internal JWT
        try:
            unverified_claims: dict = jose_jwt.get_unverified_claims(jwt_token)
        except jose_jwt.JWTError:
            self._log_token(jwt_token)
            logger.exception("Failed to decode JWT claim")
            return {}, []

        # Throw out JWT if it has no issuer
        if "iss" not in unverified_claims or unverified_claims["iss"] is None:
            self._log_token(jwt_token)
            logger.info("JWT claim has no issuer")
            if verify:
                return {}, []

        # Throw out JWT if this route is locked down to certain issuer(s) and the JWT's issuer doesn't match
        if (
            self.allowed_issuers is not None
            and unverified_claims["iss"] not in self.allowed_issuers
        ):
            self._log_token(jwt_token)
            logger.info(
                "JWT issuer is not allowed for this endpoint",
                extra={
                    "issuer": unverified_claims["iss"],
                    "allowed_issuers": self.allowed_issuers,
                },
            )
            if verify:
                return {}, []

        # Generate the correct parser object

        # Find the appropriate issuer domain or error
        if (
            full_auth0_domain is not None
            and unverified_claims["iss"] == full_auth0_domain
        ):
            issuer_to_verify: str = full_auth0_domain
            audience: str = current_app.config["AUTH0_AUDIENCE"]
            metadata_key: str = current_app.config["AUTH0_METADATA"]
            scope_key: str = current_app.config["AUTH0_SCOPE_KEY"]
            jwt_parser: JwtParser = jwt_parsers.Auth0JwtParser(
                required_audience=audience,
                required_issuer=issuer_to_verify,
                allowed_algorithms=algorithms,
                metadata_key=metadata_key,
                scope_key=scope_key,
                verify=verify,
            )
        elif unverified_claims["iss"] == full_internal_domain:
            jwt_parser = jwt_parsers.InternalJwtParser(
                required_audience=internal_audience,
                required_issuer=full_internal_domain,
                allowed_algorithms=algorithms,
                metadata_key="metadata",
                scope_key="scope",
                verify=verify,
                hs_key=current_app.config["HS_KEY"],
            )
        elif (
            full_customdb_auth0_domain is not None
            and unverified_claims["iss"] == full_customdb_auth0_domain
        ):
            jwt_parser = jwt_parsers.Auth0LoginJwtParser(
                required_audience=internal_audience,
                required_issuer=full_customdb_auth0_domain,
                allowed_algorithms=algorithms,
                metadata_key="metadata",
                scope_key="scope",
                verify=verify,
                hs_key=current_app.config["AUTH0_HS_KEY"],
            )
        elif (
            full_epr_service_adapter_domain is not None
            and unverified_claims["iss"] == full_epr_service_adapter_domain
        ):
            jwt_parser = jwt_parsers.InternalJwtParser(
                required_audience=internal_audience,
                required_issuer=full_epr_service_adapter_domain,
                allowed_algorithms=algorithms,
                metadata_key="metadata",
                scope_key="scope",
                verify=verify,
                hs_key=current_app.config["EPR_SERVICE_ADAPTER_HS_KEY"],
                title="EPR Service Adapter",
            )
        else:
            logger.error(
                "Detected JWT with unknown issuer",
                extra={"issuer": unverified_claims["iss"]},
            )
            return {}, []

        # Verify jwt or error
        unverified_header: Any = None
        try:
            # Auth0 token
            unverified_header = jose_jwt.get_unverified_header(jwt_token)
            return jwt_parser.decode_jwt(jwt_token, unverified_header)
        except (
            ValueError,
            jose_jwt.ExpiredSignatureError,
            jose_jwt.JWTClaimsError,
            jose_jwt.JWSError,
            jose_jwt.JWTError,
        ) as e:
            self._log_token(jwt_token)
            logger.info(
                "Access attempted with invalid JWT",
                extra={"error_message": e},
            )
            logger.debug("Detected %s", jwt_parser)
            logger.debug("Unverified token header: %s", unverified_header)
            logger.debug("Unverified token claims: %s", unverified_claims)
            # Deliberately mask the error so the caller has no clues about security internals
            return {}, []


protected_route = _ProtectedRoute

# Tell connexion to use our decode function
if "BEARERINFO_FUNC" not in os.environ:
    os.environ["BEARERINFO_FUNC"] = ".".join(
        [
            connexion_bearerinfo.decode_bearer_token.__module__,
            connexion_bearerinfo.decode_bearer_token.__name__,
        ]
    )
