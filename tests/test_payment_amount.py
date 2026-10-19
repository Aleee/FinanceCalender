from datetime import date
from decimal import Decimal

import pytest

from gui.paymentamountdialog import PaymentAmountDialog
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


def test_change_payment_amounts_changes_both(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    assert dbh.change_payment_amounts(second, Decimal("250.00"), Decimal("1050.00"))
    assert Decimal(query_all(path, "SELECT sum FROM payment WHERE id = ?", second)[0][0]) == Decimal("250.00")
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1050.00")


def test_change_payment_amounts_only_payment(event_with_payments):
    dbh, path, event_id, _, second = event_with_payments
    assert dbh.change_payment_amounts(second, Decimal("250.00"), Decimal("1000.00"))
    assert Decimal(query_all(path, "SELECT sum FROM payment WHERE id = ?", second)[0][0]) == Decimal("250.00")
    assert Decimal(query_all(path, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1000.00")


def test_change_payment_amounts_missing_payment_changes_nothing(event_with_payments):
    dbh, path, event_id, *_ = event_with_payments
    assert not dbh.change_payment_amounts(9999, Decimal("1.00"), Decimal("5.00"))
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
