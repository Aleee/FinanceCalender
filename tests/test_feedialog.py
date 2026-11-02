from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import gui.feedialog as feedialog
from base.feeparser import DailyFees
from base.liability import LiabilityCategory
from tests.dbtools import fetch_all
from tests.test_event_writing import make_payment_model
from tests.test_readpath import db_file, models, open_models  # noqa: F401


def fee_categories(total: str):
    daily = {date(2026, 10, 10): DailyFees(1, Decimal(total), [Decimal(total)])}
    return [(daily, LiabilityCategory.BANKING, ""), ({}, LiabilityCategory.COMMISSION, "")]


def confirm_fee_totals(monkeypatch, statement_total, calculated_total) -> list[str]:
    asked: list[str] = []

    class FakeYesNo:
        YES_RETURN_VALUE = 2
        NO_RETURN_VALUE = 3

        def __init__(self, text, parent=None, cancel_by_default=False):
            asked.append(text)

        def exec(self):
            return 2

    monkeypatch.setattr(feedialog, "YesNoMessagebox", FakeYesNo)
    dialog = SimpleNamespace(statement_fee_totals=statement_total)
    assert feedialog.FeeDialog._confirm_fee_totals(dialog, fee_categories(calculated_total))
    return asked


def test_fee_totals_without_difference_do_not_warn(monkeypatch):
    totals = {(date(2026, 10, 10), LiabilityCategory.BANKING): Decimal("1156.92")}
    assert confirm_fee_totals(monkeypatch, totals, "1156.92") == []


def test_fee_totals_difference_asks_for_confirmation(monkeypatch):
    totals = {(date(2026, 10, 10), LiabilityCategory.BANKING): Decimal("1157.92")}
    asked = confirm_fee_totals(monkeypatch, totals, "1156.92")
    assert len(asked) == 1 and "10.10.2026" in asked[0]


def test_standalone_fee_dialog_does_not_check_totals(monkeypatch):
    assert confirm_fee_totals(monkeypatch, None, "1156.92") == []


TODAY_DATE = date.today()


def make_fee_dialog(models, shared_dbh):
    from base.feeparser import DailyFees, FeeCategoryResult, StatementParseResult
    from gui.feedialog import FeeDialog

    def fees(*days: int) -> FeeCategoryResult:
        result = FeeCategoryResult()
        for offset in days:
            result.daily[TODAY_DATE.replace(day=1) + timedelta(days=offset)] = DailyFees(1, Decimal("5.50"), [Decimal("5.50")])
        return result

    dialog = FeeDialog(None, shared_dbh, models.table, make_payment_model(shared_dbh))
    dialog.parse_result = StatementParseResult((TODAY_DATE, TODAY_DATE), fees(0, 1), fees(2))
    return dialog


def test_fee_payments_are_created_in_one_transaction(models, shared_dbh, monkeypatch):
    import gui.feedialog as feedialogmod
    dialog = make_fee_dialog(models, shared_dbh)
    monkeypatch.setattr(feedialogmod, "show_status_message", lambda *args, **kwargs: None)
    assert dialog.make_fee_payments()
    assert fetch_all(models.path, "SELECT COUNT(*) FROM event")[0][0] == 3
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment")[0][0] == 3


def test_failed_fee_payment_rolls_back_all_created_before(models, shared_dbh, monkeypatch):
    import gui.feedialog as feedialogmod
    dialog = make_fee_dialog(models, shared_dbh)
    shown = []
    monkeypatch.setattr(feedialogmod, "show_status_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(feedialogmod, "ErrorInfoMessageBox", lambda text, *args, **kwargs: type("Box", (), {"exec": lambda self: shown.append(text)})())
    original = shared_dbh.insert_payment
    calls = []

    def failing_insert_payment(data):
        calls.append(data)
        return None if len(calls) == 3 else original(data)

    monkeypatch.setattr(shared_dbh, "insert_payment", failing_insert_payment)
    assert not dialog.make_fee_payments()
    assert len(calls) == 3
    assert fetch_all(models.path, "SELECT COUNT(*) FROM event")[0][0] == 0
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment")[0][0] == 0
    assert models.table.stored_count == 0
    assert len(shown) == 1 and "отменены" in shown[0]
