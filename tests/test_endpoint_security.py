import os
from unittest.mock import Mock

import pytest
from pytest_mock import MockFixture

from flask_batteries_included import create_app
from flask_batteries_included.helpers.security import endpoint_security
from flask_batteries_included.helpers.security.endpoint_security import (
    and_,
    argument_not_present,
    argument_present,
    compare_keys,
    key_contains_value,
    key_contains_value_in_list,
    key_present,
    non_production_only_route,
    or_,
    production_only_route,
    scopes_present,
)


def test_valid_key_present() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_present("patient_id")
    assert bound_function(jwt_claims, None) is True


def test_invalid_key_present() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_present("clinician")
    assert bound_function(jwt_claims, None) is False


def test_valid_or_() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = or_(key_present("clinician_id"), key_present("patient_id"))
    assert bound_function(jwt_claims, None) is True


def test_invalid_or_() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = or_(key_present("clinician_id"), key_present("system_id"))
    assert bound_function(jwt_claims, None) is False


def test_valid_and_() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = and_(key_present("patient_id"), key_present("patient_id"))
    assert bound_function(jwt_claims, None) is True


def test_invalid_and_() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = and_(key_present("patient_id"), key_present("clinician_id"))
    assert bound_function(jwt_claims, None) is False


def test_valid_key_and_value() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value("patient_id", "12345")
    assert bound_function(jwt_claims, None) is True


def test_invalid_key_and_valid_value() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value("clinician_id", "12345")
    assert bound_function(jwt_claims, None) is False


def test_valid_key_and_invalid_value() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value("patient_id", "123456")
    assert bound_function(jwt_claims, None) is False


def test_valid_key_and_list_of_values() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value_in_list("patient_id", ["12345", "67890"])
    assert bound_function(jwt_claims, None) is True


def test_invalid_key_and_valid_list_of_values() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value_in_list("clinician_id", ["12345", "67890"])
    assert bound_function(jwt_claims, None) is False


def test_valid_key_and_invalid_list_of_values() -> None:
    jwt_claims = {"patient_id": "12345"}
    bound_function = key_contains_value_in_list("patient_id", ["123456", "78901"])
    assert bound_function(jwt_claims, None) is False


def test_invalid_scope() -> None:
    jwt_scopes = ["read:user"]
    bound_function = scopes_present(required_scopes=["write:user"])
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is False


def test_invalid_scopes() -> None:
    jwt_scopes = ["read:user", "write:user"]
    bound_function = scopes_present(required_scopes=["write:users"])
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is False


def test_invalid_scopes_superset() -> None:
    jwt_scopes = ["read:user", "write:user", "read:patient"]
    bound_function = scopes_present(
        required_scopes=["read:user", "write:user", "read:patient", "write:patient"]
    )
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is False


def test_invalid_scope_to_list() -> None:
    jwt_scopes = ["read:user", "write:user"]
    bound_function = scopes_present(required_scopes="read:patient")
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is False


def test_valid_scope() -> None:
    jwt_scopes = ["read:user", "write:user"]
    bound_function = scopes_present(required_scopes=["write:user"])
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is True


def test_valid_scopes_equal() -> None:
    jwt_scopes = ["read:user", "write:user"]
    bound_function = scopes_present(required_scopes=["read:user", "write:user"])
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is True


def test_valid_scopes_subset() -> None:
    jwt_scopes = ["read:user", "write:user", "read:patient"]
    bound_function = scopes_present(required_scopes=["write:user", "read:patient"])
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is True


def test_valid_scope_to_list() -> None:
    jwt_scopes = ["read:user", "write:user", "read:patient"]
    bound_function = scopes_present(required_scopes="read:user")
    assert bound_function({}, None, jwt_scopes=jwt_scopes) is True


def test_compare_keys_no_expected_params() -> None:
    assert compare_keys({}, {}) is True


def test_compare_keys_expected_params_not_supplied() -> None:
    assert compare_keys({}, {"patient_id": "patient_id"}) is False


def test_compare_keys_with_expected_params() -> None:
    assert (
        compare_keys(
            {"patient_id": "12345"}, {"patient_id": "patient_id"}, patient_id="12345"
        )
        is True
    )


def test_compare_keys_without_expected_params() -> None:
    assert (
        compare_keys(
            {"patient_id": "WRONG_ID_IN_JWT"},
            {"patient_id": "patient_id"},
            patient_id="12345",
        )
        is False
    )


