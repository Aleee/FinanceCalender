from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QDate


class PaymentDueType(str, Enum):
    PREPAYMENT = "PREPAYMENT"  # Предоплата / Сроки явно не определены
    RELATIVE = "RELATIVE"      # Относительные сроки (привязка к событию)
    FIXED = "FIXED"            # Фиксированные сроки (привязка к календарю)


class DaysType(str, Enum):
    CALENDAR = "CALENDAR"      # календарные
    BANKING = "BANKING"        # банковские
    WORKING = "WORKING"        # рабочие


class MonthType(str, Enum):
    CURRENT = "CURRENT"        # отчетный
    NEXT = "NEXT"              # следующий
    PREVIOUS = "PREVIOUS"      # предыдущий


@dataclass
class ContractDocumentData:
    document_id: int
    contractor_id: int
    contractor_name: str
    contract_id: int
    contract_number: str
    contract_date: QDate
    document_type: int
    position_id: int
    document_name: str
    description: str

    payment_type: PaymentDueType
    days_count: Optional[int] = 0
    days_type: Optional[DaysType] = None
    has_calendar_condition: bool = False
    month_day: Optional[int] = None
    month_type: Optional[MonthType] = None

@dataclass
class ContractInfo:
    contractor_id: int
    contractor_name: str
    contract_id: int
    contract_number: str
    contract_date: QDate

@dataclass
class DocumentTitle:
    document_id: int
    contractor_id: int
    contractor_name: str
    contract_id: int
    contract_number: str
    contract_date: QDate
    document_name: str

@dataclass
class SavedContractValues:
    contractdocumentid: int
    receiver: str
    category: int
    subcategory: int
    name: str
    nds: int
    paymenttype: int
    descr: str
    responsible: int
    hidden: int
