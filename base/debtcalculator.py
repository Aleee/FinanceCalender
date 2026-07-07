import sqlite3
from decimal import Decimal

import lovely_logger as log
from collections import defaultdict
from datetime import date, timedelta

from dataclasses import dataclass, field
from datetime import date

from PySide6.QtCore import QDate
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


@dataclass
class CategoryTimeline:
    total_changes: dict[date, Decimal] = field(default_factory=dict)
    overdue_changes: dict[date, Decimal] = field(default_factory=dict)


class DebtRepository:

    def load(self) -> list[Event]:
        events: dict = {}

        query: QSqlQuery = QSqlQuery()
        query.exec("SELECT id, category, totalamount, createdate, duedate FROM event WHERE type = 2 AND paymenttype <> 3")
        while query.next():
            events[query.value(0)] = Event(
                id=query.value(0),
                category=query.value(1),
                amount=Decimal(query.value(2)),
                created=date.fromisoformat(query.value(3)),
                due=date.fromisoformat(query.value(4)),
            )

        query.exec("SELECT eventid, paymentdate, sum FROM payment ORDER BY paymentdate")
        while query.next():
            try:
                events[query.value(0)].payments.append(Payment(date.fromisoformat(query.value(1)), Decimal(query.value(2))))
            except KeyError:
                continue

        return list(events.values())


class DebtTimelineBuilder:

    def __init__(self, repository):

        self.repository = repository
        self.events = []
        self.timelines = {}

    def load(self):
        self.events = self.repository.load()
        self.timelines.clear()

        for event in self.events:
            timeline = self.timelines.setdefault(event.category, CategoryTimeline())
            self.process(event, timeline)

    @staticmethod
    def add_change(mapping, day, delta):
        mapping[day] = mapping.get(day, Decimal("0")) + delta

    def process(self, event, timeline):
        self.add_change(timeline.total_changes, event.created, event.amount)
        for payment in event.payments:
            self.add_change(timeline.total_changes, payment.day, -payment.amount)

        actual_due = max(event.due, event.created)

        # Считаем остаток долга на конец дня дедлайна (включая платежи в этот день)
        remaining_at_due = event.amount
        for payment in event.payments:
            if payment.day <= actual_due:
                remaining_at_due -= payment.amount

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


    def build(self, begin, end, categories):

        merged_total = defaultdict(Decimal)
        merged_overdue = defaultdict(Decimal)

        for category in categories:

            timeline = self.timelines.get(category)
            if timeline is None:
                continue

            for day, delta in timeline.total_changes.items():
                merged_total[day] += delta
            for day, delta in timeline.overdue_changes.items():
                merged_overdue[day] += delta

        total = self.initial_total(begin, categories)
        overdue = self.initial_overdue(begin, categories)

        result = []
        current = begin

        while current <= end:
            total += merged_total.get(current, Decimal("0"))
            overdue += merged_overdue.get(current, Decimal("0"))
            result.append(DailyDebt(current, total, overdue))
            current += timedelta(days=1)

        return result


    def initial_total(self, begin, categories):
        total = 0
        for event in self.events:
            if event.category not in categories:
                continue
            if event.created >= begin:
                continue
            total += event.amount
            for payment in event.payments:
                if payment.day < begin:
                    total -= payment.amount
        return total

    def initial_overdue(self, begin, categories):
        overdue = Decimal("0")
        for event in self.events:
            if event.category not in categories:
                continue

            actual_due = max(event.due, event.created)
            overdue_start_day = actual_due + timedelta(days=1)

            # Если день начала просрочки еще не наступил относительно 'begin', пропускаем
            if overdue_start_day >= begin:
                continue

            remaining_at_due = event.amount
            for payment in event.payments:
                if payment.day <= actual_due:
                    remaining_at_due -= payment.amount

            if remaining_at_due > 0:
                overdue += remaining_at_due
                overdue_remaining = remaining_at_due
                for payment in event.payments:
                    if overdue_start_day <= payment.day < begin:
                        amount_to_deduct = min(payment.amount, overdue_remaining)
                        overdue -= amount_to_deduct
                        overdue_remaining -= amount_to_deduct
        return overdue
