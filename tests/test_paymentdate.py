import pytest
from PySide6.QtCore import QDate

import base.workcalendar as wc
from base.contract import ContractDocumentData, DaysType, MonthType, PaymentDueType
from base.paymentdate import add_days, calculate_payment_date, fixed_date, next_working_day, period_for_due_month
from base.workcalendar import (is_bank_day, is_working_day, load_calendar_exceptions, save_calendar_exceptions)

# 2026-10-23 пятница, 24 суббота, 25 воскресенье, 26 понедельник, 27 вторник
FRI = QDate(2026, 10, 23)
SAT = QDate(2026, 10, 24)
SUN = QDate(2026, 10, 25)
MON = QDate(2026, 10, 26)
TUE = QDate(2026, 10, 27)


class FakeDbh:

    def __init__(self):
        self.settings: dict[str, str] = {}

    def get_setting(self, key: str, default: str | None = "") -> str | None:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: str) -> None:
        self.settings[key] = value


@pytest.fixture
def cal():
    wc.clear_calendar_cache()
    yield FakeDbh()
    wc.clear_calendar_cache()


def set_exceptions(dbh: FakeDbh, year: int = 2026, holidays=(), workbank=(), worknonbank=()) -> None:
    save_calendar_exceptions(dbh, year, {"holidays": list(holidays), "workbank": list(workbank),
                                         "worknonbank": list(worknonbank)})


def make_terms(payment_type=PaymentDueType.RELATIVE, **kwargs) -> ContractDocumentData:
    return ContractDocumentData(document_id=1, contractor_id=1, contractor_name="c", contract_id=1,
                                contract_number="1", contract_date=QDate(2026, 1, 1), document_type=0, position_id=0,
                                document_name="d", description="", payment_type=payment_type, **kwargs)


def test_weekend_is_not_working_and_not_bank_day(cal):
    assert is_working_day(cal, FRI) and is_bank_day(cal, FRI)
    assert not is_working_day(cal, SAT) and not is_bank_day(cal, SAT)
    assert not is_working_day(cal, SUN) and not is_bank_day(cal, SUN)


def test_holiday_on_weekday(cal):
    set_exceptions(cal, holidays=[MON])
    assert not is_working_day(cal, MON)
    assert not is_bank_day(cal, MON)


def test_working_saturday_with_bank_open(cal):
    set_exceptions(cal, workbank=[SAT])
    assert is_working_day(cal, SAT)
    assert is_bank_day(cal, SAT)


def test_working_saturday_with_bank_closed(cal):
    set_exceptions(cal, worknonbank=[SAT])
    assert is_working_day(cal, SAT)
    assert not is_bank_day(cal, SAT)


def test_calendar_exceptions_roundtrip_sorted_and_invalid_skipped(cal):
    cal.settings["Calendar/2026/holidays"] = "2026-10-27, bad, ,2026-10-26"
    assert load_calendar_exceptions(cal, 2026)["holidays"] == [MON, TUE]
    assert load_calendar_exceptions(cal, 2026)["workbank"] == []


def test_calendar_cache_is_dropped_on_save(cal):
    set_exceptions(cal, holidays=[MON])
    assert not is_working_day(cal, MON)
    cal.settings["Calendar/2026/holidays"] = ""
    assert not is_working_day(cal, MON)
    set_exceptions(cal)
    assert is_working_day(cal, MON)


def test_calendar_returns_copy_of_cache(cal):
    set_exceptions(cal, holidays=[MON])
    load_calendar_exceptions(cal, 2026)["holidays"].clear()
    assert load_calendar_exceptions(cal, 2026)["holidays"] == [MON]


def test_calendar_years_are_independent(cal):
    set_exceptions(cal, 2027, holidays=[QDate(2027, 1, 4)])
    assert is_working_day(cal, QDate(2026, 1, 5))
    assert not is_working_day(cal, QDate(2027, 1, 4))


def test_next_working_day(cal):
    assert next_working_day(cal, FRI) == FRI
    assert next_working_day(cal, SAT) == MON
    set_exceptions(cal, holidays=[MON])
    assert next_working_day(cal, SAT) == TUE


def test_add_days_calendar_moves_result_from_weekend(cal):
    assert add_days(cal, FRI, 1, DaysType.CALENDAR) == MON
    assert add_days(cal, FRI, 4, DaysType.CALENDAR) == TUE


def test_add_days_zero_moves_start_from_weekend(cal):
    assert add_days(cal, SAT, 0, DaysType.CALENDAR) == MON
    assert add_days(cal, SAT, 0, DaysType.WORKING) == MON
    assert add_days(cal, SAT, 0, DaysType.BANKING) == MON
    assert add_days(cal, FRI, 0, DaysType.WORKING) == FRI


