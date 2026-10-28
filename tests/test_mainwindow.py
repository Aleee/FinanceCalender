import hashlib
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QDate, QEvent, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

import base.edition as edition
import base.paths as paths
import gui.mainwindow as mainwindowmod
from base.liability import Col, PaymentType
from base.updater import UpdateChecker
from base.version import DB_VERSION
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from tests.dbtools import create_db, fetch_all
from tests.test_readpath import TODAY, add_event, add_payment, day, run_sql


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


def test_calendar_is_a_second_view_next_to_the_table(storage, make_window):
    window = make_window()

    assert window.calendar_widget.parent() is window.ui.page_calendar
    assert window.ui.stw_view.currentWidget() is window.ui.page_table
    assert window.calendar_widget.store is window.table_model.store


def test_view_menu_starts_with_exclusive_table_and_calendar(storage, make_window):
    window = make_window()

    actions = window.tb_view.menu().actions()
    assert actions[:2] == [window.ui.act_view_table, window.ui.act_view_calendar]
    assert actions[2].isSeparator()
    assert window.ui.act_view_table.isChecked()

    window.ui.act_view_calendar.trigger()
    assert window.ui.act_view_calendar.isChecked()
    assert not window.ui.act_view_table.isChecked()
    assert window.ui.stw_view.currentWidget() is window.ui.page_calendar

    window.ui.act_view_table.trigger()
    assert window.ui.stw_view.currentWidget() is window.ui.page_table


def test_calendar_view_disables_term_and_period_filters(storage, make_window):
    window = make_window()
    ui = window.ui

    window.ui.act_view_calendar.trigger()
    for switch_button, filter_widget in ((ui.spb_term, ui.lw_term), (ui.spb_period, ui.wdg_period)):
        assert not filter_widget.isEnabled()
        assert switch_button.inactive
        assert "не действует" in filter_widget.toolTip()
    assert ui.lw_category.isEnabled()
    assert ui.cmb_responsiblefilter.isEnabled()

    window.ui.act_view_table.trigger()
    for switch_button, filter_widget in ((ui.spb_term, ui.lw_term), (ui.spb_period, ui.wdg_period)):
        assert filter_widget.isEnabled()
        assert not switch_button.inactive
        assert filter_widget.toolTip() == ""


def test_toggle_view_switches_between_table_and_calendar(storage, make_window):
    window = make_window()

    window.toggle_view()
    assert window.ui.stw_view.currentWidget() is window.ui.page_calendar
    assert window.ui.act_view_calendar.isChecked()
    window.toggle_view()
    assert window.ui.stw_view.currentWidget() is window.ui.page_table
    assert window.ui.act_view_table.isChecked()


