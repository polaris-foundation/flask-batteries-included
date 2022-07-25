from typing import Dict, List, Optional, Tuple

import requests
from flask import current_app, g
from jose import jwt as jose_jwt
from she_logging import logger

VALID_USER_ID_KEYS: Tuple = ("patient_id", "device_id", "clinician_id", "system_id")


def current_jwt_user() -> str:
    try:
        claims = g.jwt_claims or {}
    except AttributeError:
        claims = {}

    for claim_type in VALID_USER_ID_KEYS:
        if claim_type in claims:
            return claims[claim_type]

    if claims:
        # There are claims, so we should expect to be able to get the user UUID.
        logger.warning("Could not get user UUID from JWT - claims are: %s", claims)
    return "unknown"


def decode_hs_jwt(
    hs_key: str, jwt_token: str, algorithms: List[str], decode_options: Dict
) -> Optional[Dict]:
    try:
        return jose_jwt.decode(
            jwt_token, hs_key, algorithms=algorithms, options=decode_options
        )
    except (jose_jwt.ExpiredSignatureError, jose_jwt.JWTError, jose_jwt.JWSError):
        logger.exception("Access attempted with incorrect JWT token: %s")
        # Deliberately mask the error so the caller has no clues about security internals
        return None


def add_system_jwt_to_headers(http_headers: Dict, system_id: str) -> Dict:
    # Grab a JWT from local system JWT provider if IGNORE_JWT_VALIDATION is false
    with current_app.app_context():
        if current_app.config["IGNORE_JWT_VALIDATION"] is False:
            _scheme = current_app.config["SYSTEM_AUTH_URL_SCHEME"]
            _host = current_app.config["SYSTEM_AUTH_HOST"]
            _port = str(current_app.config["SYSTEM_AUTH_PORT"])

            return _add_system_jwt_to_headers(
                http_headers, system_id, f"{_scheme}://{_host}:{_port}"
            )

    return http_headers


def _add_system_jwt_to_headers(
    http_headers: Dict, system_id: str, _url_base: str
) -> Dict:
    url = f"{_url_base}/dhos/v1/system/{system_id}/jwt"
    jwt: str = requests.get(url).json()["jwt"]
    http_headers["Authorization"] = f"Bearer {jwt}"

    return http_headers
