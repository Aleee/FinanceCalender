from decimal import Decimal


def dec_strcommaspace(dec: Decimal) -> str:
    return f"{dec:,.2f}".replace(",", " ").replace(".", ",")


def float_strcommaspace(fl: float, pos=None) -> str:
    return f"{fl:,.2f}".replace(",", " ").replace(".", ",")


def float_strpercentage(fl: float) -> str:
    return f"{fl:.1%}"


def str_rubstr(str: str) -> str:
    return str + " руб."
