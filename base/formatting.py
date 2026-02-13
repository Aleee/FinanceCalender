from decimal import Decimal


def dec_strcommaspace(dec: Decimal) -> str:
    return f"{dec:,.2f}".replace(",", " ").replace(".", ",")


def float_strcommaspace(fl: float) -> str:
    return f"{fl:,.2f}".replace(",", " ").replace(".", ",")


def float_strpercentage(fl: float) -> str:
    return f"{fl:.1%}"


def str_rubstr(string: str) -> str:
    return string + " руб."
