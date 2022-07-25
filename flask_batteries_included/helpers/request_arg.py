from datetime import datetime
from typing import Any, List, Optional, Type

from flask import request

from flask_batteries_included.helpers.converters import str_bool_to_bool

from .timestamp import parse_iso8601_to_datetime


class RequestArg:
    @staticmethod
    def _get(key: str, default: Any, type: Type) -> Any:
        return request.args.get(key, default, type=type)

    @classmethod
    def product_name(cls, default: str = None) -> str:
        name = cls._get("type", default=default, type=str)
        return name.upper()

    @classmethod
    def diagnosis(cls, default: str = None) -> str:
        diagnosis = cls._get("diagnosis", default=default, type=str)
        return diagnosis

    @classmethod
    def current(cls, default: str = None) -> bool:
        current = cls._get("current", default=default, type=str)
        return str_bool_to_bool(current)

    @classmethod
    def compact(cls, default: str = None) -> bool:
        compact = cls._get("compact", default=default, type=str)
        return str_bool_to_bool(compact)

    @classmethod
    def email(cls, default: str = None) -> str:
        email = cls._get("email", default=default, type=str)
        return email

    @classmethod
    def active(cls, default: str = None) -> bool:
        active = cls._get("active", default=default, type=str)
        return str_bool_to_bool(active)

    @classmethod
    def iso8601_datetime(cls, argument: str, default: str = None) -> Optional[datetime]:
        datetime_str = cls._get(argument, default=default, type=str)
        return parse_iso8601_to_datetime(datetime_str)

    @classmethod
    def string(cls, argument: str, default: str = None) -> str:
        string = cls._get(argument, default=default, type=str)
        return string

    @classmethod
    def integer(cls, argument: str, default: int = None) -> Optional[int]:
        integer = cls._get(argument, default=default, type=int)
        try:
            return None if integer is None else int(integer)
        except ValueError:
            return None

    @classmethod
    def boolean(cls, argument: str, default: str = None) -> bool:
        boolean = cls._get(argument, default=default, type=str)
        return str_bool_to_bool(boolean)

    @classmethod
    def list(cls, argument: str, default: Optional[List] = None) -> List[str]:
        raw_list: str = cls._get(argument, default=None, type=str)
        return default if raw_list is None else raw_list.split("|")