def test_ctrl_t_switches_views(storage, make_window):
    window = make_window()
    window.show()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)

    QTest.keyClick(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    assert window.ui.act_view_calendar.isChecked()
    QTest.keyClick(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    assert window.ui.act_view_table.isChecked()


def test_calendar_minimum_height_is_limited_by_the_screen(storage, make_window, qapp):
    window = make_window()
    window.screen = lambda: SimpleNamespace(availableGeometry=lambda: QRect(0, 0, 1440, 700))
    window.show()
    qapp.processEvents()
    table_minimum = window.minimumHeight()

    window.ui.act_view_calendar.setChecked(True)

    assert table_minimum < window.minimumHeight() <= 700


def test_export_is_disabled_in_calendar_view(storage, make_window, qapp):
    add_event(storage, receiver="ООО Альфа")
    window = make_window()
    window.show()
    qapp.processEvents()
    assert window.ui.act_export.isEnabled()

    window.ui.act_view_calendar.setChecked(True)
    qapp.processEvents()
    assert not window.ui.act_export.isEnabled()
    assert "только в виде таблицы" in window.ui.act_export.toolTip()

    window.ui.act_view_table.setChecked(True)
    qapp.processEvents()
    assert window.ui.act_export.isEnabled()
    assert "только в виде таблицы" not in window.ui.act_export.toolTip()


def test_calendar_view_raises_the_minimum_window_height(storage, make_window, qapp):
    window = make_window()
    window.screen = lambda: SimpleNamespace(availableGeometry=lambda: QRect(0, 0, 1600, 900))
    window.resize(1400, 900)
    window.show()
    qapp.processEvents()
    table_minimum = window.minimumHeight()

    window.ui.act_view_calendar.setChecked(True)
    qapp.processEvents()
    assert window.minimumHeight() > table_minimum

    window.resize(1400, table_minimum)
    qapp.processEvents()
    calendar = window.calendar_widget
    assert window.ui.stw_view.height() >= calendar.minimumSizeHint().height()
    assert calendar.ui.tv_calendar.height() >= calendar.ui.tv_calendar.minimumHeight()

    window.ui.act_view_table.setChecked(True)
    assert window.minimumHeight() == table_minimum


def test_bottom_panel_shrinks_first_and_grows_last(storage, make_window, qapp):
    window = make_window()
    window.resize(1400, 900)
    window.show()
    qapp.processEvents()
    qapp.processEvents()
    splitter = window.ui.spl_workarea
    minimum = splitter.widget(1).minimumSizeHint().height()
    splitter.setSizes([sum(splitter.sizes()) - 330, 330])
    splitter.splitterMoved.emit(0, 1)
    top, bottom = splitter.sizes()
    assert bottom == 330 > minimum + 20

    window.resize(1400, 900 - 20)
    qapp.processEvents()
    assert splitter.sizes() == [top, bottom - 20]

    window.resize(1400, 900 - (bottom - minimum) - 50)
    qapp.processEvents()
    shrunk_top, shrunk_bottom = splitter.sizes()
    assert shrunk_bottom == minimum
    assert shrunk_top == top - 50

    window.resize(1400, 900 - (bottom - minimum) - 20)
    qapp.processEvents()
    assert splitter.sizes() == [top - 20, minimum]

    window.resize(1400, 900 - (bottom - minimum) - 10)
    qapp.processEvents()
    assert splitter.sizes() == [top - 10, minimum]

    window.resize(1400, 900 - (bottom - minimum) + 10)
    qapp.processEvents()
    assert splitter.sizes() == [top, minimum + 10]

    window.resize(1400, 900)
    qapp.processEvents()
    assert splitter.sizes() == [top, bottom]

    window.resize(1400, 900 + 40)
    qapp.processEvents()
    assert splitter.sizes() == [top + 40, bottom]


def test_switching_to_calendar_shows_the_selected_payment(storage, make_window):
    add_event(storage, receiver="ООО Альфа", due=day(0))
    far = add_event(storage, receiver="ООО Бета", due=day(40))
    window = make_window()
    window.select_event(far)

    window.ui.act_view_calendar.trigger()

    assert window.calendar_widget.current_event_id == far
    assert window.calendar_widget.selected == TODAY.addDays(40)


def test_choosing_a_payment_in_calendar_selects_it_in_the_table(storage, make_window):
    first = add_event(storage, receiver="ООО Альфа", due=day(0))
    second = add_event(storage, receiver="ООО Бета", due=day(1))
    window = make_window()
    window.ui.act_view_calendar.trigger()
    calendar = window.calendar_widget

    calendar.ui.tv_calendar.setCurrentIndex(calendar.model.index_of(TODAY.addDays(1)))

    assert window.current_data(Col.ID) == second
    calendar.ui.tv_calendar.setCurrentIndex(calendar.model.index_of(TODAY.addDays(0)))
    assert window.current_data(Col.ID) == first


def test_calendar_shows_in_the_panel_a_payment_hidden_from_the_table_by_term(storage, make_window):
    open_id = add_event(storage, receiver="ООО Альфа", total="100.00", due=day(0))
    paid_id = add_event(storage, receiver="ООО Бета", total="200.00", due=day(0))
    add_payment(storage, paid_id, day(-1), "200.00")
    window = make_window()
    assert window.table_model.index_by_id(paid_id).isValid() is False
    window.ui.act_view_calendar.trigger()
    calendar = window.calendar_widget
    events = calendar.ui.tbl_events
    rows = {events.item(row, 0).text(): row for row in range(events.rowCount())}

    events.selectRow(rows["ООО Бета"])
    assert window.current_data(Col.ID) == paid_id

    events.selectRow(rows["ООО Альфа"])
    assert window.current_data(Col.ID) == open_id

    window.ui.act_view_table.trigger()
    assert not window.table_model.index_by_id(paid_id).isValid()
    assert window.table_model.index_by_id(open_id).isValid()


def test_calendar_follows_the_search_filter(storage, make_window):
    first = add_event(storage, receiver="ООО Альфа", due=day(0))
    add_event(storage, receiver="ООО Бета", due=day(0))
    window = make_window()
    window.ui.le_search.setText("альфа")
    window.update_filters_and_select()

    window.ui.act_view_calendar.trigger()
    window.calendar_widget.reload()

    table = window.calendar_widget.ui.tbl_events
    assert [table.item(row, 0).data(Qt.ItemDataRole.UserRole) for row in range(table.rowCount())] == [first]


def test_activating_in_calendar_opens_the_payment_card(storage, make_window, monkeypatch):
    add_event(storage, receiver="ООО Альфа", due=day(0))
    window = make_window()
    window.ui.act_view_calendar.trigger()
    opened = []
    monkeypatch.setattr(window, "open_event_dialog", lambda **kwargs: opened.append(kwargs))

    window.calendar_widget.open_current_event()

    assert opened == [{"edit": True}]
