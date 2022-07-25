import environs
import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask

from flask_batteries_included import config


class TestConfig:
    def test_init_jwt_config_success(self, monkeypatch: MonkeyPatch) -> None:
        app: Flask = Flask(__name__)
        monkeypatch.setenv("HS_KEY", "key_test")
        monkeypatch.setenv("PROXY_URL", "http://someurl.com/")
        config.init_config(app=app, use_jwt=True)
        assert app.config["HS_KEY"] == "key_test"
        assert app.config["PROXY_URL"] == "http://someurl.com/"

    def test_init_jwt_config_missing(self, monkeypatch: MonkeyPatch) -> None:
        app: Flask = Flask(__name__)
        monkeypatch.delenv("HS_KEY")
        monkeypatch.delenv("PROXY_URL")
        with pytest.raises(environs.EnvError):
            config.init_config(app=app, use_jwt=True)

    def test_init_jwt_config_not_required(self, monkeypatch: MonkeyPatch) -> None:
        app: Flask = Flask(__name__)
        monkeypatch.delenv("HS_KEY")
        monkeypatch.delenv("PROXY_URL")
        config.init_config(app=app, use_jwt=False)
        assert "HS_KEY" not in app.config
        assert "PROXY_URL" not in app.config

    def test_init_jwt_config_auth0_gdm(self, monkeypatch: MonkeyPatch) -> None:
        app: Flask = Flask(__name__)
        monkeypatch.setenv("HS_KEY", "key_test")
        monkeypatch.setenv("PROXY_URL", "http://someurl.com/")
        config.init_config(app=app, use_jwt=True, use_auth0=True)
        assert app.config["HS_KEY"] == "key_test"
        assert app.config["PROXY_URL"] == "http://someurl.com/"
        assert app.config["AUTH0_METADATA"] == "https://gdm.sensynehealth.com/metadata"
        assert app.config["AUTH0_SCOPE_KEY"] == "https://gdm.sensynehealth.com/scope"

    def test_init_jwt_config_b2c_merlin(self, monkeypatch: MonkeyPatch) -> None:
        app: Flask = Flask(__name__)
        monkeypatch.setenv("HS_KEY", "key_test")
        monkeypatch.setenv("PROXY_URL", "http://someurl.com/")
        monkeypatch.setenv("AUTH0_METADATA", "dummy")
        monkeypatch.setenv("AUTH0_SCOPE_KEY", "permissions")
        config.init_config(app=app, use_jwt=True, use_auth0=True)
        assert app.config["HS_KEY"] == "key_test"
        assert app.config["PROXY_URL"] == "http://someurl.com/"
        assert app.config["AUTH0_METADATA"] == "dummy"
        assert app.config["AUTH0_SCOPE_KEY"] == "permissions"
