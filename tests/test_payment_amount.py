from datetime import date, timedelta
from decimal import Decimal

import pytest

from base.liability import Col
import gui.paymentamountdialog as paymentamountdialog
from gui.paymentamountdialog import PaymentAmountDialog, delete_payment_confirmed
from tests.test_audit_fixes import query_all
from tests.test_readpath import add_event, add_payment, day, db_file, models, open_models  # noqa: F401


@pytest.fixture
def event_with_payments(db_file, open_models, shared_dbh):
    open_models(db_file)
    event_id = add_event(db_file, total="1000.00")
    first = add_payment(db_file, event_id, day(-5), "300.00")
    second = add_payment(db_file, event_id, day(0), "200.00")
    return shared_dbh, db_file, event_id, first, second


def test_read_payment_info(event_with_payments):
    dbh, _, event_id, _, second = event_with_payments
    info = dbh.read_payment_info(second)
    assert info.event_id == event_id
    assert info.payment_sum == Decimal("200.00")
    assert info.total_amount == Decimal("1000.00")
    assert info.paid_amount == Decimal("500.00")
    assert info.paid_before == Decimal("300.00")
    assert info.receiver == "ООО Ромашка"
    assert isinstance(info.payment_date, date)


def test_read_payment_info_missing_payment(event_with_payments):
    dbh, *_ = event_with_payments
    assert dbh.read_payment_info(9999) is None


def test_update_payment_changes_both(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    assert dbh.update_payment(second, date.today(), Decimal("250.00"), Decimal("1050.00"))
    assert Decimal(query_all(path, "SELECT sum FROM payment WHERE id = ?", second)[0][0]) == Decimal("250.00")
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1050.00")


def test_update_payment_only_payment(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    assert dbh.update_payment(second, date.today(), Decimal("250.00"), Decimal("1000.00"))
    assert Decimal(query_all(path, "SELECT sum FROM payment WHERE id = ?", second)[0][0]) == Decimal("250.00")
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1000.00")


def test_update_payment_changes_date_only(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    new_date = date.today() - timedelta(days=3)
    assert dbh.update_payment(second, new_date, Decimal("200.00"), Decimal("1000.00"))
    assert query_all(path, "SELECT paymentdate FROM payment WHERE id = ?", second)[0][0] == new_date.isoformat()
    assert dbh.read_payment_info(second).payment_date == new_date


def test_update_payment_missing_payment_changes_nothing(event_with_payments):
    dbh, path, event_id, *_ = event_with_payments
    assert not dbh.update_payment(9999, date.today(), Decimal("1.00"), Decimal("5.00"))
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1000.00")


def test_dialog_default_moves_total_with_payment(event_with_payments):
    dbh, _, _, _, second = event_with_payments
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(second))
    assert dialog.ui.chb_changetotal.isChecked()
    dialog.ui.dsb_payment.setValue(250)
    assert dialog.total_amount() == Decimal("1050")
    assert dialog.ui.lbl_remain.text() == "500,00"
    assert not dialog.ui.dsb_total.isEnabled()


def test_dialog_unchecked_keeps_total(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(second))
    dialog.ui.chb_changetotal.setChecked(False)
    dialog.ui.dsb_payment.setValue(250)
    assert dialog.total_amount() == Decimal("1000")
    assert dialog.ui.lbl_remain.text() == "450,00"
    assert dialog.ui.dsb_total.isEnabled()
    assert dialog.problem_text() == ""


def test_dialog_rejects_total_below_paid(event_with_payments):
    dbh, _, _, _, second = event_with_payments
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(second))
    dialog.ui.chb_changetotal.setChecked(False)
    dialog.ui.dsb_payment.setValue(800)
    assert dialog.problem_text() != ""


def test_dialog_refund_keeps_sign(db_file, open_models, shared_dbh):
    dbh = shared_dbh
    open_models(db_file)
    event_id = add_event(db_file, total="-100.00")
    payment_id = add_payment(db_file, event_id, day(0), "-100.00")
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(payment_id))
    assert dialog.ui.dsb_payment.value() == 100
    dialog.ui.dsb_payment.setValue(70)
    assert dialog.payment_sum() == Decimal("-70")
    assert dialog.total_amount() == Decimal("-70")
    assert dialog.problem_text() == ""


def test_dialog_partial_refund_keeps_payment_sign(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    refund = add_payment(path, event_id, day(0), "-100.00")
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(refund))
    assert dialog.ui.dsb_payment.value() == 100
    dialog.ui.chb_changetotal.setChecked(False)
    dialog.ui.dsb_payment.setValue(150)
    assert dialog.payment_sum() == Decimal("-150")
    assert dialog.total_amount() == Decimal("1000")
    assert dialog.problem_text() == ""


def test_dialog_rejects_refund_above_paid(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    refund = add_payment(path, event_id, day(0), "-100.00")
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(refund))
    dialog.ui.chb_changetotal.setChecked(False)
    dialog.ui.dsb_payment.setValue(600)
    assert dialog.problem_text() != ""


