import time
from typing import Dict

from flask import Flask
from flask import Response as FlaskResponse
from flask import request
from prometheus_client import Counter, Histogram, Summary, generate_latest
from she_logging import logger
from werkzeug import Response as WerkzeugResponse

NO_METRICS_HEADER_NAME = "X-No-Metrics"
NO_METRICS_HEADER = {NO_METRICS_HEADER_NAME: "X"}

CONTENT_TYPE_LATEST = str("text/plain; version=0.0.4; charset=utf-8")


FLASK_REQUEST_LATENCY = Histogram(
    "flask_request_latency_seconds", "Flask Request Latency", ["method", "endpoint"]
)

FLASK_REQUEST_COUNT = Counter(
    "flask_request_count", "Flask Request Count", ["method", "endpoint", "http_status"]
)

REQUEST_TIME = Summary(
    "request_processing_seconds",
    "Time spent processing request",
    ["method", "endpoint"],
)


def set_no_metrics(response: FlaskResponse) -> FlaskResponse:
    response.headers.extend(NO_METRICS_HEADER)
    return response


def add_no_cache_headers(response: WerkzeugResponse) -> WerkzeugResponse:
    """
    Add headers to both force IE to not cache response
    Only add header if not already set
    """
    if not response.headers.get("Cache-Control"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    if not response.headers.get("Pragma"):
        response.headers["Pragma"] = "no-cache"
    if not response.headers.get("Expires"):
        response.headers["Expires"] = "0"
    return response


def before_request() -> None:
    request.start_time = time.time()  # type: ignore


def after_request(response: WerkzeugResponse) -> WerkzeugResponse:
    response = add_no_cache_headers(response)

    # Skip logging and metrics for app monitoring probes
    if NO_METRICS_HEADER_NAME in response.headers:
        del response.headers[NO_METRICS_HEADER_NAME]
        return response

    start_time: float = request.start_time  # type:ignore
    request_latency: float = time.time() - start_time
    FLASK_REQUEST_LATENCY.labels(request.method, request.endpoint).observe(
        request_latency
    )
    FLASK_REQUEST_COUNT.labels(
        request.method, request.endpoint, response.status_code
    ).inc()
    REQUEST_TIME.labels(request.method, request.endpoint).observe(request_latency)

    content_length = response.headers.get("content-length")

    request_details = {
        "status": response.status_code,
        "requestUrl": request.url,
        "requestMethod": request.method,
        "remoteIp": request.remote_addr,
        "responseSize": content_length,
        "userAgent": str(request.user_agent),
        "latency": f"{request_latency:.4f}s",
        "etag": response.get_etag(),
    }
    additional_details: Dict[str, Dict] = {
        "requestXHeaders": {
            k: v for k, v in request.headers.items() if k.lower().startswith("x-")
        },
        "requestQueryParams": dict(request.args or {}),
        "requestPathParams": dict(request.view_args or {}),
    }
    if response.status_code not in range(200, 300) and not response.direct_passthrough:
        # HTTP error has happened, so include the request/response body which may describe the error.
        response_body_text: str = response.get_data(as_text=True)
        request_body_text: str = request.get_data(as_text=True)
        if len(response_body_text) > 5000:
            response_body_text = response_body_text[:5000] + " [clipped]"
        if len(request_body_text) > 5000:
            request_body_text = request_body_text[:5000] + " [clipped]"
        request_details["responseContent"] = response_body_text
        request_details["requestContent"] = request_body_text
    logger.info(
        '%s "%s" %s',
        request.method,
        request.endpoint or request.path,
        response.status_code,
        extra={"httpRequest": request_details},
    )
    logger.debug(
        "Request has additional details",
        extra={"httpRequest": additional_details},
    )
    return response


def init_metrics(app: Flask) -> None:
    app.before_request(before_request)
    app.after_request(after_request)

    @app.route("/metrics")
    def get_metrics() -> FlaskResponse:
        return set_no_metrics(
            FlaskResponse(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
        )

    logger.info("Registered metrics route on /metrics")


# Ref: https://blog.codeship.com/monitoring-your-synchronous-python-web-applications-using-prometheus/
