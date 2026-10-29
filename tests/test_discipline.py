from datetime import date
from decimal import Decimal

from base.debtcalculator import DebtRepository, Event, Payment
from base.discipline import (DelayBucket, collect_stats, delay_bucket, filter_events, find_closed, find_overdue,
                             total_stats)
from tests.test_debtcalculator import debt_db, insert_event, insert_payment  # noqa: F401


def d(month: int, day: int) -> date:
    return date(2026, month, day)


def make_event(amount="100", due=d(10, 10), payments=(), category=1101, receiver="r", event_id=1) -> Event:
    return Event(event_id, category, Decimal(amount), d(10, 1), due,
                 [Payment(day, Decimal(sum_)) for day, sum_ in payments], "name", receiver)


def test_delay_bucket_borders():
    assert [delay_bucket(delay) for delay in (-5, 0, 1, 7, 8, 30, 31)] == [
        DelayBucket.IN_TIME, DelayBucket.IN_TIME, DelayBucket.WEEK, DelayBucket.WEEK,
        DelayBucket.MONTH, DelayBucket.MONTH, DelayBucket.LONG]


def test_closed_delay_is_counted_by_last_payment():
    event = make_event(payments=[(d(10, 8), "40"), (d(10, 15), "60")])
    closed = find_closed([event], d(10, 1), d(10, 31))
    assert [(item.paid_date, item.delay) for item in closed] == [(d(10, 15), 5)]


def test_partially_paid_and_unpaid_are_not_closed():
    events = [make_event(payments=[(d(10, 8), "40")], event_id=1), make_event(event_id=2)]
    assert find_closed(events, d(1, 1), d(12, 31)) == []


def test_closed_is_filtered_by_last_payment_date():
    events = [make_event(payments=[(d(9, 30), "100")], event_id=1),
              make_event(payments=[(d(10, 5), "100")], event_id=2),
              make_event(payments=[(d(11, 1), "100")], event_id=3)]
    assert [item.event.id for item in find_closed(events, d(10, 1), d(10, 31))] == [2]


def test_zero_amount_is_ignored():
    assert find_closed([make_event(amount="0", payments=[(d(10, 5), "0")])], d(1, 1), d(12, 31)) == []
    assert find_overdue([make_event(amount="0")], d(12, 1)) == []


def test_overdue_contains_unpaid_and_partially_paid_sorted_by_age():
    events = [make_event(due=d(10, 20), event_id=1),
              make_event(due=d(10, 5), payments=[(d(10, 6), "30")], event_id=2),
              make_event(due=d(10, 10), payments=[(d(10, 6), "100")], event_id=3),
              make_event(due=d(11, 20), event_id=4)]
    overdue = find_overdue(events, d(11, 1))
    assert [(item.event.id, item.remain, item.days) for item in overdue] == [
        (2, Decimal(70), 27), (1, Decimal(100), 12)]


def test_due_today_is_not_overdue():
    assert find_overdue([make_event(due=d(11, 1))], d(11, 1)) == []


def test_stats_totals():
    events = [make_event(payments=[(d(10, 5), "100")], event_id=1),
              make_event(payments=[(d(10, 10), "100")], event_id=2),
              make_event(amount="200", payments=[(d(10, 15), "200")], event_id=3),
              make_event(amount="50", payments=[(d(11, 25), "50")], event_id=4)]
    stats = total_stats(find_closed(events, d(1, 1), d(12, 31)))
    assert stats.count == 4
    assert stats.amount == Decimal(450)
    assert stats.late_count == 2
    assert stats.late_amount == Decimal(250)
    assert stats.max_delay == 46
    assert stats.average_late_delay == Decimal(46 + 5) / 2
    assert stats.in_time_share == Decimal("0.5")
    assert stats.in_time_amount_share == Decimal(200) / 450
    assert stats.late_count_share == Decimal("0.5")
    assert stats.late_amount_share == Decimal(250) / 450
    assert stats.bucket_amounts == {DelayBucket.IN_TIME: Decimal(200), DelayBucket.WEEK: Decimal(200),
                                    DelayBucket.MONTH: Decimal(0), DelayBucket.LONG: Decimal(50)}
    assert stats.buckets == {DelayBucket.IN_TIME: 2, DelayBucket.WEEK: 1, DelayBucket.MONTH: 0, DelayBucket.LONG: 1}


def test_empty_stats_do_not_divide_by_zero():
    stats = total_stats([])
    assert stats.average_late_delay == 0
    assert stats.in_time_share == 0
    assert stats.in_time_amount_share == 0
    assert stats.late_count_share == 0
    assert stats.late_amount_share == 0


def test_closed_payment_bucket():
    event = make_event(payments=[(d(10, 20), "100")])
    assert find_closed([event], d(1, 1), d(12, 31))[0].bucket == DelayBucket.MONTH


def test_collect_stats_groups_by_key():
    events = [make_event(payments=[(d(10, 5), "100")], receiver="a", event_id=1),
              make_event(payments=[(d(10, 20), "100")], receiver="a", event_id=2),
              make_event(payments=[(d(10, 20), "100")], receiver="b", event_id=3)]
    by_receiver = collect_stats(find_closed(events, d(1, 1), d(12, 31)), lambda item: item.event.receiver)
    assert {key: stats.count for key, stats in by_receiver.items()} == {"a": 2, "b": 1}
    assert by_receiver["a"].late_count == 1


def test_filter_events_by_category_and_receiver():
    events = [make_event(category=1101, receiver="ООО Ромашка", event_id=1),
              make_event(category=1101, receiver="ИП Петров", event_id=2),
              make_event(category=1103, receiver="ООО Ромашка", event_id=3)]
    assert [event.id for event in filter_events(events, set(), "")] == [1, 2, 3]
    assert [event.id for event in filter_events(events, {1101}, "")] == [1, 2]
    assert [event.id for event in filter_events(events, set(), " ромашка ")] == [1, 3]
    assert [event.id for event in filter_events(events, {1101, 1103}, "ромашка")] == [1, 3]
    assert filter_events(events, {2100}, "") == []


def test_repository_loads_name_and_receiver(debt_db):
    insert_event(debt_db)
    events = DebtRepository().load()
    assert (events[0].receiver, events[0].name) == ("r", "")
