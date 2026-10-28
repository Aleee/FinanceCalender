import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QDate, QEvent
from PySide6.QtWidgets import QMessageBox

import base.edition as edition
import base.paths as paths
import gui.mainwindow as mainwindowmod
from base.liability import Col, PaymentType
from base.updater import UpdateChecker
from base.version import DB_VERSION
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from tests.dbtools import create_db, fetch_all
from tests.test_readpath import add_event, add_payment, day, run_sql


@pytest.fixture
def work_db_path(tmp_path: Path) -> Path:
    return tmp_path / "data" / "db" / "db.db"


@pytest.fixture
def storage(tmp_path, work_db_path, dbh, monkeypatch) -> Path:
    create_db(work_db_path, DB_VERSION)
    run_sql(work_db_path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'Иванов', 1, NULL, 0)")
    monkeypatch.setattr(paths, "storage_dir", lambda: str(tmp_path))
    monkeypatch.setattr(UpdateChecker, "check", lambda self: None)
    monkeypatch.setattr(mainwindowmod, "DBHandler", lambda settings_handler: dbh)
    for name in ("exec", "information", "warning", "critical", "question"):
        monkeypatch.setattr(QMessageBox, name, lambda *args, _name=name, **kwargs: pytest.fail(f"unexpected QMessageBox.{_name}"))
    return work_db_path


@pytest.fixture
def errors(monkeypatch) -> list[str]:
    shown: list[str] = []
    monkeypatch.setattr(ErrorInfoMessageBox, "exec", lambda self: shown.append(self.text()) or 0)
    return shown


class Answers(list):

    def __init__(self):
        super().__init__()
        self.value = YesNoMessagebox.YES_RETURN_VALUE


@pytest.fixture
def answer(monkeypatch) -> Answers:
    asked = Answers()
    monkeypatch.setattr(YesNoMessagebox, "exec", lambda self: asked.append(self.text()) or asked.value)
    return asked


@pytest.fixture
def make_window(qapp):
    opened = []

    def factory():
        window = mainwindowmod.MainWindow()
        opened.append(window)
        qapp.processEvents()
        return window

    yield factory
    for window in opened:
        window.date_timer.stop()
        window.close()
    qapp.processEvents()
    for window in opened:
        window.deleteLater()
    qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select(window, event_id: int):
    index = window.select_event(event_id)
    assert index.isValid()
    return index


def rows_of(path: Path, sql: str) -> list[tuple]:
    return fetch_all(path, sql)


def test_window_opens_and_shows_events(storage, make_window):
    event_id = add_event(storage, receiver="ООО Альфа")
    window = make_window()
    assert window.table_model.index_by_id(event_id).isValid()
    assert window.ui.act_edit.text() != "Просмотр"


def test_window_in_viewer_mode_does_not_change_files(storage, make_window, tmp_path, errors, answer):
    event_id = add_event(storage, total="1000.00")
    first = make_window()
    first.close()
    before = file_hash(storage)
    backups_before = sorted(path.name for path in (tmp_path / "data" / "backup").glob("*"))
    edition.set_viewer(True)
    try:
        window = make_window()
        assert window.windowTitle().endswith("просмотр")
        select(window, event_id)
        window.ui.te_notes.setPlainText("заметка в режиме просмотра")
        assert not window.save_note()
        window.ui.dsb_paymentsum.setValue(100)
        assert not window.make_new_payment()
        assert not window.delete_event()
        assert not window.undo_delete_event()
        assert not window.open_event_dialog()
        assert not window.open_copydoc_dialog()
        assert errors == [] and answer == []
    finally:
        edition.set_viewer(False)
    assert file_hash(storage) == before
    assert sorted(path.name for path in (tmp_path / "data" / "backup").glob("*")) == backups_before


def test_new_payment_is_written_and_remain_is_updated(storage, make_window):
    event_id = add_event(storage, total="1000.00")
    window = make_window()
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(400)
    window.ui.de_paymentdate.setDate(QDate.currentDate())
    assert window.make_new_payment()
    payments = rows_of(storage, f"SELECT eventid, sum FROM payment WHERE eventid = {event_id}")
    assert [(row[0], Decimal(row[1])) for row in payments] == [(event_id, Decimal("400"))]
    assert window.table_model.qt_value(window.liability_store.visible_rows()[window.table_model.index_by_id(event_id).row()],
                                       Col.REMAINAMOUNT) == Decimal("600")


@pytest.mark.parametrize("amount, fragment", [(0, "отличную от нуля"), (1000.01, "превышает остаток")])
def test_invalid_payment_amount_is_refused(storage, make_window, errors, amount, fragment):
    event_id = add_event(storage, total="1000.00")
    window = make_window()
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(amount)
    assert not window.make_new_payment()
    assert len(errors) == 1 and fragment in errors[0]
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(0,)]


def test_payment_cannot_exceed_remaining_after_previous_payments(storage, make_window, errors):
    event_id = add_event(storage, total="1000.00")
    add_payment(storage, event_id, day(-1), "700.00")
    window = make_window()
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(300.01)
    assert not window.make_new_payment()
    assert "превышает остаток" in errors[0]
    window.ui.dsb_paymentsum.setValue(300)
    assert window.make_new_payment()
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(2,)]


