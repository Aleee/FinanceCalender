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
    NAME = 4
    REMAINAMOUNT = 5
    TOTALAMOUNT = 6
    PERCENTAGE = 7
    DUEDATE = 8
    PAYMENTTYPE = 9
    CREATEDATE = 10
    DESCR = 11
    RESPONSIBLE = 12
    TODAYSHARE = 13
    TERMFLAGS = 14
    NOTES = 15
    LASTPAYMENTDATE = 16


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
    INVENTORY = 1114
    COMMISSION = 1115
    MEDEQREPAIR = 1116
    TOP_FINANCES = 2100
    TOP_INVESTMENT = 3100


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
    name: str                   # 4
    remainamount: Decimal       # 5
    totalamount: Decimal        # 6
    percentage: float           # 7
    duedate: QDate              # 8
    paymenttype: int            # 9
    createdate: QDate           # 10
    descr: str                  # 11
    responsible: str            # 12
    todayshare: Decimal         # 13
    termflags: TermRoleFlags    # 14
    notes: str                  # 15
    lastpaymentdate: QDate      # 16


def term_filter_flags(remainamount: Decimal, duedate: QDate, are_today_payments_present: bool) -> TermRoleFlags:
    current_date = get_current_date()
    term_flags = TermRoleFlags.NONE
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
