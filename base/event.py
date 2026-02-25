from dataclasses import dataclass
from enum import Flag, auto, IntEnum
from decimal import Decimal

from PySide6.QtCore import QDate

from base.date import get_current_date, get_date_diff, days_to_weekend, days_to_month


class PaymentType(IntEnum):
    NORMAL = auto()
    ADVANCE = auto()


class RowType(IntEnum):
    HEADER = auto()
    EVENT = auto()
    FOOTER = auto()
    FINALFOOTER = auto()


class EventField(IntEnum):
    RECEIVER = 0
    TYPE = 1
    ID = 2
    CATEGORY = 3
    SUBCATEGORY = 4
    NAME = 5
    REMAINAMOUNT = 6
    TOTALAMOUNT = 7
    PERCENTAGE = 8
    DUEDATE = 9
    PAYMENTTYPE = 10
    CREATEDATE = 11
    DESCR = 12
    RESPONSIBLE = 13
    TODAYSHARE = 14
    TERMFLAGS = 15
    NOTES = 16
    LASTPAYMENTDATE = 17
    NDS = 18


class EventCategory(IntEnum):
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


class EventFinanceSubcategory(IntEnum):
    LOAN = 1
    LEASING = 2
    INTEREST = 3
    FOUNDERLOAN = 4


class TermRoleFlags(Flag):
    PAID = auto()
    NOTPAID = auto()
    DUE = auto()
    TODAY = auto()
    WEEK = auto()
    MONTH = auto()
    NONE = 0


@dataclass()
class Event:

    receiver: str               # 0
    type: int                   # 1
    id: int                     # 2
    category: int               # 3
    subcategory: int            # 4
    name: str                   # 5
    remainamount: Decimal       # 6
    totalamount: Decimal        # 7
    percentage: float           # 8
    duedate: QDate              # 9
    paymenttype: int            # 10
    createdate: QDate           # 11
    descr: str                  # 12
    responsible: str            # 13
    todayshare: Decimal         # 14
    termflags: TermRoleFlags    # 15
    notes: str                  # 16
    lastpaymentdate: QDate      # 17
    nds: int                    # 18


def term_filter_flags(remainamount: Decimal, duedate: QDate, are_today_payments_present: bool) -> TermRoleFlags:
    current_date: QDate = get_current_date()
    term_flags: TermRoleFlags = TermRoleFlags.NONE
    # Проверка на оплаченность
    if remainamount <= 0 and not are_today_payments_present:
        term_flags |= TermRoleFlags.PAID
    else:
        term_flags |= TermRoleFlags.NOTPAID
        # Проверка по дате
        date_diff = get_date_diff(current_date, duedate)
        if date_diff < 0:
            term_flags |= TermRoleFlags.DUE
        if date_diff == 0:
            term_flags |= TermRoleFlags.TODAY
        if -1 < date_diff <= days_to_weekend(current_date):
            term_flags |= TermRoleFlags.WEEK
        if -1 < date_diff <= days_to_month(current_date):
            term_flags |= TermRoleFlags.MONTH
    return term_flags
