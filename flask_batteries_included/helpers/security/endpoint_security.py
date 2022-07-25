from typing import Any, Callable, Dict, List, Optional, Union

from flask import request
from she_logging import logger

from flask_batteries_included.config import (
    is_not_production_environment,
    is_production_environment,
)


def or_(*args: Callable) -> Callable[..., bool]:
    def composed_validation(jwt_claims: Dict, claims_map: Dict, **kwargs: Any) -> bool:
        return any(arg(jwt_claims, claims_map, **kwargs) for arg in args)

    return composed_validation


def and_(*args: Callable) -> Callable[..., bool]:
    def composed_validation(jwt_claims: Dict, claims_map: Dict, **kwargs: Any) -> bool:
        return all(arg(jwt_claims, claims_map, **kwargs) for arg in args)

    return composed_validation


def key_present(key_to_contain: str) -> Callable[..., bool]:
    def any_with_key(jwt_claims: Dict, claims_map: Dict, **kwargs: Any) -> bool:
        if isinstance(key_to_contain, str) and key_to_contain in jwt_claims:
            return True
        logger.debug(
            "Failed to find key '%s' in JWT",
            key_to_contain,
            extra={"jwt_claims": jwt_claims},
        )
        return False

    return any_with_key


def key_contains_value(
    key_to_contain: str, value_to_contain: str
) -> Callable[..., bool]:
    if not isinstance(value_to_contain, str):
        raise ValueError("Endpoint protection expected values can only be of type str")

    def any_with_key_and_value(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        if (
            key_to_contain in jwt_claims
            and jwt_claims[key_to_contain] == value_to_contain
        ):
            return True
        logger.debug(
            "Failed to find key '%s' in JWT with the expected value '%s'",
            key_to_contain,
            value_to_contain,
            extra={"jwt_claims": jwt_claims},
        )
        return False

    return any_with_key_and_value


def key_contains_value_in_list(
    key_to_contain: str, list_of_possible_values_to_contain: List[str]
) -> Callable[..., bool]:
    if not isinstance(list_of_possible_values_to_contain, list):
        raise ValueError("Endpoint protection expected list can only be of type list")

    def any_with_key_in_value_list(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        if (
            key_to_contain in jwt_claims
            and jwt_claims[key_to_contain] in list_of_possible_values_to_contain
        ):
            return True
        logger.debug(
            "Failed to find key '%s' in JWT with allowed value",
            key_to_contain,
            extra={
                "allowed_values": list_of_possible_values_to_contain,
                "jwt_claims": jwt_claims,
            },
        )
        return False

    return any_with_key_in_value_list


def scopes_present(required_scopes: Union[str, List[str]]) -> Callable[..., bool]:
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]  # wrap string in a list
    elif not isinstance(required_scopes, list):
        raise ValueError("Endpoint protection expected list can only be of type list")

    if not required_scopes:
        raise ValueError(
            "Endpoints protected with scopes_present must require at least one scope"
        )

    def all_scopes_present(
        jwt_claims: Dict, claims_map: Dict, jwt_scopes: List[str], **kwargs: Any
    ) -> bool:
        if jwt_scopes == {}:
            logger.debug("No scopes found in JWT claims")
            return False

        scopes_in_claims: bool = all(
            required_scope in jwt_scopes for required_scope in required_scopes
        )
        if not scopes_in_claims:
            missing_scopes: List[str] = list(set(required_scopes) - set(jwt_scopes))
            logger.debug("JWT is missing required scopes: %s", missing_scopes)
        return scopes_in_claims

    return all_scopes_present


def match_keys(**route_params: str) -> Callable[..., bool]:
    def match_all_keys(jwt_claims: Dict, claims_map: Dict, **kwargs: Any) -> bool:
        return compare_keys(jwt_claims, route_params, **kwargs)

    return match_all_keys


def compare_keys(jwt_claims: Dict, claims_map: Dict, **route_params: str) -> bool:

    # Loop over everything provided in the protected_route constructor
    # If claims_map is empty, they pass this validation stage
    for route_param_name, claim_field in claims_map.items():

        # Check each key in protected_route matches a key in the request route
        if route_param_name not in route_params or claim_field not in jwt_claims:
            return False

        # Get the live value out of the request
        route_value: str = route_params[route_param_name]

        # Get the value out of the jwt_claims
        permission: str = jwt_claims[claim_field]

        # If the permission is a list, look in it. Otherwise just compare values
        if type(permission) == list:
            if route_value not in permission:
                return False

        # Dicts aren't implemented yet
        elif type(permission) == dict:
            return False

        # Compare the route value and the claim
        elif route_value != permission:
            return False

    return True


def non_production_only_route() -> Callable[..., bool]:
    def non_production_only_route_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        return is_not_production_environment()

    return non_production_only_route_internal


def production_only_route() -> Callable[..., bool]:
    def production_only_route_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        return is_production_environment()

    return production_only_route_internal


def argument_present(argument: str, expected_value: str) -> Callable:
    def argument_present_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        value = request.args.get(argument, default="").upper()
        return value == expected_value.upper()

    return argument_present_internal


def argument_not_present(argument: str) -> Callable:
    def argument_not_present_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        return request.args.get(argument, default=None) is None

    return argument_not_present_internal


def field_in_path_matches_jwt_claim(
    path_field_name: str, jwt_claim_name: str
) -> Callable:
    """
    Returns a function that checks that the named field in the request path matches the named JWT claim.
    :param path_field_name: Name of the field in the request path
    :param jwt_claim_name: Name of the JWT claim
    :return: a Callable
    """

    def field_in_path_matches_jwt_claim_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        uuid_in_path: Optional[str] = (
            request.view_args.get(path_field_name)
            if request.view_args is not None
            else None
        )
        jwt_user_id: Optional[str] = jwt_claims.get(jwt_claim_name)
        return jwt_user_id is not None and uuid_in_path == jwt_user_id

    return field_in_path_matches_jwt_claim_internal


def field_in_body_matches_jwt_claim(
    body_field_name: str, jwt_claim_name: str
) -> Callable:
    """
    Returns a function that checks that the named field in the request JSON body matches the named JWT claim.
    :param body_field_name: Name of the field in the request body
    :param jwt_claim_name: Name of the JWT claim
    :return: a Callable
    """

    def field_in_body_matches_jwt_claim_internal(
        jwt_claims: Dict, claims_map: Dict, **kwargs: Any
    ) -> bool:
        body = request.get_json(silent=True)
        field_in_body: Optional[str] = (
            body.get(body_field_name) if body is not None else None
        )
        jwt_claim: Optional[str] = jwt_claims.get(jwt_claim_name)
        return jwt_claim is not None and field_in_body == jwt_claim

    return field_in_body_matches_jwt_claim_internal
