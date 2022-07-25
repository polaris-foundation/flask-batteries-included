from datetime import date, datetime, timedelta, timezone

import pytest

from flask_batteries_included.helpers.timestamp import (
    join_timestamp,
    parse_date_to_iso8601,
    parse_datetime_to_iso8601,
    parse_iso8601_to_date,
    parse_iso8601_to_datetime,
    split_timestamp,
)

ISO8601_DATETIME = "2010-08-11T11:59:50.123Z"
ISO8601_DATE = ISO8601_DATETIME[:10]
DATE = datetime(2010, 8, 11, 11, 59, 50, 123000)
TZ = 0


@pytest.mark.parametrize(
    ["iso8601", "expected_dt", "expected_tz"],
    (
        [ISO8601_DATETIME, DATE, TZ],
        ["2015-01-01T05:00:00.456+01:00", datetime(2015, 1, 1, 4, 0, 0, 456000), 3600],
        [
            "1975-11-12T16:34:10.010-05:00",
            datetime(1975, 11, 12, 21, 34, 10, 10000),
            -18000,
        ],
    ),
)
def test_split_iso8601_success(
    iso8601: str, expected_dt: datetime, expected_tz: int
) -> None:
    d, tz = split_timestamp(iso8601)

    assert d == expected_dt

    assert tz == expected_tz


def test_split_invalid_iso8601() -> None:
    with pytest.raises(ValueError):
        split_timestamp(ISO8601_DATETIME[:-1])


def test_split_none_iso8601() -> None:
    with pytest.raises(ValueError):
        split_timestamp(None)  # type:ignore


def test_join_iso8601_success() -> None:
    tz_aware_datetime = join_timestamp(DATE, TZ)

    assert tz_aware_datetime == DATE.replace(tzinfo=timezone(timedelta(TZ)))


def test_parse_datetime_to_datetime_string() -> None:
    tz_aware_datetime = join_timestamp(DATE, TZ)
    iso8601 = parse_datetime_to_iso8601(tz_aware_datetime)

    assert iso8601 == ISO8601_DATETIME


def test_parse_datetime_to_iso8601() -> None:
    tz_aware_datetime = join_timestamp(DATE, TZ)
    iso8601 = parse_date_to_iso8601(tz_aware_datetime)

    assert iso8601 == ISO8601_DATE


def test_parse_empty_datetime_to_iso8601() -> None:
    assert parse_datetime_to_iso8601(None) is None


def test_parse_empty_date_to_iso8601() -> None:
    assert parse_date_to_iso8601(None) is None


def test_parse_datetime_string_to_datetime() -> None:
    tz_aware_datetime = parse_iso8601_to_datetime(ISO8601_DATETIME)

    assert tz_aware_datetime == DATE.replace(tzinfo=timezone(timedelta(TZ)))


def test_parse_datetime_string_to_date() -> None:
    d = parse_iso8601_to_date(ISO8601_DATE)

    assert d == date(year=DATE.year, month=DATE.month, day=DATE.day)


def test_parse_invalid_iso8601_to_date() -> None:
    with pytest.raises(ValueError):
        parse_iso8601_to_date("Hello, world!")


def test_parse_empty_iso8601_to_date() -> None:

    assert parse_iso8601_to_date("") is None


def test_parse_empty_iso8601_to_datetime() -> None:

    assert parse_iso8601_to_datetime("") is None
