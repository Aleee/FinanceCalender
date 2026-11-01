from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, NamedTuple, Optional

from base.formatting import str_decimal

MONTHS_COUNT = 12


class CategoryDef(NamedTuple):
    children: tuple[int, ...]
    row_label: str
    title: str
    bold: bool
    counts_execution: bool


FINPLAN_STRUCTURE = {
    10000: CategoryDef((), "1.", "Остаток средств на начало периода", True, False),
    20000: CategoryDef((21000, 22000, 23000), "2.", "Поступление денежных средств", True, True),
    21000: CategoryDef((), "2.1.", "выручка от реализации услуг", False, True),
    22000: CategoryDef((), "2.2.", "прочие доходы", False, True),
    23000: CategoryDef((23100, 23200), "2.3.", "кредиты и займы", False, True),
    23100: CategoryDef((), "2.3.1.", "овердрафт", False, True),
    23200: CategoryDef((), "2.3.2.", "кредит", False, True),
    30000: CategoryDef((31000, 32000, 33000), "3.", "Расходование денежных средств", True, True),
    31000: CategoryDef((31100, 31200), "3.1.", "текущая деятельность", True, True),
    31100: CategoryDef((31101, 31102, 31103), "3.1.1.", "переменные затраты", True, True),
    31101: CategoryDef((), "3.1.1.1.", "заработная плата с налогами", False, True),
    31102: CategoryDef((), "3.1.1.2.", "материалы", False, True),
    31103: CategoryDef((), "3.1.1.3.", "услуги сторонних организаций", False, True),
    31200: CategoryDef(
        (31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213),
        "3.1.2.", "постоянные затраты", True, True,
    ),
    31201: CategoryDef((), "3.1.2.1", "налоги", False, True),
    31202: CategoryDef((), "3.1.2.2", "энергоносители", False, True),
    31203: CategoryDef((), "3.1.2.3", "маркетинг", False, True),
    31204: CategoryDef((), "3.1.2.4", "аренда офиса", False, True),
    31205: CategoryDef((), "3.1.2.5", "аренда помещений", False, True),
    31206: CategoryDef((), "3.1.2.6", "IT обслуживание", False, True),
    31207: CategoryDef((), "3.1.2.7", "обеспечение текущей деятельности", False, True),
    31208: CategoryDef((), "3.1.2.8", "обслуживание здания", False, True),
    31209: CategoryDef((), "3.1.2.9", "банковские расходы", False, True),
    31210: CategoryDef((), "3.1.2.10", "услуги связи", False, True),
    31211: CategoryDef((), "3.1.2.11", "комиссионное вознаграждение", False, True),
    31212: CategoryDef((), "3.1.2.12", "обучение персонала", False, True),
    31213: CategoryDef((), "3.1.2.13", "техническое обслуживание и страхование оборудования", False, True),
    32000: CategoryDef((32100, 32200, 32300), "3.2.", "финансовая деятельность", True, True),
    32100: CategoryDef((32101, 32102), "3.2.1.", "погашение кредитных обязательств", False, True),
    32101: CategoryDef((), "3.2.1.1", "погашение кредитов", False, True),
    32102: CategoryDef((), "3.2.1.2", "погашение лизинга", False, True),
    32200: CategoryDef((), "3.2.2", "погашение процентов по кредитам, займам", False, True),
    32300: CategoryDef((), "3.2.3", "погашение займов учредителям", False, True),
    33000: CategoryDef((), "3.3.", "инвестиционная деятельность", True, True),
    40000: CategoryDef((), "4.", "Остаток средств на конец периода", True, False),
}


def to_amount(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    amount = value if isinstance(value, Decimal) else str_decimal(str(value))
    try:
        if amount is None or not amount.is_finite():
            return None
        amount = amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
    except InvalidOperation:
        return None
    return Decimal(int(amount)) if amount == amount.to_integral_value() else amount


def stored_amount(amount: Optional[Decimal]) -> int | float | None:
    if amount is None:
        return None
    return int(amount) if amount == amount.to_integral_value() else float(amount)