def test_refund_cannot_exceed_paid_amount(storage, make_window, errors):
    event_id = add_event(storage, total="1000.00")
    add_payment(storage, event_id, day(-1), "300.00")
    window = make_window()
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(-300.01)
    assert not window.make_new_payment()
    assert "Сумма возврата" in errors[0]
    window.ui.dsb_paymentsum.setValue(-300)
    assert window.make_new_payment()
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(2,)]


def test_refund_event_accepts_only_negative_payments(storage, make_window, errors):
    event_id = add_event(storage, total="-500.00", paymenttype=PaymentType.REFUND, due=day(-1))
    window = make_window()
    window.ui.lw_term.setCurrentRow(0)
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(100)
    assert not window.make_new_payment()
    assert "Сумма возврата" in errors[0]
    window.ui.dsb_paymentsum.setValue(-500)
    assert window.make_new_payment()
    assert [Decimal(row[0]) for row in rows_of(storage, "SELECT sum FROM payment")] == [Decimal("-500")]


def test_payment_in_future_needs_confirmation(storage, make_window, answer):
    event_id = add_event(storage, total="1000.00")
    window = make_window()
    select(window, event_id)
    window.ui.dsb_paymentsum.setValue(100)
    window.ui.de_paymentdate.setDate(QDate.currentDate().addDays(5))
    answer.value = YesNoMessagebox.NO_RETURN_VALUE
    assert not window.make_new_payment()
    assert len(answer) == 1
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(0,)]
    answer.value = YesNoMessagebox.YES_RETURN_VALUE
    assert window.make_new_payment()
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(1,)]


def test_delete_event_removes_payments_and_undo_restores_them(storage, make_window, answer):
    event_id = add_event(storage, total="1000.00", receiver="ООО Удаляемое")
    other_id = add_event(storage, total="50.00")
    add_payment(storage, event_id, day(-2), "100.00")
    add_payment(storage, event_id, day(-1), "200.00")
    original = rows_of(storage, f"SELECT * FROM event WHERE id = {event_id}")
    window = make_window()
    select(window, event_id)
    assert window.delete_event()
    assert rows_of(storage, f"SELECT COUNT(*) FROM event WHERE id = {event_id}") == [(0,)]
    assert rows_of(storage, f"SELECT COUNT(*) FROM payment WHERE eventid = {event_id}") == [(0,)]
    assert rows_of(storage, f"SELECT COUNT(*) FROM event WHERE id = {other_id}") == [(1,)]
    assert window.undo_delete_event()
    assert rows_of(storage, f"SELECT * FROM event WHERE id = {event_id}") == original
    assert sorted(Decimal(row[0]) for row in rows_of(storage, f"SELECT sum FROM payment WHERE eventid = {event_id}")) == [Decimal(100), Decimal(200)]
    assert window.table_model.index_by_id(event_id).isValid()
    assert not window.undo_delete_event()


def test_delete_event_declined_keeps_everything(storage, make_window, answer):
    event_id = add_event(storage, total="1000.00")
    add_payment(storage, event_id, day(-1), "100.00")
    window = make_window()
    select(window, event_id)
    answer.value = YesNoMessagebox.NO_RETURN_VALUE
    assert not window.delete_event()
    assert rows_of(storage, "SELECT COUNT(*) FROM event") == [(1,)]
    assert rows_of(storage, "SELECT COUNT(*) FROM payment") == [(1,)]
    assert window.deleted_event is None


def test_delete_event_without_selection_warns(storage, make_window, errors):
    add_event(storage)
    window = make_window()
    window.ui.trw_event.selectionModel().clearCurrentIndex()
    window.ui.trw_event.selectionModel().clear()
    assert not window.delete_event()
    assert len(errors) == 1
    assert rows_of(storage, "SELECT COUNT(*) FROM event") == [(1,)]


def test_note_is_saved_when_selection_moves(storage, make_window):
    first_id = add_event(storage, receiver="Первый")
    second_id = add_event(storage, receiver="Второй")
    window = make_window()
    select(window, first_id)
    window.ui.te_notes.setPlainText("важная заметка")
    select(window, second_id)
    assert rows_of(storage, f"SELECT notes FROM event WHERE id = {first_id}") == [("важная заметка",)]
    assert rows_of(storage, f"SELECT notes FROM event WHERE id = {second_id}") == [(None,)]


def test_note_is_saved_on_close(storage, make_window):
    event_id = add_event(storage)
    window = make_window()
    select(window, event_id)
    window.ui.te_notes.setPlainText("заметка перед выходом")
    assert window.close()
    assert rows_of(storage, f"SELECT notes FROM event WHERE id = {event_id}") == [("заметка перед выходом",)]


def test_unchanged_note_is_not_written(storage, make_window):
    event_id = add_event(storage)
    window = make_window()
    select(window, event_id)
    changes_before = rows_of(storage, "SELECT COUNT(*) FROM changelog")
    assert not window.save_note()
    assert rows_of(storage, "SELECT COUNT(*) FROM changelog") == changes_before


def test_backup_is_made_on_start(storage, make_window, tmp_path):
    add_event(storage)
    make_window()
    assert list((tmp_path / "data" / "backup").glob("*"))
