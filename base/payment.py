from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum

from PySide6.QtCore import QDate

from base.liability import LiabilityCategory


class PaymentField(IntEnum):
    ID = 0
    EVENT = 1
    PAYMENT_DATE = 2
    SUM = 3
    CREATE_DATE = 4


@dataclass()
class Payment:
    payment_id: int
    event_id: int
    payment_date: QDate
    payment_sum: Decimal
    create_date: QDate


@dataclass()
class PaymentEntry:
    amount: Decimal
    descr: str
    receiver: str = ""
    payment_id: int | None = None
    event_id: int | None = None
    details: str = ""
    fee_category: LiabilityCategory | None = None
