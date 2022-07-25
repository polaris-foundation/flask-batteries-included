from flask import Flask
from flask_log_request_id import RequestID, current_request_id
from werkzeug import Response


def init_request_id(app: Flask) -> None:
    RequestID(app)
    app.after_request(append_request_id)


def append_request_id(response: Response) -> Response:
    response.headers.add("X-REQUEST-ID", current_request_id())
    return response
