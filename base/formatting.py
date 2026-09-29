from decimal import Decimal, InvalidOperation
from typing import Optional


def dec_strcommaspace(dec: Decimal, add_rub: bool = False) -> str:
    return f"{dec:,.2f}".replace(",", " ").replace(".", ",") + (" руб." if add_rub else "")


def str_strcommaspace(string: str) -> str:
    return dec_strcommaspace(Decimal(string))


def int_strspace(integer: int) -> str:
    return f"{integer:,}".replace(",", " ")


def float_strcommaspace(fl: float, pos: int | None = None) -> str:
    return f"{fl:,.2f}".replace(",", " ").replace(".", ",")


def float_strpercentage(fl: float) -> str:
    return f"{fl:.1%}"


def str_rubstr(string: str) -> str:
    return string + " руб."


def str_decimal(raw: str) -> Optional[Decimal]:
    try:
        return Decimal(raw.replace(" ", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None
