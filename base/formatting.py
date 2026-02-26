from decimal import Decimal


def dec_strcommaspace(dec: Decimal) -> str:
    return f"{dec:,.2f}".replace(",", " ").replace(".", ",")


def int_strspace(integer: int) -> str:
    return f"{integer:,}".replace(",", " ")


def float_strcommaspace(fl: float, pos: int | None = None) -> str:
    return f"{fl:,.2f}".replace(",", " ").replace(".", ",")


def float_strpercentage(fl: float) -> str:
    return f"{fl:.1%}"


def str_rubstr(string: str) -> str:
    return string + " руб."
