from typing import Any


def str_bool(string: Any, defaut: bool = False, strict: bool = False) -> bool:
    if not strict and type(string) is bool:
        return string
    try:
        return bool(int(string))
    except ValueError, TypeError:
        return defaut


def str_int(string: Any) -> int:
    try:
        return int(string)
    except ValueError, TypeError:
        return 0
