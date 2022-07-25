from flask import Flask, request
from she_logging import logger
from werkzeug import Response


def init_etags(app: Flask) -> None:
    app.after_request(_process_etag)


def _process_etag(response: Response) -> Response:
    # We must not modify the response if it is in direct passthrough mode (e.g. serving assets)
    if response.direct_passthrough:
        return response

    response.add_etag()
    # XXX: Flask seems to have the wrong signature for make_conditional
    response.make_conditional(request)  # type:ignore
    if response.status_code == 304:
        logger.debug(
            "304 Not Modified - request header 'If-None-Match' matched ETag",
            extra={"etag": response.get_etag()},
        )
    return response
