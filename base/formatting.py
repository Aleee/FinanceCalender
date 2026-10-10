from decimal import Decimal, InvalidOperation
from typing import Optional


COLOR_STATEMENT: str = "#b03a2e"
COLOR_CALENDAR: str = "#1f5fa8"
COLOR_OK: str = "#2e7d32"
COLOR_HEADER_BG: str = "#e9ecef"
COLOR_WARNING: str = "#9a6700"
COLOR_WARNING_BG: str = "#fff4cc"
COLOR_PAIR_BG: str = "#fffbea"


def dec_strcommaspace(dec: Decimal, add_rub: bool = False) -> str:
    return f"{dec:,.2f}".replace(",", " ").replace(".", ",") + (" руб." if add_rub else "")


def dec_html(dec: Decimal) -> str:
    return dec_strcommaspace(dec, add_rub=True).replace(" ", "&nbsp;").replace("&nbsp;руб.", " руб.")


def int_strspace(integer: int) -> str:
    return f"{integer:,}".replace(",", " ")


def float_strpercentage(fl: float) -> str:
    return f"{fl:.1%}".replace(".", ",")


def str_rubstr(string: str) -> str:
    return string + " руб."


def str_decimal(raw: str) -> Optional[Decimal]:
    try:
        return Decimal(raw.replace(" ", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None
