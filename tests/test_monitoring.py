import logging
from typing import Any, Dict, Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture
from flask import Flask

from flask_batteries_included import init_monitoring


class _Anything:
    def __init__(self, _type: Optional[Type] = None) -> None:
        self._type = _type

    def __eq__(self, other: Any) -> bool:
        if self._type is not None:
            return isinstance(other, self._type)
        return True


ANY = _Anything()
ANY_STRING = _Anything(str)
ANY_FLOAT = _Anything(float)


@pytest.fixture
def with_app_monitoring(app: Flask) -> None:
    from flask_batteries_included.helpers.metrics import init_metrics

    init_metrics(app)
    init_monitoring(app)


@pytest.mark.parametrize(
    "endpoint, content_type,expected",
    [
        ("/running", "application/json", {"running": True}),
        ("/metrics", "text/plain", None),
        (
            "/healthcheck",
            "application/json",
            {
                "hostname": ANY_STRING,
                "results": [],
                "status": "success",
                "timestamp": ANY_FLOAT,
            },
        ),
    ],
)
def test_monitoring_endpoints(
    with_app_monitoring: None,
    client: Any,
    caplog: LogCaptureFixture,
    endpoint: str,
    content_type: str,
    expected: Dict,
) -> None:
    with caplog.at_level(logging.DEBUG):
        response = client.get(endpoint)

    assert not caplog.text, "Metrics endpoint should not be logged"
    assert response.status_code == 200
    if content_type == "application/json":
        assert response.json == expected
