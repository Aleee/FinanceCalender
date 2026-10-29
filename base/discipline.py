from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import IntEnum
from typing import Callable, Hashable, Iterable

from base.debtcalculator import Event


class DelayBucket(IntEnum):
    IN_TIME = 0
    WEEK = 1
    MONTH = 2
    LONG = 3


BUCKET_NAMES = {
    DelayBucket.IN_TIME: "В срок или раньше",
    DelayBucket.WEEK: "1–7 дней",
    DelayBucket.MONTH: "8–30 дней",
    DelayBucket.LONG: "Больше 30 дней",
}


def delay_bucket(delay: int) -> DelayBucket:
    if delay <= 0:
        return DelayBucket.IN_TIME
    if delay <= 7:
        return DelayBucket.WEEK
    if delay <= 30:
        return DelayBucket.MONTH
    return DelayBucket.LONG


@dataclass(slots=True)
class ClosedPayment:
    event: Event
    paid_date: date

    @property
    def delay(self) -> int:
        return (self.paid_date - self.event.due).days

    @property
    def bucket(self) -> DelayBucket:
        return delay_bucket(self.delay)


@dataclass(slots=True)
class OverduePayment:
    event: Event
    remain: Decimal
    days: int


@dataclass(slots=True)
class DisciplineStats:
    count: int = 0
    amount: Decimal = Decimal(0)
    late_count: int = 0
    late_amount: Decimal = Decimal(0)
    late_delay_sum: int = 0
    max_delay: int = 0
    buckets: dict[DelayBucket, int] = field(default_factory=lambda: dict.fromkeys(DelayBucket, 0))
    bucket_amounts: dict[DelayBucket, Decimal] = field(default_factory=lambda: dict.fromkeys(DelayBucket, Decimal(0)))

    def add(self, item: ClosedPayment) -> None:
        delay = item.delay
        self.count += 1
        self.amount += item.event.amount
        self.max_delay = max(self.max_delay, delay)
        self.buckets[item.bucket] += 1
        self.bucket_amounts[item.bucket] += item.event.amount
        if delay > 0:
            self.late_count += 1
            self.late_amount += item.event.amount
            self.late_delay_sum += delay

    @property
    def average_late_delay(self) -> Decimal:
        return Decimal(self.late_delay_sum) / self.late_count if self.late_count else Decimal(0)

    @property
    def late_count_share(self) -> Decimal:
        return Decimal(self.late_count) / self.count if self.count else Decimal(0)

    @property
    def late_amount_share(self) -> Decimal:
        return self.late_amount / self.amount if self.amount else Decimal(0)

    @property
    def in_time_share(self) -> Decimal:
        return Decimal(self.buckets[DelayBucket.IN_TIME]) / self.count if self.count else Decimal(0)

    @property
    def in_time_amount_share(self) -> Decimal:
        return self.bucket_amounts[DelayBucket.IN_TIME] / self.amount if self.amount else Decimal(0)


def filter_events(events: Iterable[Event], categories: set[int], receiver_part: str) -> list[Event]:
    receiver_part = receiver_part.strip().lower()
    return [event for event in events
            if (not categories or event.category in categories) and receiver_part in event.receiver.lower()]


def find_closed(events: Iterable[Event], start: date, end: date) -> list[ClosedPayment]:
    result: list[ClosedPayment] = []
    for event in events:
        if event.amount <= 0 or not event.payments:
            continue
        if sum((payment.amount for payment in event.payments), Decimal(0)) < event.amount:
            continue
        paid_date = max(payment.day for payment in event.payments)
        if start <= paid_date <= end:
            result.append(ClosedPayment(event, paid_date))
    return result


def find_overdue(events: Iterable[Event], today: date) -> list[OverduePayment]:
    result: list[OverduePayment] = []
    for event in events:
        if event.amount <= 0 or event.due >= today:
            continue
        remain = event.amount - sum((payment.amount for payment in event.payments), Decimal(0))
        if remain > 0:
            result.append(OverduePayment(event, remain, (today - event.due).days))
    return sorted(result, key=lambda item: item.days, reverse=True)


def collect_stats(items: Iterable[ClosedPayment], key: Callable[[ClosedPayment], Hashable]) -> dict[Hashable, DisciplineStats]:
    result: dict[Hashable, DisciplineStats] = {}
    for item in items:
        result.setdefault(key(item), DisciplineStats()).add(item)
    return result


def total_stats(items: Iterable[ClosedPayment]) -> DisciplineStats:
    stats = DisciplineStats()
    for item in items:
        stats.add(item)
    return stats
