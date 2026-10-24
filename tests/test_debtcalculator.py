import sqlite3
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from base.debtcalculator import DebtRepository, DebtTimelineBuilder, Event, Payment
from base.liability import PaymentType, RowType
from base.version import DB_VERSION
from tests.dbtools import create_db


class FakeRepository:

    def __init__(self, events: list[Event]):
        self.events = events

    def load(self) -> list[Event]:
        return self.events


def d(day: int) -> date:
    return date(2026, 10, day)


def make_event(amount="100", created=1, due=10, payments=(), category=1, event_id=1) -> Event:
    return Event(event_id, category, Decimal(amount), d(created), d(due),
                 [Payment(d(day), Decimal(sum_)) for day, sum_ in payments])


def build(events: list[Event], begin=1, end=15, categories=(1,)):
    builder = DebtTimelineBuilder(FakeRepository(events))
    builder.load()
    return {item.day.day: (item.total, item.overdue) for item in builder.build(d(begin), d(end), categories)}


def test_paid_in_time_has_no_overdue():
    result = build([make_event(payments=[(5, "100")])])
    assert result[1] == (Decimal(100), 0)
    assert result[4] == (Decimal(100), 0)
    assert result[5] == (0, 0)
    assert all(overdue == 0 for _, overdue in result.values())


def test_unpaid_becomes_overdue_next_day_after_due():
    result = build([make_event()])
    assert result[10] == (Decimal(100), 0)
    assert result[11] == (Decimal(100), Decimal(100))
    assert result[15] == (Decimal(100), Decimal(100))


def test_payment_on_due_day_is_not_overdue():
    result = build([make_event(payments=[(10, "100")])])
    assert result[9] == (Decimal(100), 0)
    assert result[10] == (0, 0)
    assert result[11] == (0, 0)


def test_partial_payment_before_due_leaves_rest_overdue():
    result = build([make_event(payments=[(5, "30")])])
    assert result[5] == (Decimal(70), 0)
    assert result[11] == (Decimal(70), Decimal(70))


def test_partial_payment_after_due_reduces_overdue():
    result = build([make_event(payments=[(15, "40")])])
    assert result[14] == (Decimal(100), Decimal(100))
    assert result[15] == (Decimal(60), Decimal(60))


def test_full_payment_after_due_closes_overdue():
    result = build([make_event(payments=[(12, "100")])])
    assert result[11] == (Decimal(100), Decimal(100))
    assert result[12] == (0, 0)


def test_overpayment_does_not_make_overdue_negative():
    result = build([make_event(payments=[(15, "150")])])
    assert result[15] == (Decimal(-50), 0)


def test_refund_of_payment_after_due_does_not_change_overdue():
    result = build([make_event(payments=[(12, "-20")])])
    assert result[12] == (Decimal(120), Decimal(100))


def test_due_before_created_counts_from_created_day():
    result = build([make_event(created=10, due=1)])
    assert result[10] == (Decimal(100), 0)
    assert result[11] == (Decimal(100), Decimal(100))


def test_range_starts_with_balance_accumulated_before_begin():
    first = build([make_event(payments=[(3, "30")])], begin=12)[12]
    assert first == (Decimal(70), Decimal(70))


def test_changes_after_end_are_ignored():
    result = build([make_event(payments=[(14, "100")])], end=9)
    assert result[9] == (Decimal(100), 0)
    assert 10 not in result


def test_build_returns_every_day_of_range():
    builder = DebtTimelineBuilder(FakeRepository([make_event()]))
    builder.load()
    days = [item.day for item in builder.build(d(3), d(7), [1])]
    assert days == [d(3) + timedelta(days=shift) for shift in range(5)]


def test_categories_are_summed_and_filtered():
    events = [make_event("100", category=1, event_id=1), make_event("50", category=2, event_id=2)]
    assert build(events, categories=[1])[11] == (Decimal(100), Decimal(100))
    assert build(events, categories=[2])[11] == (Decimal(50), Decimal(50))
    assert build(events, categories=[1, 2])[11] == (Decimal(150), Decimal(150))
    assert build(events, categories=[3])[11] == (0, 0)


def test_load_resets_previous_timelines():
    repository = FakeRepository([make_event()])
    builder = DebtTimelineBuilder(repository)
    builder.load()
    repository.events = []
    builder.load()
    assert builder.build(d(1), d(15), [1])[-1].total == 0


@pytest.fixture
def debt_db(shared_dbh, tmp_path: Path):
    path = create_db(tmp_path / "db" / "db.db", DB_VERSION)
    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(path))
    assert shared_dbh.db.open()
    yield path
    shared_dbh.db.close()
    shared_dbh.db.setConnectOptions("")


def insert_event(path: Path, row_type=RowType.LIABILITY, paymenttype=PaymentType.NORMAL, due="2026-10-10") -> int:
    con = sqlite3.connect(path)
    try:
        cur = con.execute("INSERT INTO event (receiver, type, category, totalamount, createdate, duedate, paymenttype)"
                          " VALUES ('r', ?, 1101, '100.00', '2026-10-01', ?, ?)",
                          (int(row_type), due, int(paymenttype)))
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def insert_payment(path: Path, event_id: int, day: str, amount: str) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (?, ?, ?, ?)",
                    (event_id, day, amount, day))
        con.commit()
    finally:
        con.close()


def test_repository_loads_liabilities_with_payments_sorted_by_date(debt_db):
    event_id = insert_event(debt_db)
    insert_payment(debt_db, event_id, "2026-10-09", "20.00")
    insert_payment(debt_db, event_id, "2026-10-05", "30.00")
    events = DebtRepository().load()
    assert len(events) == 1
    assert events[0].amount == Decimal("100.00")
    assert events[0].due == date(2026, 10, 10)
    assert [(p.day, p.amount) for p in events[0].payments] == [(date(2026, 10, 5), Decimal("30.00")),
                                                               (date(2026, 10, 9), Decimal("20.00"))]


def test_repository_skips_refunds_and_other_row_types(debt_db):
    kept = insert_event(debt_db)
    refund = insert_event(debt_db, paymenttype=PaymentType.REFUND)
    insert_event(debt_db, row_type=RowType.HEADER)
    insert_payment(debt_db, refund, "2026-10-05", "10.00")
    assert [event.id for event in DebtRepository().load()] == [kept]


def test_repository_skips_broken_rows(debt_db):
    kept = insert_event(debt_db)
    broken = insert_event(debt_db, due="not-a-date")
    insert_payment(debt_db, broken, "2026-10-05", "10.00")
    insert_payment(debt_db, kept, "bad-date", "10.00")
    events = DebtRepository().load()
    assert [event.id for event in events] == [kept]
    assert events[0].payments == []
