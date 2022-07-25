from typing import Optional, Union, overload


@overload
def str_bool_to_bool(string: bool) -> bool:
    ...


@overload
def str_bool_to_bool(string: None) -> None:
    ...


@overload
def str_bool_to_bool(string: str) -> bool:
    ...


def str_bool_to_bool(string: Union[str, bool, None]) -> Optional[bool]:

    if isinstance(string, bool) or string is None:
        return string

    if string.lower() == "true":
        return True

    elif string.lower() == "false":
        return False

    raise TypeError(f"{string} cannot be converted to a boolean")