def test_add_days_working_skips_weekend_and_holiday(cal):
    assert add_days(cal, FRI, 1, DaysType.WORKING) == MON
    assert add_days(cal, FRI, 2, DaysType.WORKING) == TUE
    set_exceptions(cal, holidays=[MON])
    assert add_days(cal, FRI, 1, DaysType.WORKING) == TUE


def test_add_days_working_vs_banking_on_nonbank_saturday(cal):
    set_exceptions(cal, worknonbank=[SAT])
    assert add_days(cal, FRI, 1, DaysType.WORKING) == SAT
    assert add_days(cal, FRI, 1, DaysType.BANKING) == MON


def test_add_days_working_saturday_with_open_bank(cal):
    set_exceptions(cal, workbank=[SAT])
    assert add_days(cal, FRI, 1, DaysType.WORKING) == SAT
    assert add_days(cal, FRI, 1, DaysType.BANKING) == SAT


def test_add_days_negative_is_plain_calendar_shift(cal):
    assert add_days(cal, MON, -1, DaysType.WORKING) == SUN
    assert add_days(cal, MON, -3, DaysType.BANKING) == FRI


def test_fixed_date_clamps_day_to_month_length():
    assert fixed_date(2026, 2, 31, MonthType.CURRENT) == QDate(2026, 2, 28)
    assert fixed_date(2024, 2, 31, MonthType.CURRENT) == QDate(2024, 2, 29)
    assert fixed_date(2024, 1, 31, MonthType.NEXT) == QDate(2024, 2, 29)


def test_fixed_date_month_shift_across_year():
    assert fixed_date(2026, 12, 10, MonthType.NEXT) == QDate(2027, 1, 10)
    assert fixed_date(2026, 1, 10, MonthType.PREVIOUS) == QDate(2025, 12, 10)
    assert fixed_date(2026, 5, 10, MonthType.CURRENT) == QDate(2026, 5, 10)


def test_fixed_date_day_below_one_becomes_first():
    assert fixed_date(2026, 5, 0, MonthType.CURRENT) == QDate(2026, 5, 1)


def test_fixed_date_requires_day_and_month_type():
    with pytest.raises(ValueError):
        fixed_date(2026, 5, None, MonthType.CURRENT)
    with pytest.raises(ValueError):
        fixed_date(2026, 5, 10, None)


def test_period_for_due_month():
    due = QDate(2026, 11, 1)
    assert period_for_due_month(make_terms(month_type=MonthType.NEXT), due) == QDate(2026, 10, 1)
    assert period_for_due_month(make_terms(month_type=MonthType.PREVIOUS), due) == QDate(2026, 12, 1)
    assert period_for_due_month(make_terms(month_type=MonthType.CURRENT), due) == due
    assert period_for_due_month(make_terms(month_type=None), due) == due


def test_calculate_fixed_moves_from_weekend(cal):
    terms = make_terms(PaymentDueType.FIXED, month_day=24, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 1, 1), 2026, 10) == MON


def test_calculate_fixed_skips_holiday(cal):
    set_exceptions(cal, holidays=[MON])
    terms = make_terms(PaymentDueType.FIXED, month_day=26, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 1, 1), 2026, 10) == TUE


def test_calculate_relative_calendar_days(cal):
    terms = make_terms(days_count=10, days_type=DaysType.CALENDAR)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == QDate(2026, 10, 12)


def test_calculate_relative_working_days(cal):
    terms = make_terms(days_count=5, days_type=DaysType.WORKING)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == QDate(2026, 10, 8)


def test_calculate_relative_calendar_condition_limits_result(cal):
    terms = make_terms(days_count=30, days_type=DaysType.CALENDAR, has_calendar_condition=True,
                       month_day=15, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == QDate(2026, 10, 15)


def test_calculate_relative_calendar_condition_not_reached(cal):
    terms = make_terms(days_count=5, days_type=DaysType.CALENDAR, has_calendar_condition=True,
                       month_day=15, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == QDate(2026, 10, 6)


def test_calculate_relative_limit_on_weekend_moves_forward(cal):
    terms = make_terms(days_count=30, days_type=DaysType.CALENDAR, has_calendar_condition=True,
                       month_day=24, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == MON


def test_calculate_relative_condition_ignored_when_flag_off(cal):
    terms = make_terms(days_count=30, days_type=DaysType.CALENDAR, has_calendar_condition=False,
                       month_day=15, month_type=MonthType.CURRENT)
    assert calculate_payment_date(cal, terms, QDate(2026, 10, 1), 2026, 10) == QDate(2026, 11, 2)


def test_calculate_without_term_returns_none(cal):
    assert calculate_payment_date(cal, make_terms(PaymentDueType.PREPAYMENT), FRI, 2026, 10) is None
    assert calculate_payment_date(cal, make_terms(days_count=5, days_type=None), FRI, 2026, 10) is None
