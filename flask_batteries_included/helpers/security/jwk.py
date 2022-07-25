import json
from typing import Dict, Optional

import requests
from flask import current_app
from she_logging import logger


def retrieve_relevant_jwk(jwks: Dict, jwt_header: Dict) -> Optional[Dict]:
    rsa_key = None
    for key in jwks["keys"]:
        if key["kid"] == jwt_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break
    return rsa_key


def fetch_auth0_jwks() -> str:
    logger.debug("Fetching JWKS from Auth0")
    with current_app.app_context():
        auth0_jwks_url = current_app.config["AUTH0_JWKS_URL"]
    fresh_jwks_resp = requests.get(auth0_jwks_url)
    if fresh_jwks_resp.status_code != 200:
        logger.critical("Not able to retrieve Auth0 JWKS from Auth0")
        raise EnvironmentError("Could not retrieve JWKs from Auth0")
    return fresh_jwks_resp.text


def retrieve_auth0_jwks(jwt_header: Dict, testing: bool = False) -> Dict:
    if testing:
        with current_app.app_context():
            jwks_str = current_app.config["AUTH0_JWKS_TESTING"]
            jwks = json.loads(jwks_str)
            return jwks

    # Import dhosredis locally so we can avoid needing redis for services that don't use JWT validation.
    import dhosredis

    jwks_from_cache = dhosredis.get_value("AUTH0_JWKS")
    if (
        jwks_from_cache
        and retrieve_relevant_jwk(json.loads(jwks_from_cache), jwt_header) is not None
    ):
        jwks_str = jwks_from_cache
    else:
        logger.debug("Did not find Auth0 JWKS in cache - fetching from Auth0 API")
        jwks_str = fetch_auth0_jwks()
        dhosredis.set_value("AUTH0_JWKS", jwks_str)
    return json.loads(jwks_str)
