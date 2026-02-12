def str_bool(string: str, defaut: bool = False) -> bool:
    try:
        return bool(int(string))
    except ValueError, TypeError:
        return defaut
