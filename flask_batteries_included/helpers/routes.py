import re
from datetime import datetime, timezone
from functools import wraps
from typing import Callable, Dict, List, TypeVar, cast
from warnings import warn

from flask import Response
from she_logging import logger

F = TypeVar("F", bound=Callable[..., Response])


def deprecated_route(
    superseded_by: str = None, deprecated: datetime = None
) -> Callable[[F], F]:
    """
    Decorator to be used to mark deprecated endpoints.
    This decorator marks the endpoint as deprecated in the openapi.yaml file,
    it also sets the Deprecation header in all responses to the `deprecated` time, or `true` if no time was given.

    :param superseded_by: method and path of the new endpoint that should be used
    :param deprecated: when the endpoint became deprecated (may be in the future)
    """
    if deprecated and deprecated.tzinfo is None:
        deprecated = deprecated.replace(tzinfo=timezone.utc)

    deprecation_header: str = (
        deprecated.isoformat(timespec="milliseconds") if deprecated else "true"
    )
    extra_headers = {"Deprecation": deprecation_header}
    if superseded_by:
        successor_method, successor = superseded_by.split(maxsplit=1)
        extra_headers["Link"] = f'<{successor}>; rel="successor-version"'

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: List, **kwds: Dict) -> Response:
            warn(
                f"Endpoint {func.__name__} is deprecated, use {superseded_by}",
                DeprecationWarning,
            )
            logger.warning(f"Use of deprecated endpoint {func.__name__}")
            response: Response = func(*args, **kwds)
            response.headers.extend(extra_headers)
            return response

        def _fbi_apispec(operation: Dict) -> None:
            if superseded_by and not re.fullmatch(
                r"(GET|PUT|POST|DELETE|PATCH) /\S+", superseded_by
            ):
                raise ValueError("invalid superseded_by argument for deprecated_route")

            logger.warning(
                f"Marking {operation['operationId']} as deprecated",
            )
            if hasattr(func, "_fbi_apispec"):
                func._fbi_apispec(operation)  # type:ignore
            operation["deprecated"] = True

        setattr(wrapper, "_fbi_apispec", _fbi_apispec)

        return cast(F, wrapper)

    return decorator
