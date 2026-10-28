from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QDate

from base.date import date_str
from base.liability import TermCategory, LiabilityCategory, PaymentType
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventdialog import EventDialog
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.responsiblemodels import ResponsibleCategorySortModel, ResponsibleModel
from tests.conftest import FakeSettingsHandler
from tests.dbtools import fetch_all
from tests.test_readpath import add_event, add_payment, day, db_file, models, open_models, run_sql  # noqa: F401

TODAY = QDate.currentDate()


class Prompts:

    def __init__(self):
        self.errors: list[str] = []
        self.questions: list[str] = []
        self.answer = YesNoMessagebox.YES_RETURN_VALUE


@pytest.fixture
def prompts(monkeypatch) -> Prompts:
    state = Prompts()
    monkeypatch.setattr(ErrorInfoMessageBox, "exec", lambda self: state.errors.append(self.text()) or 0)
    monkeypatch.setattr(YesNoMessagebox, "exec", lambda self: state.questions.append(self.text()) or state.answer)
    return state


@pytest.fixture
def opened(models, db_file, shared_dbh, tmp_path, qapp):
    run_sql(db_file, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'Иванов', 1, NULL, 0)")
    settings = FakeSettingsHandler(tmp_path / "dialog_settings.ini")
    personal = shared_dbh.load_personal_data(as_dict=True)
    models.table.personal_dict = personal[0]
    responsible = ResponsibleModel(only_active_personal=True)
    responsible.setup_model(personal[0])
    sorted_model = ResponsibleCategorySortModel(personal[1])
    sorted_model.setSourceModel(responsible)
    payment_model = PaymentHistoryTableModel(shared_dbh)
    dialogs: list[EventDialog] = []

    def factory(**kwargs) -> EventDialog:
        dialog = EventDialog(models.table, sorted_model, payment_model, shared_dbh, settings, **kwargs)
        dialogs.append(dialog)
        return dialog

    factory.models = models
    factory.path = db_file
    yield factory
    for dialog in dialogs:
        dialog.close()
        dialog.deleteLater()
    qapp.processEvents()


def fill(dialog: EventDialog, *, receiver="ООО Тест", name="Услуги", amount=1234.56, due: QDate | None = None,
         descr="Счет №1", responsible=1, category=LiabilityCategory.CURRENT) -> None:
    dialog.ui.le_receiver.setText(receiver)
    dialog.ui.te_name.setPlainText(name)
    dialog.ui.dsb_totalamount.setValue(amount)
    dialog.ui.cmb_category.setCurrentIndex(dialog.ui.cmb_category.findData(int(category)))
    dialog.ui.de_incurrencedate.setDate(TODAY)
    dialog.ui.de_duedate.setDate(due or TODAY.addDays(10))
    dialog.ui.te_descr.setPlainText(descr)
    dialog.ui.cmb_responsible.setCurrentIndex(dialog.ui.cmb_responsible.findData(responsible))


def event_rows(path: Path) -> list[tuple]:
    return fetch_all(path, "SELECT receiver, name, totalamount, duedate, createdate, paymenttype, responsible, featured, hidden, "
                           "contractdocument_id FROM event ORDER BY id")


def payment_rows(path: Path) -> list[tuple]:
    return fetch_all(path, "SELECT eventid, paymentdate, sum FROM payment ORDER BY id")


def test_new_payment_is_written_with_entered_values(opened, prompts):
    dialog = opened()
    fill(dialog, receiver="  ООО Тест  ", name=" Услуги ", amount=1234.56)
    dialog.accept()
    assert dialog.result() == dialog.DialogCode.Accepted
    assert prompts.errors == [] and prompts.questions == []
    rows = event_rows(opened.path)
    assert len(rows) == 1
    receiver, name, total, due, created, paymenttype, responsible, featured, hidden, document = rows[0]
    assert (receiver, name, Decimal(total)) == ("ООО Тест", "Услуги", Decimal("1234.56"))
    assert due == date_str(TODAY.addDays(10)) and created == date_str(TODAY)
    assert (paymenttype, str(responsible), featured, hidden) == (int(PaymentType.NORMAL), "1", 0, 0)
    assert not document
    assert payment_rows(opened.path) == []


@pytest.mark.parametrize("change, fragment", [
    (dict(receiver="   "), "Получатель"),
    (dict(name=" "), "Наименование"),
    (dict(amount=0), "равна нулю"),
    (dict(responsible=0), "Ответственный"),
])
def test_invalid_input_is_refused_and_nothing_is_written(opened, prompts, change, fragment):
    dialog = opened()
    fill(dialog, **change)
    dialog.accept()
    assert dialog.result() != dialog.DialogCode.Accepted
    assert len(prompts.errors) == 1 and fragment in prompts.errors[0]
    assert event_rows(opened.path) == []


