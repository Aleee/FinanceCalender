from decimal import Decimal
from enum import IntEnum, IntFlag, auto
from typing import NamedTuple

from PySide6.QtCore import QDate

from base.date import date_str, days_to_month, days_to_weekend, get_date_diff


class LiabilityCategory(IntEnum):
    TOP_CURRENT = 1000
    SALARIES = 1101
    TAXES = 1102
    CONSUMABLES = 1103
    ENERGY = 1104
    MARKETING = 1105
    OFFICERENT = 1106
    ROOMRENT = 1107
    EQUIPMENT = 1108
    CURRENT = 1109
    BUILDINGMAINT = 1110
    BANKING = 1111
    TELECOM = 1112
    TRAINING = 1113
    THIRDPARTYSERVICES = 1114
    COMMISSION = 1115
    MEDEQREPAIR = 1116
    TOP_FINANCES = 2100
    TOP_INVESTMENT = 3100


CATEGORY_NAMES = {
    LiabilityCategory.TOP_CURRENT: "1.   Текущая деятельность",
    LiabilityCategory.SALARIES: "1.1.  Заработная плата с налогами на з/п",
    LiabilityCategory.TAXES: "1.2.  Налоги и сборы",
    LiabilityCategory.CONSUMABLES: "1.3.  Расходные материалы для медицинских центров",
    LiabilityCategory.ENERGY: "1.4.  Энергоносители",
    LiabilityCategory.MARKETING: "1.5.  Расходы на маркетинг",
    LiabilityCategory.OFFICERENT: "1.6.  Расходы по аренде офисов",
    LiabilityCategory.ROOMRENT: "1.7.  Расходы по аренде помещений",
    LiabilityCategory.EQUIPMENT: "1.8.  Обслуживание оргтехники",
    LiabilityCategory.CURRENT: "1.9.  Текущие расходы",
    LiabilityCategory.BUILDINGMAINT: "1.10.  Расходы на обслуживание зданий и помещений",
    LiabilityCategory.BANKING: "1.11.  Банковские расходы",
    LiabilityCategory.TELECOM: "1.12.  Услуги связи",
    LiabilityCategory.TRAINING: "1.13.  Расходы на обучение и повышение квалификации",
    LiabilityCategory.THIRDPARTYSERVICES: "1.14.  Услуги сторонних организаций",
    LiabilityCategory.COMMISSION: "1.15.  Комиссионные расходы",
    LiabilityCategory.MEDEQREPAIR: "1.16.  Ремонт, обслуживание и страхование мед. оборудования",
    LiabilityCategory.TOP_FINANCES: "2.    Финансовая деятельность",
    LiabilityCategory.TOP_INVESTMENT: "3.    Инвестиционная деятельность",
}


def category_section(category: int) -> int:
    return category // 1000


def is_top_level_category(category: int) -> bool:
    return category % 100 == 0


NDS_VALUE = {
    LiabilityCategory.TOP_CURRENT: 0,
    LiabilityCategory.SALARIES: 0,
    LiabilityCategory.TAXES: 0,
    LiabilityCategory.CONSUMABLES: 10,
    LiabilityCategory.ENERGY: 20,
    LiabilityCategory.MARKETING: 20,
    LiabilityCategory.OFFICERENT: 20,
    LiabilityCategory.ROOMRENT: 20,
    LiabilityCategory.EQUIPMENT: 20,
    LiabilityCategory.CURRENT: 20,
    LiabilityCategory.BUILDINGMAINT: 20,
    LiabilityCategory.BANKING: 0,
    LiabilityCategory.TELECOM: 25,
    LiabilityCategory.TRAINING: 20,
    LiabilityCategory.THIRDPARTYSERVICES: 20,
    LiabilityCategory.COMMISSION: 20,
    LiabilityCategory.MEDEQREPAIR: 20,
    LiabilityCategory.TOP_FINANCES: 0,
    LiabilityCategory.TOP_INVESTMENT: 20,
}