def test_dialog_prefilled_with_statement_amount(event_with_payments):
    dbh, _, _, _, second = event_with_payments
    dialog = PaymentAmountDialog(dbh, dbh.read_payment_info(second), Decimal("246.50"))
    assert dialog.payment_sum() == Decimal("246.5")
    assert dialog.total_amount() == Decimal("1046.5")


def test_dialog_shows_and_returns_payment_date(event_with_payments):
    dbh, _, _, _, second = event_with_payments
    info = dbh.read_payment_info(second)
    dialog = PaymentAmountDialog(dbh, info)
    assert dialog.payment_date() == info.payment_date
    new_date = info.payment_date - timedelta(days=2)
    dialog.ui.de_paymentdate.setDate(new_date)
    assert dialog.payment_date() == new_date


def test_dialog_accept_saves_new_date(event_with_payments):
    dbh, _, _, _, second = event_with_payments
    info = dbh.read_payment_info(second)
    dialog = PaymentAmountDialog(dbh, info)
    new_date = info.payment_date - timedelta(days=2)
    dialog.ui.de_paymentdate.setDate(new_date)
    dialog.accept()
    updated = dbh.read_payment_info(second)
    assert updated.payment_date == new_date
    assert updated.payment_sum == info.payment_sum
    assert updated.total_amount == info.total_amount


def test_model_refresh_event_after_payment_update(db_file, open_models, shared_dbh):
    models = open_models(db_file)
    event_id = add_event(db_file, total="1000.00")
    payment_id = add_payment(db_file, event_id, day(0), "200.00")
    models.table.reload()
    remain_before = models.table.index_by_id(event_id, Col.REMAINAMOUNT).data(models.table.qtValueRole)
    assert shared_dbh.update_payment(payment_id, date.today(), Decimal("250.00"), Decimal("1050.00"))
    models.table.refresh_event(event_id)
    index = models.table.index_by_id(event_id)
    assert index.siblingAtColumn(Col.TOTALAMOUNT).data(models.table.qtValueRole) == Decimal("1050.00")
    assert index.siblingAtColumn(Col.REMAINAMOUNT).data(models.table.qtValueRole) == remain_before == Decimal("800.00")


class FakeBox:

    answer = 0
    shown: list[str] = []

    def __init__(self, text, *args, **kwargs):
        FakeBox.shown.append(text)

    def exec(self):
        return FakeBox.answer


@pytest.fixture
def fake_boxes(monkeypatch):
    FakeBox.shown = []
    FakeBox.answer = paymentamountdialog.YesNoMessagebox.YES_RETURN_VALUE
    monkeypatch.setattr(paymentamountdialog, "YesNoMessagebox", type("Yes", (FakeBox,), {
        "YES_RETURN_VALUE": 2, "NO_RETURN_VALUE": 3}))
    monkeypatch.setattr(paymentamountdialog, "ErrorInfoMessageBox", FakeBox)
    return FakeBox


def payment_ids(path, event_id):
    return [row[0] for row in query_all(path, "SELECT id FROM payment WHERE eventid = ? ORDER BY id", event_id)]


def test_delete_payment_confirmed_removes_payment(event_with_payments, fake_boxes):
    dbh, path, event_id, first, second = event_with_payments
    assert delete_payment_confirmed(dbh, dbh.read_payment_info(second), None)
    assert payment_ids(path, event_id) == [first]
    assert fake_boxes.shown[0].startswith("Удалить оплату ")
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1000.00")


def test_delete_payment_confirmed_cancel_keeps_payment(event_with_payments, fake_boxes):
    dbh, path, event_id, first, second = event_with_payments
    fake_boxes.answer = 3
    assert not delete_payment_confirmed(dbh, dbh.read_payment_info(second), None)
    assert payment_ids(path, event_id) == [first, second]


def test_delete_payment_confirmed_refuses_when_others_exceed_total(event_with_payments, fake_boxes):
    dbh, path, event_id, first, second = event_with_payments
    extra = add_payment(path, event_id, day(0), "900.00")
    assert not delete_payment_confirmed(dbh, dbh.read_payment_info(first), None)
    assert fake_boxes.shown == ["Нельзя удалить оплату: остальные оплаты по платежу превысят его общую сумму"]
    assert payment_ids(path, event_id) == [first, second, extra]


def test_delete_payment_confirmed_refuses_when_refund_exceeds_rest(event_with_payments, fake_boxes):
    dbh, path, event_id, first, second = event_with_payments
    add_payment(path, event_id, day(0), "-450.00")
    assert not delete_payment_confirmed(dbh, dbh.read_payment_info(second), None)
    assert fake_boxes.shown == ["Нельзя удалить оплату: сумма возвратов превысит сумму остальных оплат"]
    assert second in payment_ids(path, event_id)
