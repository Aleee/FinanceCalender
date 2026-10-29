from datetime import date
from decimal import Decimal

from base.expenses import (ExpensePayment, ExpenseRepository, build_structure, change_share, collect_stats, filter_payments,
                           in_period, month_range, monthly_average, peak_month, previous_period, rank_categories,
                           stack_months, total_stats)
from tests.test_debtcalculator import debt_db, insert_event, insert_payment  # noqa: F401


def payment(category: int, amount: str, day: date = date(2026, 10, 15), receiver: str = "r") -> ExpensePayment:
    return ExpensePayment(category, receiver, "n", day, Decimal(amount))


def test_previous_period_has_the_same_length_right_before_start():
    assert previous_period(date(2026, 10, 5), date(2026, 10, 5)) == (date(2026, 10, 4), date(2026, 10, 4))
    assert previous_period(date(2026, 1, 1), date(2026, 10, 29)) == (date(2025, 3, 5), date(2025, 12, 31))


def test_previous_period_of_full_months_is_the_same_number_of_full_months():
    assert previous_period(date(2026, 10, 1), date(2026, 10, 31)) == (date(2026, 9, 1), date(2026, 9, 30))
    assert previous_period(date(2026, 3, 1), date(2026, 3, 31)) == (date(2026, 2, 1), date(2026, 2, 28))
    assert previous_period(date(2026, 1, 1), date(2026, 1, 31)) == (date(2025, 12, 1), date(2025, 12, 31))
    assert previous_period(date(2026, 7, 1), date(2026, 9, 30)) == (date(2026, 4, 1), date(2026, 6, 30))
    assert previous_period(date(2026, 1, 1), date(2026, 12, 31)) == (date(2025, 1, 1), date(2025, 12, 31))


def test_month_range_crosses_year():
    assert len(month_range(date(2025, 11, 20), date(2026, 2, 1))) == 4


def test_refund_reduces_category_amount_and_is_counted_separately():
    stats = total_stats([payment(1101, "100.00"), payment(1101, "-30.00")])
    assert (stats.count, stats.amount, stats.refunds) == (2, Decimal("70.00"), Decimal("30.00"))


def test_filter_by_categories_receiver_and_skipped_sections():
    payments = [payment(1101, "1", receiver="ООО Ромашка"), payment(1102, "2"), payment(2100, "3"), payment(3100, "4")]
    assert len(filter_payments(payments, set(), "", set())) == 4
    assert [p.category for p in filter_payments(payments, {1102, 2100}, "", set())] == [1102, 2100]
    assert [p.category for p in filter_payments(payments, set(), "", {2, 3})] == [1101, 1102]
    assert [p.category for p in filter_payments(payments, set(), " ромашка ", set())] == [1101]


def test_in_period_includes_borders():
    payments = [payment(1101, "1", date(2026, 10, 1)), payment(1101, "1", date(2026, 10, 31)), payment(1101, "1", date(2026, 11, 1))]
    assert len(in_period(payments, date(2026, 10, 1), date(2026, 10, 31))) == 2


def test_change_share_is_none_without_previous():
    assert change_share(Decimal(10), Decimal(0)) is None
    assert change_share(Decimal(150), Decimal(100)) == Decimal("0.5")
    assert change_share(Decimal(50), Decimal(100)) == Decimal("-0.5")


def test_structure_is_sorted_by_amount_and_has_shares():
    current = collect_stats([payment(1102, "25"), payment(1101, "75")], lambda p: p.category)
    rows = build_structure(current, {})
    assert [row.categories for row in rows] == [(1101,), (1102,)]
    assert rows[0].share == Decimal("0.75")


def test_structure_keeps_category_present_only_in_previous_period():
    current = collect_stats([payment(1101, "10")], lambda p: p.category)
    previous = collect_stats([payment(1102, "5")], lambda p: p.category)
    rows = build_structure(current, previous)
    assert [(row.categories, row.amount, row.previous) for row in rows] == [((1101,), 10, 0), ((1102,), 0, 5)]


def test_small_categories_merge_into_other_only_when_there_are_two():
    payments = [payment(1101, "970"), payment(1102, "15"), payment(1103, "15")]
    current = collect_stats(payments, lambda p: p.category)
    rows = build_structure(current, {}, Decimal("0.02"))
    assert [row.categories for row in rows] == [(1101,), (1102, 1103)]
    assert rows[1].amount == Decimal(30) and rows[1].count == 2

    payments = [payment(1101, "985"), payment(1102, "15")]
    current = collect_stats(payments, lambda p: p.category)
    assert [row.categories for row in build_structure(current, {}, Decimal("0.02"))] == [(1101,), (1102,)]


def test_rank_and_stack_months_put_the_rest_to_other():
    payments = [payment(1101, "100", date(2026, 9, 1)), payment(1101, "50", date(2026, 10, 1)),
                payment(1102, "10", date(2026, 10, 1)), payment(1103, "5", date(2026, 10, 2)),
                payment(1101, "-20", date(2026, 10, 3))]
    top = rank_categories(payments, 1)
    assert top == [1101]
    stacked = stack_months(payments, top)
    assert stacked[1101] == {2026 * 12 + 9: Decimal(100), 2026 * 12 + 10: Decimal(30)}
    assert stacked[None] == {2026 * 12 + 10: Decimal(15)}


def test_repository_loads_payments_with_refunds_in_period(debt_db):
    event_id = insert_event(debt_db)
    insert_payment(debt_db, event_id, "2026-10-10", "100.00")
    insert_payment(debt_db, event_id, "2026-10-12", "-30.00")
    insert_payment(debt_db, event_id, "2026-09-30", "7.00")
    loaded = ExpenseRepository().load(date(2026, 10, 1), date(2026, 10, 31))
    assert sorted((p.day, p.amount) for p in loaded) == [(date(2026, 10, 10), Decimal("100.00")), (date(2026, 10, 12), Decimal("-30.00"))]
    assert loaded[0].category == 1101 and loaded[0].receiver == "r"
    assert {p.eventid for p in loaded} == {event_id}


def test_monthly_average_scales_period_to_month():
    assert monthly_average(Decimal("310"), date(2026, 10, 1), date(2026, 10, 31)) == Decimal("304.375")
    assert monthly_average(Decimal(0), date(2026, 10, 1), date(2026, 10, 1)) == 0


def test_peak_month_picks_the_biggest_net_month():
    payments = [payment(1101, "100", date(2026, 9, 5)), payment(1101, "70", date(2026, 10, 5)),
                payment(1102, "50", date(2026, 10, 6)), payment(1102, "-100", date(2026, 9, 7))]
    assert peak_month(payments) == (2026 * 12 + 10, Decimal("120"))
    assert peak_month([]) is None
