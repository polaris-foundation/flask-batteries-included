import os
from typing import Any, Dict

import pytest

from flask_batteries_included.helpers import schema


@pytest.mark.usefixtures("app")
class TestSchema:

    schema: Dict[str, Any] = {
        "required": {"thing": str, "other": int, "list": [str]},
        "optional": {"dict_list": [dict]},
        "updatable": {},
    }

    bad_object1 = {
        "thing": "thing",
        "other": 12,
        "list": [{"thing": "thing"}, {"thing": "thing"}],
    }

    bad_object2 = {"thing": "thing", "other": 12.5, "list": ["thing", "thing"]}

    bad_object3 = {"thing": "thing", "other": 12.5, "list": ["thing", "thing"]}

    bad_object4 = {"thing": 12, "other": 12.5, "list": ["thing", "thing"]}

    bad_object5 = {
        "thing": 12,
        "other": 12.5,
        "list": ["thing", "thing"],
        "dict_list": ["thing", "thing"],
    }

    good_object1 = {
        "thing": "thing",
        "other": 12,
        "list": ["thing", "thing"],
        "dict_list": [{"thing": "thing"}, {"thing": "thing"}],
    }

    def test_schema(self) -> None:
        for i in [
            self.bad_object1,
            self.bad_object2,
            self.bad_object3,
            self.bad_object4,
            self.bad_object5,
        ]:
            with pytest.raises(TypeError):
                schema.post(json_in=i, **self.schema)

        assert schema.post(json_in=self.good_object1, **self.schema)

    def test_update_illegal_field(self) -> None:
        json_in = {"imallowed": "hello", "imnotallowed": "oops!"}

        with pytest.raises(ValueError):
            schema.update(updatable={"imallowed": str}, json_in=json_in)

    def test_update_illegal_type(self) -> None:
        json_in = {"imastring": "hello", "imanint": "oops!"}

        with pytest.raises(TypeError):
            schema.update(updatable={"imastring": str, "imanint": int}, json_in=json_in)

    def test_update_int_to_float(self) -> None:
        json_in = {"imafloat": 123}

        out = schema.update(updatable={"imafloat": float}, json_in=json_in)

        assert out == {"imafloat": 123.0}

    def test_allows_white_list(self) -> None:

        os.environ["ENVIRONMENT"] = "DEVELOPMENT"

        res = schema.post(
            required={"thing": int},
            optional={"other": bool},
            json_in={"thing": 123, "created": "some-iso-string", "other": False},
        )

        assert isinstance(res, dict)
        for key in ("thing", "other", "created"):
            assert key in res

    def test_fails_white_list(self) -> None:

        os.environ["ENVIRONMENT"] = "PRODUCTION"

        with pytest.raises(KeyError):
            schema.post(
                required={"thing": int},
                optional={"other": bool},
                json_in={"thing": 123, "created": "some-iso-string", "other": False},
            )
