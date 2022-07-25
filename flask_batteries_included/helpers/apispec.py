import copy
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Union

import connexion
from apispec import APISpec, BasePlugin
from apispec.yaml_utils import dict_to_yaml
from connexion import FlaskApp
from flask import Blueprint
from flask import current_app as app
from marshmallow import Schema, fields
from she_logging import logger

from flask_batteries_included.blueprint_monitoring import app_monitor


class FlaskBatteriesPlugin(BasePlugin):
    """APISpec plugin for Flask Batteries"""

    def path_helper(
        self,
        path: str = None,
        operations: Dict = None,
        parameters: Any = None,
        view: Callable = None,
        **kwargs: Dict[str, Any],
    ) -> Optional[str]:
        """Path helper that adds operationId and security to operations."""
        view_module = getattr(view, "__module__")
        view_name = getattr(view, "__name__")

        if operations is not None and view_module and view_name:
            for key, operation in operations.items():
                if isinstance(operation, dict):
                    if "operationId" not in operation:
                        operation["operationId"] = ".".join([view_module, view_name])
                    is_deprecated = operation.pop("deprecated", None)

                    if hasattr(view, "_fbi_apispec"):
                        view._fbi_apispec(operation)  # type:ignore

                    # Setting "deprecated" explicitly in the yaml is only allowed if we also have the decorator
                    # If correctly applied deprecated_route will have added the "deprecated" field back again.
                    if is_deprecated and not operation.get("deprecated"):
                        raise RuntimeError(
                            f"Missing deprecated_route decorator for {operation['operationId']}"
                        )

        return path


class Error(Schema):
    class Meta:
        description = """An error response in json format"""
        ordered = True

    code = fields.Integer(
        required=True, metadata={"description": "HTTP response code", "example": 404}
    )
    message = fields.String(
        required=False,
        metadata={
            "description": "Message attached to response",
            "example": "Not Found",
        },
    )


class Identifier(Schema):
    class Meta:
        ordered = True

    uuid = fields.String(
        required=True,
        metadata={
            "description": "Universally unique identifier for object",
            "example": "2c4f1d24-2952-4d4e-b1d1-3637e33cc161",
        },
    )
    created = fields.String(
        metadata={
            "description": "When the object was created",
            "example": "2017-09-23T08:29:19.123+00:00",
        }
    )
    created_by = fields.String(
        metadata={
            "description": "UUID of the user that created the object",
            "example": "d26570d8-a2c9-4906-9c6a-ea1a98b8b80f",
        }
    )
    modified = fields.String(
        metadata={
            "description": "When the object was modified",
            "example": "2017-09-23T08:29:19.123+00:00",
        }
    )
    modified_by = fields.String(
        metadata={
            "description": "UUID of the user that modified the object",
            "example": "2a0e26e5-21b6-463a-92e8-06d7290067d0",
        }
    )


RESPONSES = [
    ("BadRequest", "Bad or malformed request was received"),
    ("NotFound", "The specified resource was not found"),
    ("Unauthorized", "Unauthorized"),
    ("ServiceUnavailable", "Service or dependent resource not available"),
]


def initialise_apispec(spec: APISpec) -> None:
    """Adds standard responses and bearerAuth authentication to the api spec"""
    spec.components.schema("Error", schema=Error).security_scheme(
        "bearerAuth", {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    )

    for component_id, description in RESPONSES:
        spec.components.response(
            component_id=component_id,
            component={
                "description": description,
                "content": {"application/json": {"schema": "Error"}},
            },
        )


def openapi_schema(
    spec: APISpec, component: Dict = None
) -> Callable[[Type[Schema]], Type[Schema]]:
    """Decorator to expose a marshmallow schema in the api spec"""

    def wrap(cls: Type[Schema]) -> Type[Schema]:
        spec.components.schema(
            component_id=cls.__name__, component=component, schema=cls
        )
        return cls

    return wrap


def generate_openapi_spec(
    specification: APISpec, output: Union[Path, str], *blueprints: Blueprint
) -> None:
    filters = tuple(f"{blueprint.name}." for blueprint in blueprints + (app_monitor,))

    with app.test_request_context():
        for name, func in app.view_functions.items():
            operation_id = ".".join([func.__module__, func.__name__])
            if not name.startswith(filters):
                # Skip view functions that aren't part of a blueprint we are requesting.
                continue
            if func.__doc__ is not None and "---" in func.__doc__:
                logger.info("Endpoint %s %s", name, operation_id)
                specification.path(view=func)
            elif operation_id == "healthcheck.check":
                # Healthcheck endpoint is added by a library so we can't document it.
                continue
            else:
                logger.warning(
                    "Skipping endpoint %s %s - doc missing", name, operation_id
                )

    spec_dict = specification.to_dict()

    # Order the spec so that they are consistently laid out.
    top_keys = ["openapi", "info", "servers", "paths"]
    ordered_spec = dict.fromkeys(key for key in top_keys if key in spec_dict)
    ordered_spec.update(spec_dict)

    if verify_openapi_spec(ordered_spec):
        yaml_text = dict_to_yaml(ordered_spec, yaml_dump_kwargs={"sort_keys": False})
        Path(output).write_text(yaml_text)
        logger.info("API specification generated in %s", output)


def verify_openapi_spec(specification: Dict) -> bool:
    # Make a copy so we don't mutate the input dict.
    specification_copy: Dict = copy.deepcopy(specification)
    try:
        connexion_app: FlaskApp = connexion.App(
            __name__, specification_dir="swagger/", options={"swagger_ui": False}
        )
        connexion_app.add_api(
            specification=specification_copy,
            strict_validation=True,
            base_path="/specification-test",
        )
    except Exception as e:
        logger.error("Invalid OPENAPI specification: %s", str(e))
        return False
    return True
