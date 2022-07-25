import pytest
from flask import Flask
from pytest_mock import MockFixture

import flask_batteries_included
from flask_batteries_included import create_app


class TestDebug:
    @pytest.mark.parametrize("is_dev_environment", [True, False])
    def test_debug(self, mocker: MockFixture, is_dev_environment: bool) -> None:
        mock_check = mocker.patch.object(
            flask_batteries_included,
            "is_not_production_environment",
            return_value=is_dev_environment,
        )
        app: Flask = create_app()
        assert mock_check.call_count == 1
        client = app.test_client()
        response = client.get("/debug", headers={"X-Something": "some-value"})
        if is_dev_environment:
            assert response.status_code == 200
            assert response.json is not None
            assert response.json["X-Something"] == "some-value"
        else:
            assert response.status_code == 404
