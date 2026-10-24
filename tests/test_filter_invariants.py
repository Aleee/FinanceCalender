from decimal import Decimal

from PySide6.QtCore import QDate

from base.liability import FilterFlags, LiabilityRow, TermCategory, calculate_filterflags, matches_term, paid_threshold

TODAY = QDate(2026, 10, 24)


def make_row(flags):
    return LiabilityRow(category=1, search_text="", responsible=0, featured=False, hidden=False,
                        remain=Decimal(0), today_share=Decimal(0), last_payment_date="", filter_flags=flags)


def test_unpaid_zero_remain_without_payments_is_visible_somewhere():
    flags = calculate_filterflags(Decimal("0"), QDate(2026, 10, 1), False, TODAY, False)
    row = make_row(flags)
    threshold = paid_threshold(TODAY, 12)
    assert any(matches_term(term, row, threshold) for term in TermCategory)


def test_refund_without_payments_is_visible_somewhere():
    flags = calculate_filterflags(Decimal("-50"), QDate(2026, 10, 1), False, TODAY, False)
    row = make_row(flags)
    threshold = paid_threshold(TODAY, 12)
    assert any(matches_term(term, row, threshold) for term in TermCategory)


def test_invalid_duedate_is_not_today_week_month():
    flags = calculate_filterflags(Decimal("100"), QDate(), False, TODAY, False)
    assert flags == FilterFlags.NOTPAID
