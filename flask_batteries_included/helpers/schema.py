from typing import Any, Dict, Type

from flask import request

from flask_batteries_included.config import is_not_production_environment

NON_PROD_WHITE_LIST = ["uuid", "created", "created_by", "modified", "modified_by"]


def _is_whitelisted(key: str) -> bool:
    return key in NON_PROD_WHITE_LIST and is_not_production_environment()


def _get_json() -> Dict:
    """
    Gets a json object from flask.request if one exists,
    otherwise it throws a 400
    """

    if request.is_json:
        data = request.get_json()
        if data is not None:
            return data
    raise ValueError("Request requires a json body")


def post(
    required: Dict = None,
    optional: Dict = None,
    json_in: Dict = None,
    **kwargs: Dict[str, Any],
) -> Dict:
    """
    Used for validating a json object in a POST request

    If no json_in is supplied, It will attempt to get it from _get_json(),
    otherwise it will just use the dictionary passed in as json_in.

    If a value is optional but does not exist in json object,
    it will be set to an empty list if its expected type is a list otherwise
    None

    500 will be thrown if...
    - No object is passed as json_in and no json object is available in
    flask.request

    400 will be thrown if...
    - If the key is required but does not exist in json_in
    - If the value of any key is not the expected type (will convert int to
    float automatically)
    - If a key is passed in that does not exist in the models schema
    """

    # Default required and optional
    required = {} if required is None else required
    optional = {} if optional is None else optional

    def type_check(obj: Any, typ: Type) -> Any:

        if obj is None:
            return None

        # check list type
        if isinstance(typ, list):
            typ_len = len(typ)

            if not isinstance(obj, list):
                raise TypeError("%s is not of the expected type" % obj)

            # list of > 1 types, not valid
            if typ_len > 1:
                raise ValueError("")

            # list of 1 type, perfect!
            elif typ_len == 1:
                real_type = typ[0]
                for item in obj:
                    if not isinstance(item, real_type):
                        raise TypeError(
                            "value in list %s is not of the expected type" % key
                        )

            # list of 0 types, we don't care what type it is
            else:
                pass

        # Check value is of expected type, or if int supplied and float expected, auto convert
        elif not isinstance(obj, typ):
            if isinstance(obj, int) and typ == float:
                obj = float(obj)
            else:
                raise TypeError("value for %s is not of the expected type" % key)

        return obj

    if json_in is None:
        _json = _get_json()
    else:
        _json = json_in

    if _json is None:

        raise ValueError("No JSON body provided")

    for key in required:

        value_type = required[key]

        if key not in _json or _json[key] is None:
            raise KeyError(f"Json request is missing a required key %s" % key)

        _json[key] = type_check(_json[key], value_type)

    for key in optional:
        value_type = optional[key]

        # Default optional list or dict value if not present or if set to None
        if key not in _json or _json[key] is None:
            if value_type in [list, dict]:
                _json[key] = value_type()
            elif isinstance(value_type, list):
                _json[key] = list()
            else:
                _json[key] = None

        _json[key] = type_check(_json[key], value_type)

    for key in _json:
        if key not in optional and key not in required and not _is_whitelisted(key):
            raise KeyError(
                "Request body '%s' contains unexpected key: %s" % (_json, key)
            )

    return _json


def update(
    updatable: Dict = None,
    optional: Dict = None,
    json_in: Dict = None,
    **kwargs: Dict[str, Any],
) -> Dict:
    """
    Used for validating a json object in a PUT/PATCH request

    If no json_in is supplied, It will attempt to get it from _get_json(),
    otherwise it will just use the dictionary passed in as json_in.

    500 will be thrown if...
    - No object is passed as json_in and no json object is available in
    flask.request

    400 will be thrown if...
    - If the value of any key is not the expected type (will convert int to
    float automatically)
    - If a key is passed in that is not in updatable
    """

    # Default updatable and optional
    updatable = {} if updatable is None else updatable
    optional = {} if optional is None else optional

    _json = json_in or _get_json()

    if _json is None:
        raise ValueError("JSON body is empty")

    for key in _json:
        if key not in updatable:
            raise ValueError("%s can not be updated" % key)
        elif not isinstance(_json[key], updatable[key]):
            if isinstance(_json[key], int) and updatable[key] == float:
                _json[key] = float(_json[key])
            elif _json[key] is None and key in optional:
                continue
            else:
                raise TypeError("value for %s is not of the expected type" % key)
    return _json


def get() -> None:
    """
    Because a GET request should not contain a json object,
    If one is available in flask.request, a 400 will be thrown
    """
    if request.is_json:
        raise ValueError("GET request should not have json body")
    return None


def delete() -> None:
    """
    Because a DELETE request should not contain a json object,
    If one is available in flask.request, a 400 will be thrown
    """
    if request.is_json:
        raise ValueError("DELETE request should not have json body")
    return None