def test_incurrence_date_after_due_date_is_refused(opened, prompts):
    dialog = opened()
    fill(dialog, due=TODAY.addDays(5))
    dialog.ui.de_incurrencedate.setDate(TODAY.addDays(6))
    dialog.accept()
    assert len(prompts.errors) == 1 and "Дата возникновения" in prompts.errors[0]
    assert event_rows(opened.path) == []


def test_subcategory_is_required_for_finances(opened, prompts):
    dialog = opened()
    dialog.show()
    fill(dialog, category=LiabilityCategory.TOP_FINANCES)
    dialog.accept()
    assert len(prompts.errors) == 1 and "Подкатегория" in prompts.errors[0]
    dialog.ui.cmb_subcategory.setCurrentIndex(1)
    dialog.accept()
    assert len(event_rows(opened.path)) == 1


def test_soft_warnings_need_confirmation(opened, prompts):
    dialog = opened()
    fill(dialog, due=TODAY.addDays(-3), descr="")
    dialog.ui.de_incurrencedate.setDate(TODAY.addDays(-10))
    prompts.answer = YesNoMessagebox.NO_RETURN_VALUE
    dialog.accept()
    assert len(prompts.questions) == 1
    assert "Срок оплаты меньше" in prompts.questions[0] and "Основание" in prompts.questions[0]
    assert event_rows(opened.path) == [] and dialog.result() != dialog.DialogCode.Accepted
    prompts.answer = YesNoMessagebox.YES_RETURN_VALUE
    dialog.accept()
    assert len(event_rows(opened.path)) == 1


def test_far_future_due_date_needs_confirmation(opened, prompts):
    dialog = opened()
    fill(dialog, due=TODAY.addYears(3))
    prompts.answer = YesNoMessagebox.NO_RETURN_VALUE
    dialog.accept()
    assert "более чем на 2 года" in prompts.questions[0]
    assert event_rows(opened.path) == []


def test_refund_is_stored_negative_and_paid_at_once(opened, prompts):
    dialog = opened()
    fill(dialog, amount=500, due=TODAY)
    dialog.ui.rb_typerefund.setChecked(True)
    dialog.accept()
    assert prompts.errors == [] and prompts.questions == []
    rows = event_rows(opened.path)
    assert len(rows) == 1 and Decimal(rows[0][2]) == Decimal(-500) and rows[0][5] == int(PaymentType.REFUND)
    payments = payment_rows(opened.path)
    assert len(payments) == 1 and Decimal(payments[0][2]) == Decimal(-500)
    assert payments[0][0] == fetch_all(opened.path, "SELECT id FROM event")[0][0]


def test_refund_in_the_future_is_refused(opened, prompts):
    dialog = opened()
    fill(dialog, amount=500, due=TODAY.addDays(1))
    dialog.ui.rb_typerefund.setChecked(True)
    dialog.accept()
    assert len(prompts.errors) == 1 and "Дата возврата" in prompts.errors[0]
    assert event_rows(opened.path) == [] and payment_rows(opened.path) == []


def test_statement_payment_is_paid_by_operation_date(opened, prompts):
    operation = date.fromordinal(TODAY.addDays(-2).toPython().toordinal())
    dialog = opened(from_statement=True, payment_date=operation, initial_amount=Decimal("750.50"))
    assert dialog.chb_statement.isChecked() and dialog.ui.dsb_totalamount.value() == 750.5
    fill(dialog, amount=750.5)
    dialog.accept()
    payments = payment_rows(opened.path)
    assert len(payments) == 1 and Decimal(payments[0][2]) == Decimal("750.5")
    assert payments[0][1] == date_str(TODAY.addDays(-2))


def test_statement_payment_can_be_left_unpaid(opened, prompts):
    dialog = opened(from_statement=True, payment_date=date.today(), initial_amount=Decimal("100"))
    fill(dialog, amount=100)
    dialog.chb_statement.setChecked(False)
    dialog.accept()
    assert len(event_rows(opened.path)) == 1 and payment_rows(opened.path) == []


def edit_dialog(opened, event_id: int, **kwargs) -> EventDialog:
    opened.models.table.reload()
    index = opened.models.table.index_by_id(event_id)
    assert index.isValid()
    return opened(edit_mode=True, current_index=index, **kwargs)


