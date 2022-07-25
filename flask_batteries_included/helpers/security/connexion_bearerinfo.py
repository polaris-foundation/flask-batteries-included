"""
Connexion requires a function to decode a JWT token.
This allows us to use bearerAuth in our OpenApi specifications.
"""
from typing import Any, Dict

from jose import JWTError, jwt


def decode_bearer_token(token: str) -> Dict[str, Any]:
    """
    decodes but does not verify the JWT.
    We assume the endpoint will provide the required verification
    (probably through the `protected_route` decorator)
    """
    try:
        return jwt.get_unverified_claims(token)
    except JWTError as e:
        raise PermissionError(f"Bearer token not valid") from e
