from typing import Any
from uuid import UUID

from flask import Flask

from flask_batteries_included import init_monitoring


def test_request_id_in_response(app: Flask, client: Any) -> None:
    from flask_batteries_included.helpers.metrics import init_metrics

    init_metrics(app)
    init_monitoring(app)

    test_id = "12345678-1234-5678-1234-567812345678"
    response = client.get("/running", headers={"X-REQUEST-ID": test_id})
    assert response.status_code == 200
    request_id_header = response.headers["X-Request-ID"]
    requestID = UUID(request_id_header)

    # Validates that we received a valid uuid in the header
    assert str(requestID) == request_id_header
    assert request_id_header == test_id
    assert response.headers["Cache-Control"] == "no-cache, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"
