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


@dataclass
class HistorySummary:
    count: int = 0
    total: Decimal = Decimal(0)
    paid: Decimal = Decimal(0)
    unpaid_count: int = 0
    unpaid_sum: Decimal = Decimal(0)
    paid_in_year: Decimal = Decimal(0)


def payment_years(payments: list[ContractPayment]) -> list[int]:
    return sorted({payment.payment_date.year() for payment in payments}, reverse=True)


def payments_for_year(payments: list[ContractPayment], year: int | None) -> list[ContractPayment]:
    if year is None:
        return payments
    return [payment for payment in payments if payment.payment_date.year() == year]


def summarize_history(obligations: list[ContractObligation], payments: list[ContractPayment],
                      year: int | None = None) -> HistorySummary:
    summary = HistorySummary(count=len(obligations))
    for obligation in obligations:
        summary.total += obligation.total
        summary.paid += obligation.paid
        if obligation.remain > 0:
            summary.unpaid_count += 1
            summary.unpaid_sum += obligation.remain
    summary.paid_in_year = sum((payment.amount for payment in payments_for_year(payments, year)), Decimal(0))
    return summary