def test_compare_keys_with_expected_params_not_in_route_param_list() -> None:
    assert (
        compare_keys(
            {"claim_field_1": ["claim_1_value"]},
            {"route_param_1": "claim_field_1"},
            route_param_1="claim_2_value",
        )
        is False
    )


def test_compare_keys_param_dict() -> None:
    assert (
        compare_keys(
            {"claim_field_1": {"claim_1_value": None}},
            {"route_param_1": "claim_field_1"},
            route_param_1="claim_2_value",
        )
        is False
    )


def test_argument_present() -> None:
    f = argument_present(argument="arg1", expected_value="val1")
    app = create_app()
    with app.test_request_context(
        "/dhos/v1/patient?arg1=val1", data={"format": "short"}
    ):
        assert f({}, {}) is True


def test_argument_present_of_multiple() -> None:
    f = argument_present(argument="arg1", expected_value="val1")
    app = create_app()
    with app.test_request_context(
        "/dhos/v1/patient?arg1=val1&arg2=val2", data={"format": "short"}
    ):
        assert f({}, {}) is True


def test_argument_present_fails() -> None:
    f = argument_present(argument="arg1", expected_value="val1")
    app = create_app()
    with app.test_request_context(
        "/dhos/v1/patient?arg1=val2", data={"format": "short"}
    ):
        assert f({}, {}) is False


def test_not_argument_present() -> None:
    f = argument_not_present(argument="arg1")
    app = create_app()
    with app.test_request_context(
        "/dhos/v1/patient?arg2=val1", data={"format": "short"}
    ):
        assert f({}, {}) is True


def test_not_argument_present_fails() -> None:
    f = argument_not_present(argument="arg2")
    app = create_app()
    with app.test_request_context(
        "/dhos/v1/patient?arg2=val1", data={"format": "short"}
    ):
        assert f({}, {}) is False


def test_production_only_route_prod() -> None:
    f = production_only_route()
    os.environ["ENVIRONMENT"] = "PRODUCTION"
    assert f({}, {}) is True


def test_production_only_route_dev() -> None:
    f = production_only_route()
    os.environ["ENVIRONMENT"] = "DEVELOPMENT"
    assert f({}, {}) is False


def test_non_production_only_route_prod() -> None:
    f = non_production_only_route()
    os.environ["ENVIRONMENT"] = "PRODUCTION"
    assert f({}, {}) is False


def test_non_production_only_route_dev() -> None:
    f = non_production_only_route()
    os.environ["ENVIRONMENT"] = "DEVELOPMENT"
    assert f({}, {}) is True


@pytest.mark.usefixtures("app")
@pytest.mark.parametrize(
    ["jwt_claim", "request_path_field", "expected"],
    [
        ("12345", "12345", True),
        ("abcde", "12345", False),
        ("12345", None, False),
        (None, "12345", False),
        (None, None, False),
    ],
)
def test_field_in_path_matches_jwt_claim(
    mocker: MockFixture, jwt_claim: str, request_path_field: str, expected: bool
) -> None:
    jwt_claims = {"patient_id": jwt_claim}
    mock_request: Mock = mocker.patch(
        "flask_batteries_included.helpers.security.endpoint_security.request"
    )
    mock_request.view_args = {"patient_uuid": request_path_field}
    f = endpoint_security.field_in_path_matches_jwt_claim(
        path_field_name="patient_uuid", jwt_claim_name="patient_id"
    )
    assert f(jwt_claims, None) is expected


@pytest.mark.usefixtures("app")
@pytest.mark.parametrize(
    ["jwt_claim", "request_body_field", "expected"],
    [
        ("12345", "12345", True),
        ("abcde", "12345", False),
        ("12345", None, False),
        (None, "12345", False),
        (None, None, False),
    ],
)
def test_field_in_body_matches_jwt_claim(
    mocker: MockFixture, jwt_claim: str, request_body_field: str, expected: bool
) -> None:
    jwt_claims = {"patient_id": jwt_claim}
    mocker.patch(
        "flask.request.get_json", return_value={"patient_uuid": request_body_field}
    )
    f = endpoint_security.field_in_body_matches_jwt_claim(
        body_field_name="patient_uuid", jwt_claim_name="patient_id"
    )
    assert f(jwt_claims, None) is expected
