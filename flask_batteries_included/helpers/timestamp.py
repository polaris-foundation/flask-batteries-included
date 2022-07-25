from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

# Parses a compact date format
# If the date we're looking at is 2010-08-11 11:59:50.123, timezone +00:00
# this format would represent it as 20100811T115950.123+0000

NORMALISED_8601_DATE_FORMAT = "%Y-%m-%d"
NORMALISED_8601_DATETIME_FORMAT = "%Y-%m-%dT%H%M%S.%f%z"


def split_timestamp(input_timestamp: str) -> Tuple[datetime, int]:
    """
    Takes in a string iso8601 timestamp and returns a datetime in UTC and an offset in seconds

    Raises ValueError on invalid input

    example:
        input: 2010-08-11 11:59:50.123+01:00
        output: 2010-08-11 10:59:50.123, 3600
    """
    parsed_timestamp: Optional[datetime] = parse_iso8601_to_datetime(input_timestamp)
    if parsed_timestamp is None:
        raise ValueError("invalid timestamp")

    tz = parsed_timestamp.tzinfo
    tzoffset = None if tz is None else tz.utcoffset(None)
    time_zone = 0 if tzoffset is None else int(tzoffset.total_seconds())

    delta: timedelta = timedelta(seconds=time_zone)
    parsed_timestamp = parsed_timestamp.replace(tzinfo=None)
    parsed_timestamp -= delta
    return parsed_timestamp, time_zone


def join_timestamp(timestamp: datetime, offset: int) -> datetime:
    """
    Takes in a datetime and an offset in seconds. and returns a string iso8601 timestamp

    example:
        input: 2010-08-11 10:59:50.123, 3600
        output: 2010-08-11 11:59:50.123+01:00
    """
    td: timedelta = timedelta(seconds=offset)
    tz: timezone = timezone(td)
    stamp: datetime = timestamp.replace(tzinfo=tz)
    stamp += td
    return stamp


def parse_date_to_iso8601(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return parse_date_to_iso8601_typesafe(d)


def parse_date_to_iso8601_typesafe(d: date) -> str:
    return d.strftime(NORMALISED_8601_DATE_FORMAT)


def parse_datetime_to_iso8601(dt: Optional[datetime]) -> Optional[str]:
    """
    Parses datetime to ISO8601 string

    Inputs: datetime, timedelta
    Outputs: returned ISO8601 string

    Output Formats:
        - 2000-01-01T01:01:01.123Z,
        - 2000-01-01T01:01:01.123+01:00

    Returns Optional[datetime] because of the possibility of a None return :(
    """
    if dt is None:
        return None
    return parse_datetime_to_iso8601_typesafe(dt)


def parse_datetime_to_iso8601_typesafe(dt: datetime) -> str:
    """
    Parses datetime to ISO8601 string

    Inputs: datetime, timedelta
    Outputs: returned ISO8601 string

    Output Formats:
        - 2000-01-01T01:01:01.123Z,
        - 2000-01-01T01:01:01.123+01:00
    """
    # base e.g. 2001-01-01T10:10:10
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")

    # millis e.g. 123
    millis = dt.strftime("%f")[:3]

    # timezone e.g. +01:00
    tz = dt.strftime("%z")

    if tz:
        if tz == "+0000" or tz == "-0000":
            tz = "Z"
        else:
            tz = tz[:3] + ":" + tz[3:]

    return base + "." + millis + tz


def parse_iso8601_to_date(iso8601: Optional[str]) -> Optional[date]:
    if iso8601 == "" or iso8601 is None:
        return None
    return parse_iso8601_to_date_typesafe(iso8601)


def parse_iso8601_to_date_typesafe(iso8601: str) -> date:
    original_iso8601 = iso8601

    # Normalise away : and -
    iso8601 = "".join(c for c in iso8601 if c != ":")

    try:

        # python date doesn't have strptime so we have to parse it to a datetime...

        parsed_datetime = datetime.strptime(iso8601, NORMALISED_8601_DATE_FORMAT)

        # ... and manually create a date object.

        parsed_date = date(
            year=parsed_datetime.year,
            month=parsed_datetime.month,
            day=parsed_datetime.day,
        )

    except ValueError:
        raise ValueError(original_iso8601 + " does not match expected ISO8601 format")

    return parsed_date


def parse_iso8601_to_datetime(iso8601: Optional[str]) -> Optional[datetime]:
    """
    Parses ISO8601 string to datetime

    Inputs: string (date string to parse)
    Outputs: returned Python datetime object or raised ValueError

    Accepted formats:
        - 2000-01-01T01:01:01.123Z,
        - 2000-01-01T01:01:01.123+01:00

    Anything else: raise ValueError

    Returns Optional[datetime] because of the possibility of a None return :(
    """
    if iso8601 == "" or iso8601 is None:
        return None
    return parse_iso8601_to_datetime_typesafe(iso8601)


def parse_iso8601_to_datetime_typesafe(iso8601: str) -> datetime:
    """
    Parses ISO8601 string to datetime

    Inputs: string (date string to parse)
    Outputs: returned Python datetime object or raised ValueError

    Accepted formats:
        - 2000-01-01T01:01:01.123Z,
        - 2000-01-01T01:01:01.123+01:00

    Anything else: raise ValueError
    """

    original_iso8601 = iso8601

    # Normalise the Z suffix to +00:00
    if iso8601.endswith("Z"):
        iso8601 = iso8601[:-1] + "+00:00"

    # Normalise away : and -
    iso8601 = "".join(c for c in iso8601 if c != ":")

    # ValueError
    try:
        parsed_date = datetime.strptime(iso8601, NORMALISED_8601_DATETIME_FORMAT)
    except ValueError:
        raise ValueError(original_iso8601 + " does not match expected ISO8601 format")

    return parsed_date
