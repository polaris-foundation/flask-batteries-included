import sys
from collections import Callable
from typing import Any, Dict, Tuple, Union

import flask
from flask import Flask, Response
from marshmallow import ValidationError
from she_logging import logger


class EntityNotFoundException(Exception):
    pass


class ServiceUnavailableException(Exception):
    pass


class DuplicateResourceException(Exception):
    pass


class UnprocessibleEntityException(Exception):
    pass


class AuthMissingException(Exception):
    pass


def _catch(
    error: Union[str, Exception],
    log_method: Callable,
    code: int,
    suppress_traceback: bool = False,
) -> Tuple[Response, int]:
    exc_info: Tuple[Any, Any, Any] = sys.exc_info()
    if suppress_traceback and isinstance(exc_info, tuple):
        exc_info = (exc_info[0], exc_info[1], None)
    log_method(str(error), exc_info=exc_info)
    structure: Dict[str, str] = {"message": str(error)}
    return flask.jsonify(structure), code


def catch_database_exception(
    _error: Exception, msg: str = "Service unavailable"
) -> Tuple[Response, int]:
    return _catch(
        error=f"Database connection failed: {msg}", log_method=logger.critical, code=503
    )


def catch_invalid_database_credentials(error: Exception) -> Tuple[Response, int]:
    return catch_database_exception(error, "Invalid credentials.")


def catch_invalid_database_uri(error: Exception) -> Tuple[Response, int]:
    return catch_database_exception(error, "Invalid connection URI.")


def catch_bad_request(error: Exception) -> Tuple[Response, int]:
    return _catch(error, logger.warning, 400)


def catch_internal_error(error: Exception) -> Tuple[Response, int]:
    return _catch(error, logger.critical, 500)


def catch_not_found(error: Exception) -> Tuple[Response, int]:
    return _catch(error, logger.info, 404)


def catch_unauthorised(_error: Exception) -> Tuple[Response, int]:
    # Suppress traceback because unauthorised is an invalid call, not an error
    return _catch("Forbidden", logger.info, 403, suppress_traceback=True)


def catch_not_implemented(_error: Exception) -> Tuple[Response, int]:
    return _catch("Not implemented", logger.critical, 501)


def catch_unprocessible_entity(_error: Exception) -> Tuple[Response, int]:
    return _catch("Unprocessible entity", logger.info, 422)


def catch_query_exception(_error: Exception) -> Tuple[Response, int]:
    return _catch("Query error", logger.critical, 500)


def catch_service_unavailable(_error: Exception) -> Tuple[Response, int]:
    return _catch("Service unavailable", logger.critical, 503)


def catch_duplicate_resource_error(error: Exception) -> Tuple[Response, int]:
    return _catch(error, logger.warning, 409)


def catch_auth_missing_error(_error: Exception) -> Tuple[Response, int]:
    return _catch("No authentication provided", logger.info, 401)


def catch_deflate_error(error: Exception) -> Tuple[Response, int]:

    if "[^@]+@[^@]+\\.[^@]+" in str(error):
        return _catch("email address format failed validation", logger.warning, 400)

    if "Invalid choice:" in str(error):
        # Happens when an invalid choice (e.g. from a list of strings) is made on a property.
        return _catch(f"invalid choice for property {str(error)}", logger.warning, 400)

    return catch_internal_error(error)


def init_error_handler(*, app: Flask, use_sqlalchemy: bool = False) -> None:

    # catch python errors
    app.register_error_handler(ValueError, catch_bad_request)
    app.register_error_handler(KeyError, catch_bad_request)
    app.register_error_handler(TypeError, catch_bad_request)
    app.register_error_handler(PermissionError, catch_unauthorised)
    app.register_error_handler(NotImplementedError, catch_not_implemented)

    # catch Flask-Batteries-Included errors
    app.register_error_handler(EntityNotFoundException, catch_not_found)
    app.register_error_handler(ServiceUnavailableException, catch_service_unavailable)
    app.register_error_handler(UnprocessibleEntityException, catch_unprocessible_entity)
    app.register_error_handler(
        DuplicateResourceException, catch_duplicate_resource_error
    )
    app.register_error_handler(AuthMissingException, catch_auth_missing_error)

    # catch marshmallow schema validation errors
    app.register_error_handler(ValidationError, catch_bad_request)

    # catch SQLAlchemy errors, if installed
    if use_sqlalchemy:
        import sqlalchemy.exc
        from psycopg2 import ProgrammingError

        app.errorhandler(sqlalchemy.exc.ProgrammingError)(catch_query_exception)
        app.errorhandler(sqlalchemy.exc.OperationalError)(catch_database_exception)
        app.errorhandler(ProgrammingError)(catch_query_exception)

    # catch rabbitmq errors, if installed
    try:
        import pika
    except ImportError:
        pass
    else:
        app.errorhandler(pika.exceptions.ConnectionClosed)(catch_service_unavailable)
        app.errorhandler(pika.exceptions.ChannelClosed)(catch_service_unavailable)
