from decimal import Decimal

import lovely_logger as log
from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from dataclasses import dataclass, field

from PySide6.QtSql import QSqlQuery


@dataclass(slots=True)
class Payment:
    day: date
    amount: Decimal


@dataclass(slots=True)
class Event:
    id: int
    category: int
    amount: Decimal
    created: date
    due: date
    payments: list[Payment] = field(default_factory=list)


@dataclass(slots=True)
class DailyDebt:
    day: date
    total: Decimal
    overdue: Decimal


@dataclass(slots=True)
class CategoryTimeline:
    total_changes: dict[date, Decimal] = field(default_factory=dict)
    overdue_changes: dict[date, Decimal] = field(default_factory=dict)


class DebtRepository:

    def load(self) -> list[Event]:
        events: dict[int, Event] = {}

        query: QSqlQuery = QSqlQuery()
        if not query.exec("SELECT id, category, totalamount, createdate, duedate FROM event WHERE type = 2 AND paymenttype <> 3"):
            log.e(f"Не удалось загрузить события для графика долга: {query.lastError().text()}")
        while query.next():
            try:
                events[query.value(0)] = Event(
                    id=query.value(0),
                    category=query.value(1),
                    amount=Decimal(query.value(2)),
                    created=date.fromisoformat(query.value(3)),
                    due=date.fromisoformat(query.value(4)),
                )
            except (ArithmeticError, ValueError, TypeError) as error:
                log.x(f"Не удалось разобрать событие id={query.value(0)} для графика долга: {error}")

        if not query.exec("SELECT eventid, paymentdate, sum FROM payment ORDER BY paymentdate"):
            log.e(f"Не удалось загрузить платежи для графика долга: {query.lastError().text()}")
        while query.next():
            event = events.get(query.value(0))
            if event is None:
                continue
            try:
                event.payments.append(Payment(date.fromisoformat(query.value(1)), Decimal(query.value(2))))
            except (ArithmeticError, ValueError, TypeError) as error:
                log.x(f"Не удалось разобрать платёж по событию id={query.value(0)} для графика долга: {error}")

        return list(events.values())


class DebtTimelineBuilder:

    def __init__(self, repository: DebtRepository) -> None:

        self.repository = repository
        self.events: list[Event] = []
        self.timelines: dict[int, CategoryTimeline] = {}

    def load(self) -> None:
        self.events = self.repository.load()
        self.timelines.clear()

        for event in self.events:
            timeline = self.timelines.setdefault(event.category, CategoryTimeline())
            self.process(event, timeline)

    @staticmethod
    def add_change(mapping: dict[date, Decimal], day: date, delta: Decimal) -> None:
        mapping[day] = mapping.get(day, Decimal("0")) + delta

    @staticmethod
    def remaining_at_due(event: Event, actual_due: date) -> Decimal:
        # Остаток долга на конец дня дедлайна (включая платежи в этот день)
        remaining = event.amount
        for payment in event.payments:
            if payment.day <= actual_due:
                remaining -= payment.amount
        return remaining

    def process(self, event: Event, timeline: CategoryTimeline) -> None:
        self.add_change(timeline.total_changes, event.created, event.amount)
        for payment in event.payments:
            self.add_change(timeline.total_changes, payment.day, -payment.amount)

        actual_due = max(event.due, event.created)
        remaining_at_due = self.remaining_at_due(event, actual_due)

        if remaining_at_due > 0:
            # СДВИГ: Просрочка фиксируется на СЛЕДУЮЩИЙ день после дедлайна
            overdue_start_day = actual_due + timedelta(days=1)
            self.add_change(timeline.overdue_changes, overdue_start_day, remaining_at_due)

            overdue_remaining = remaining_at_due
            for payment in event.payments:
                # Платежи, пришедшие строго со дня фактической просрочки
                if payment.day >= overdue_start_day:
                    amount_to_deduct = min(payment.amount, overdue_remaining)
                    if amount_to_deduct > 0:
                        self.add_change(timeline.overdue_changes, payment.day, -amount_to_deduct)
                        overdue_remaining -= amount_to_deduct


    def build(self, begin: date, end: date, categories: Iterable[int]) -> list[DailyDebt]:

        merged_total: defaultdict[date, Decimal] = defaultdict(Decimal)
        merged_overdue: defaultdict[date, Decimal] = defaultdict(Decimal)

        for category in categories:

            timeline = self.timelines.get(category)
            if timeline is None:
                continue

            # Даты позже 'end' не влияют ни на итог до начала диапазона, ни на сам диапазон
            for day, delta in timeline.total_changes.items():
                if day <= end:
                    merged_total[day] += delta
            for day, delta in timeline.overdue_changes.items():
                if day <= end:
                    merged_overdue[day] += delta

        total = sum((delta for day, delta in merged_total.items() if day < begin), Decimal("0"))
        overdue = sum((delta for day, delta in merged_overdue.items() if day < begin), Decimal("0"))

        result = []
        current = begin

        while current <= end:
            total += merged_total.get(current, Decimal("0"))
            overdue += merged_overdue.get(current, Decimal("0"))
            result.append(DailyDebt(current, total, overdue))
            current += timedelta(days=1)

        return result