def test_edit_keeps_id_featured_and_untouched_amount_string(opened, db_file, prompts):
    event_id = add_event(db_file, total="1000.5", due=day(5), featured=1, receiver="Старый")
    dialog = edit_dialog(opened, event_id)
    assert dialog.ui.le_receiver.text() == "Старый" and dialog.ui.dsb_totalamount.value() == 1000.5
    dialog.ui.le_receiver.setText("Новый")
    dialog.accept()
    assert prompts.errors == []
    rows = fetch_all(db_file, "SELECT id, receiver, totalamount, featured FROM event")
    assert rows == [(event_id, "Новый", "1000.5", 1)]
    assert not dialog.ui.rb_typerefund.isEnabled()


def test_edit_cannot_lower_amount_below_paid(opened, db_file, prompts):
    event_id = add_event(db_file, total="1000.00", due=day(5))
    add_payment(db_file, event_id, day(-1), "600.00")
    dialog = edit_dialog(opened, event_id)
    dialog.ui.dsb_totalamount.setValue(599.99)
    dialog.accept()
    assert len(prompts.errors) == 1 and "превышает сумму уже сделанных" in prompts.errors[0]
    assert fetch_all(db_file, "SELECT totalamount FROM event") == [("1000.00",)]
    dialog.ui.dsb_totalamount.setValue(600)
    dialog.accept()
    assert Decimal(fetch_all(db_file, "SELECT totalamount FROM event")[0][0]) == Decimal(600)


def test_edit_of_paid_payment_with_past_due_date_is_not_questioned(opened, db_file, prompts):
    event_id = add_event(db_file, total="1000.00", due=day(-20))
    add_payment(db_file, event_id, day(-19), "1000.00")
    opened.models.table.reload()
    opened.models.apply(term=TermCategory.PAID)
    dialog = edit_dialog(opened, event_id)
    dialog.ui.te_notes.setPlainText("заметка")
    dialog.accept()
    assert prompts.questions == [] and prompts.errors == []
    assert fetch_all(db_file, "SELECT notes FROM event") == [("заметка",)]


def test_edit_of_refund_locks_amount_and_type(opened, db_file, prompts):
    event_id = add_event(db_file, total="-500.00", paymenttype=PaymentType.REFUND, due=day(-1))
    dialog = edit_dialog(opened, event_id)
    assert dialog.ui.rb_typerefund.isChecked() and dialog.ui.dsb_totalamount.value() == 500
    assert not dialog.ui.dsb_totalamount.isEnabled() and not dialog.ui.rb_typenormal.isEnabled()
    dialog.ui.te_notes.setPlainText("проверено")
    dialog.accept()
    assert fetch_all(db_file, "SELECT totalamount, notes FROM event") == [("-500.00", "проверено")]


def test_copy_creates_new_unpaid_payment_and_keeps_source(opened, db_file, prompts):
    event_id = add_event(db_file, total="800.00", due=day(5), featured=1, receiver="Исходный")
    add_payment(db_file, event_id, day(-1), "300.00")
    opened.models.table.reload()
    dialog = opened(copy_mode=True, current_index=opened.models.table.index_by_id(event_id))
    assert dialog.ui.le_receiver.text() == "Исходный"
    dialog.ui.te_name.setPlainText("Копия")
    dialog.accept()
    rows = fetch_all(db_file, "SELECT id, name, featured, totalamount FROM event ORDER BY id")
    assert len(rows) == 2 and rows[0][0] == event_id and rows[1][1:3] == ("Копия", 0)
    assert Decimal(rows[1][3]) == Decimal(800)
    assert [row[0] for row in payment_rows(db_file)] == [event_id]


def test_view_mode_never_writes(opened, db_file, prompts):
    event_id = add_event(db_file, total="1000.00", due=day(5), receiver="Только чтение")
    opened.models.table.reload()
    dialog = opened(edit_mode=True, view_mode=True, current_index=opened.models.table.index_by_id(event_id))
    assert dialog.ui.pb_accept.isHidden()
    assert dialog.ui.le_receiver.isReadOnly()
    dialog.ui.le_receiver.setText("Испорчено")
    dialog.accept()
    assert dialog.result() != dialog.DialogCode.Accepted
    assert fetch_all(db_file, "SELECT receiver FROM event") == [("Только чтение",)]
    assert prompts.errors == [] and prompts.questions == []


def test_failed_save_reports_error_and_keeps_dialog_open(opened, prompts, monkeypatch):
    dialog = opened()
    fill(dialog)
    monkeypatch.setattr(opened.models.table, "insert_event", lambda data: None)
    dialog.accept()
    assert len(prompts.errors) == 1 and "Не удалось сохранить" in prompts.errors[0]
    assert dialog.result() != dialog.DialogCode.Accepted
    assert event_rows(opened.path) == []
