from datetime import date, datetime
from typing import Any

from flask.json import JSONEncoder

from .timestamp import parse_date_to_iso8601, parse_datetime_to_iso8601


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:

        """
        allows the serialization of datetimes for json.
        uses parse_datetime_to_iso8601 from timestamp.py
        """
        if isinstance(obj, datetime):
            return parse_datetime_to_iso8601(obj)
        elif isinstance(obj, date):
            return parse_date_to_iso8601(obj)
        return JSONEncoder.default(self, obj)
