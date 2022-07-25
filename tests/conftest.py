from typing import Any, Dict, Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask

from flask_batteries_included import sqldb


@pytest.fixture
def app() -> Flask:
    """Fixture that creates app for testing"""
    from flask_batteries_included import create_app

    app = create_app(use_auth0=True, testing=True, use_sqlite=True)
    sqldb.init_db(app, testing=True)
    with app.app_context():
        sqldb.db.create_all()
    return app


@pytest.fixture
def app_context(app: Flask) -> Generator[None, None, None]:
    with app.app_context():
        yield


@pytest.fixture
def redis_values() -> Dict[str, Any]:
    return {}


@pytest.fixture
def mock_dhosredis(monkeypatch: MonkeyPatch, redis_values: Dict[str, Any]) -> None:
    import dhosredis

    class MockRedis:
        @classmethod
        def get_value(cls, key: str) -> Any:
            return redis_values.get(key)

        @classmethod
        def set_value(cls, key: str, value: Any) -> None:
            redis_values[key] = value

    monkeypatch.setattr(dhosredis, "DhosRedis", MockRedis)