class LiabilityFinanceSubcategory(IntEnum):
    LOAN = 1
    LEASING = 2
    INTEREST = 3
    FOUNDERLOAN = 4


class FilterFlags(IntFlag):
    PAID = auto()
    NOTPAID = auto()
    DUE = auto()
    TODAY = auto()
    WEEK = auto()
    MONTH = auto()
    NONE = 0


class TermCategory(IntEnum):
    UNPAID = 0
    DUE = 1
    TODAY = 2
    WEEK = 3
    MONTH = 4
    PAID = 5


class RowType(IntEnum):
    HEADER = auto()
    LIABILITY = auto()
    FOOTER = auto()
    FINALFOOTER = auto()


class HeaderFooterSubtype(IntEnum):
    ORDINARY = auto()
    TOPLEVELWITHEVENTS = auto()
    TOPLEVELNOEVENTS = auto()


class PaymentType(IntEnum):
    NORMAL = auto()
    ADVANCE = auto()
    REFUND = auto()


PAYMENTTYPE_NAMES = {
    PaymentType.NORMAL: "По факту",
    PaymentType.ADVANCE: "Предоплата",
    PaymentType.REFUND: "Возврат",
}


def calculate_filterflags(remainamount: Decimal, duedate: QDate, are_today_payments_present: bool, current_date: QDate) -> FilterFlags:
    filter_flags: FilterFlags = FilterFlags.NONE
    # Проверка на оплаченность
    if remainamount <= 0 and not are_today_payments_present:
        filter_flags |= FilterFlags.PAID
    else:
        filter_flags |= FilterFlags.NOTPAID
        # Проверка по дате
        date_diff = get_date_diff(current_date, duedate)
        if date_diff < 0:
            filter_flags |= FilterFlags.DUE
        if date_diff == 0:
            filter_flags |= FilterFlags.TODAY
        if -1 < date_diff <= days_to_weekend(current_date):
            filter_flags |= FilterFlags.WEEK
        if -1 < date_diff <= days_to_month(current_date):
            filter_flags |= FilterFlags.MONTH
    return filter_flags


class LiabilityRow(NamedTuple):
    category: int
    receiver: str
    responsible: int
    featured: bool
    hidden: bool
    remain: Decimal
    today_share: Decimal
    last_payment_date: str
    filter_flags: FilterFlags


TERM_FLAGS = {
    TermCategory.DUE: FilterFlags.DUE,
    TermCategory.TODAY: FilterFlags.TODAY,
    TermCategory.WEEK: FilterFlags.WEEK,
    TermCategory.MONTH: FilterFlags.MONTH,
}


def paid_threshold(current_date: QDate, paid_months_toshow: int) -> str:
    return date_str(current_date.addMonths(-paid_months_toshow))


def matches_term(term: TermCategory, liability: LiabilityRow, threshold: str) -> bool:
    if term == TermCategory.PAID:
        return FilterFlags.PAID in liability.filter_flags and liability.last_payment_date > threshold
    if FilterFlags.NOTPAID not in liability.filter_flags:
        return False
    term_flag = TERM_FLAGS.get(term)
    return term_flag is None or term_flag in liability.filter_flags


def matches_category(category: int, liability: LiabilityRow) -> bool:
    return category % 1000 == 0 or liability.category == category


def matches_details(liability: LiabilityRow, receiver: str, responsible: int, paid_today: bool, featured: bool) -> bool:
    if receiver and receiver not in liability.receiver:
        return False
    if responsible and liability.responsible != int(responsible):
        return False
    if paid_today and not liability.today_share:
        return False
    if featured and not liability.featured:
        return False
    return True


def matches_filters(liability: LiabilityRow, term: TermCategory, category: int, receiver: str, responsible: int,
                    paid_today: bool, featured: bool, threshold: str) -> bool:
    return (matches_term(term, liability, threshold)
            and matches_category(category, liability)
            and matches_details(liability, receiver, responsible, paid_today, featured))
