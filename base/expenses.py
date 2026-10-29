from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, Hashable, Iterable

import lovely_logger as log
from PySide6.QtSql import QSqlQuery

from base.liability import category_section


@dataclass(slots=True)
class ExpensePayment:
    category: int
    receiver: str
    name: str
    day: date
    amount: Decimal
    eventid: int = 0


@dataclass(slots=True)
class ExpenseStats:
    count: int = 0
    amount: Decimal = Decimal(0)
    refunds: Decimal = Decimal(0)

    def add(self, payment: ExpensePayment) -> None:
        self.count += 1
        self.amount += payment.amount
        if payment.amount < 0:
            self.refunds -= payment.amount


@dataclass(slots=True)
class StructureRow:
    categories: tuple[int, ...]
    amount: Decimal
    previous: Decimal
    count: int
    share: Decimal


class ExpenseRepository:

    def load(self, start: date, end: date) -> list[ExpensePayment]:
        payments: list[ExpensePayment] = []
        query = QSqlQuery()
        query.prepare("SELECT E.category, E.receiver, E.name, P.paymentdate, P.sum, E.id FROM payment AS P "
                      "INNER JOIN event AS E ON P.eventid = E.id WHERE P.paymentdate BETWEEN ? AND ?")
        query.addBindValue(start.isoformat())
        query.addBindValue(end.isoformat())
        if not query.exec():
            log.e(f"Не удалось загрузить оплаты для структуры расходов: {query.lastError().text()}")
            return payments
        while query.next():
            try:
                payments.append(ExpensePayment(
                    category=query.value(0),
                    receiver=query.value(1) if isinstance(query.value(1), str) else "",
                    name=query.value(2) if isinstance(query.value(2), str) else "",
                    day=date.fromisoformat(query.value(3)),
                    amount=Decimal(query.value(4)),
                    eventid=int(query.value(5)),
                ))
            except (ArithmeticError, ValueError, TypeError) as error:
                log.x(f"Не удалось разобрать оплату для структуры расходов: {error}")
        return payments


def previous_period(start: date, end: date) -> tuple[date, date]:
    if start.day == 1 and (end + timedelta(days=1)).day == 1:
        months = (end.year * 12 + end.month) - (start.year * 12 + start.month) + 1
        year, month = divmod(start.year * 12 + start.month - months - 1, 12)
        return date(year, month + 1, 1), start - timedelta(days=1)
    length = (end - start).days + 1
    return start - timedelta(days=length), start - timedelta(days=1)


def month_index(day: date) -> int:
    return day.year * 12 + day.month


def month_range(start: date, end: date) -> list[int]:
    return list(range(month_index(start), month_index(end) + 1))


def in_period(payments: Iterable[ExpensePayment], start: date, end: date) -> list[ExpensePayment]:
    return [payment for payment in payments if start <= payment.day <= end]


def filter_payments(payments: Iterable[ExpensePayment], categories: set[int], receiver_part: str,
                    skip_sections: set[int]) -> list[ExpensePayment]:
    receiver_part = receiver_part.strip().lower()
    return [payment for payment in payments
            if (not categories or payment.category in categories)
            and category_section(payment.category) not in skip_sections
            and receiver_part in payment.receiver.lower()]


def collect_stats(payments: Iterable[ExpensePayment], key: Callable[[ExpensePayment], Hashable]) -> dict[Hashable, ExpenseStats]:
    result: dict[Hashable, ExpenseStats] = {}
    for payment in payments:
        result.setdefault(key(payment), ExpenseStats()).add(payment)
    return result


def total_stats(payments: Iterable[ExpensePayment]) -> ExpenseStats:
    stats = ExpenseStats()
    for payment in payments:
        stats.add(payment)
    return stats


def share_of(amount: Decimal, total: Decimal) -> Decimal:
    return amount / total if total else Decimal(0)


def change_share(amount: Decimal, previous: Decimal) -> Decimal | None:
    return (amount - previous) / abs(previous) if previous else None


def monthly_average(amount: Decimal, start: date, end: date) -> Decimal:
    return amount / Decimal((end - start).days + 1) * Decimal("30.4375")


def peak_month(payments: Iterable[ExpensePayment]) -> tuple[int, Decimal] | None:
    by_month = collect_stats(payments, lambda payment: month_index(payment.day))
    if not by_month:
        return None
    month = max(by_month, key=lambda key: by_month[key].amount)
    return month, by_month[month].amount


def rank_categories(payments: Iterable[ExpensePayment], limit: int) -> list[int]:
    totals = collect_stats(payments, lambda payment: payment.category)
    ranked = sorted(totals, key=lambda category: totals[category].amount, reverse=True)
    return ranked[:limit]


def build_structure(current: dict[Hashable, ExpenseStats], previous: dict[Hashable, ExpenseStats],
                    merge_below: Decimal | None = None) -> list[StructureRow]:
    total = sum((stats.amount for stats in current.values()), Decimal(0))
    rows: list[StructureRow] = []
    for category in current.keys() | previous.keys():
        stats = current.get(category, ExpenseStats())
        previous_amount = previous[category].amount if category in previous else Decimal(0)
        if not stats.count and not previous_amount:
            continue
        rows.append(StructureRow((category,), stats.amount, previous_amount, stats.count, share_of(stats.amount, total)))
    rows.sort(key=lambda row: (-row.amount, -row.previous, row.categories))

    if merge_below is None:
        return rows
    small = [row for row in rows if row.share < merge_below]
    if len(small) < 2:
        return rows
    merged = StructureRow(tuple(category for row in small for category in row.categories),
                          sum((row.amount for row in small), Decimal(0)),
                          sum((row.previous for row in small), Decimal(0)),
                          sum(row.count for row in small),
                          sum((row.share for row in small), Decimal(0)))
    return [row for row in rows if row.share >= merge_below] + [merged]


def stack_months(payments: Iterable[ExpensePayment], top: list[int]) -> dict[int | None, dict[int, Decimal]]:
    result: dict[int | None, dict[int, Decimal]] = {}
    for payment in payments:
        key = payment.category if payment.category in top else None
        series = result.setdefault(key, {})
        month = month_index(payment.day)
        series[month] = series.get(month, Decimal(0)) + payment.amount
    return result
