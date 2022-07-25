import datetime

import pytest
from flask import Flask

from flask_batteries_included.helpers.request_arg import RequestArg


class TestRequestArgs:
    def test_product_name(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?type=GDM"):
            assert RequestArg.product_name() == "GDM"

    def test_product_name_lowercase(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?type=gdm"):
            assert RequestArg.product_name() == "GDM"

    def test_product_name_default(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something"):
            assert RequestArg.product_name(default="BOB") == "BOB"

    def test_diagnosis(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?diagnosis=D12345"):
            assert RequestArg.diagnosis() == "D12345"

    def test_current(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?current=true"):
            assert RequestArg.current() is True

    def test_current_default(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something"):
            assert RequestArg.current(default="false") is False

    def test_current_invalid(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?current=jeff"):
            with pytest.raises(TypeError):
                RequestArg.current()

    def test_compact(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?compact=false"):
            assert RequestArg.compact() is False

    def test_email(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?email=bob@bob.bob"):
            assert RequestArg.email() == "bob@bob.bob"

    def test_active(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?active=true"):
            assert RequestArg.active() is True

    def test_iso8601_datetime(self, app: Flask) -> None:
        with app.test_request_context(
            f"/dhos/v1/something?time=1970-01-01T00:00:00.000Z"
        ):
            assert isinstance(RequestArg.iso8601_datetime("time"), datetime.datetime)

    def test_string(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?s=some-string"):
            assert isinstance(RequestArg.string("s"), str)

    def test_integer(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?i=12345"):
            assert isinstance(RequestArg.integer("i"), int)

    def test_missing_integer(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something"):
            assert RequestArg.integer("i") is None

    def test_bad_integer(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?i=a"):
            assert RequestArg.integer("i") is None

    def test_boolean(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?b=true"):
            assert RequestArg.boolean("b") is True

        with app.test_request_context(f"/dhos/v1/something?b=false"):
            assert RequestArg.boolean("b") is False

        with app.test_request_context(f"/dhos/v1/something?a=rubbish"):
            assert RequestArg.boolean("b") is None

    def test_list(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?i=12345"):
            assert RequestArg.list("i") == ["12345"]

    def test_list_split(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?i=12345|66778"):
            assert RequestArg.list("i") == ["12345", "66778"]

    def test_list_if_none(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something"):
            assert RequestArg.list("i") is None

    def test_list_if_empty_list(self, app: Flask) -> None:
        with app.test_request_context(f"/dhos/v1/something?i=1"):
            assert isinstance(RequestArg.list("i"), list)
