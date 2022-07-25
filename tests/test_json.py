import json
from datetime import date, datetime, timedelta, timezone

import pytest

from flask_batteries_included.helpers.json import CustomJSONEncoder

TEST_DATE = date(year=2016, month=11, day=5)

TEST_DATETIME = datetime(
    year=2016, month=11, day=5, hour=3, minute=44, second=12, microsecond=0
)


def test_json_encode_datetime_utc() -> None:
    data = {
        "date": TEST_DATETIME.replace(tzinfo=timezone.utc),
        "string": "test",
        "int": 3,
    }

    assert (
        json.dumps(data, cls=CustomJSONEncoder)
        == '{"date": "2016-11-05T03:44:12.000Z", "string": "test", "int": 3}'
    )


def test_json_encode_datetime_minus_5_hours() -> None:
    data = {"date": TEST_DATETIME.replace(tzinfo=timezone(timedelta(hours=-5)))}

    assert (
        json.dumps(data, cls=CustomJSONEncoder)
        == '{"date": "2016-11-05T03:44:12.000-05:00"}'
    )


def test_json_encode_date() -> None:
    data = {"date": TEST_DATE, "string": "test", "int": 3}

    assert (
        json.dumps(data, cls=CustomJSONEncoder)
        == '{"date": "2016-11-05", "string": "test", "int": 3}'
    )


def test_json_encode_error() -> None:
    data = {"complex": 3 + 4j}
    with pytest.raises(TypeError):
        json.dumps(data, cls=CustomJSONEncoder)
