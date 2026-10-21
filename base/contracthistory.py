from dataclasses import dataclass
from decimal import Decimal

from PySide6.QtCore import QDate


@dataclass
class ContractObligation:
    event_id: int
    name: str
    due_date: QDate
    total: Decimal
    paid: Decimal
    document_name: str
    contract_id: int
    contract_number: str
    contract_date: QDate

    @property
    def remain(self) -> Decimal:
        return self.total - self.paid


@dataclass
class ContractPayment:
    payment_id: int
    event_id: int
    event_name: str
    payment_date: QDate
    amount: Decimal
    document_name: str
    contract_id: int
    contract_number: str
    contract_date: QDate


def payment_years(payments: list[ContractPayment]) -> list[int]:
    return sorted({payment.payment_date.year() for payment in payments}, reverse=True)


def payments_for_year(payments: list[ContractPayment], year: int | None) -> list[ContractPayment]:
    if year is None:
        return payments
    return [payment for payment in payments if payment.payment_date.year() == year]
