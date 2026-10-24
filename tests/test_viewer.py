import importlib
import shutil

import pytest
from PySide6.QtCore import QDate, Qt
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QTreeWidget, QTreeWidgetItemIterator, QWidget

import base.edition as edition
from base.date import date_str
from base.liability import RowType
from base.sync import FolderChannel, SyncAction, SyncError, SyncReport, pull_master, push_master, synchronize
from base.version import DB_VERSION
from gui.commonwidgets.readonly import make_read_only
from gui.finplanmodel import FinPlanTableModel
from gui.syncchangesdialog import SyncChangesDialog
from gui.syncmanager import pull_tabs
from tests.dbtools import create_db, read_meta
from tests.test_readpath import add_event, add_payment, run_sql
from tests.test_sync_flow import (PARAMS, channel, connected, edit, machine_a, make_machine,  # noqa: F401
                                  patch_backup_dir)


def tree_texts(dialog) -> list[str]:
    result = []
    for tree in dialog.findChildren(QTreeWidget):
        iterator = QTreeWidgetItemIterator(tree)
        while iterator.value():
            item = iterator.value()
            result.append(" | ".join(item.text(column) for column in range(item.columnCount())))
            iterator += 1
    return result


@pytest.fixture
def viewer():
    edition.set_viewer(True)
    yield
    edition.set_viewer(False)


@pytest.fixture
def db_with_hidden(dbh, work_db_path):
    create_db(work_db_path, DB_VERSION)
    today = QDate.currentDate()
    visible = add_event(work_db_path, hidden=0, receiver="Видимый")
    hidden = add_event(work_db_path, hidden=1, receiver="Скрытый")
    unset = add_event(work_db_path, hidden=0, receiver="Без признака")
    import sqlite3
    con = sqlite3.connect(work_db_path)
    con.execute("UPDATE event SET hidden = NULL WHERE id = ?", (unset,))
    con.commit()
    con.close()
    for event_id in (visible, hidden):
        add_payment(work_db_path, event_id, date_str(today), "100.00")
    return visible, hidden, unset


def test_editor_sees_hidden_events(dbh, db_with_hidden):
    assert dbh.open_db_connection()
    assert {row[1] for row in dbh.load_events()} == set(db_with_hidden)


def test_viewer_never_loads_hidden_events(dbh, db_with_hidden, viewer):
    visible, hidden, unset = db_with_hidden
    assert dbh.open_db_connection()
    assert {row[1] for row in dbh.load_events()} == {visible, unset}
    assert dbh.load_events(event_id=hidden) == []
    assert dbh.load_events(threshold="2000-01-01") is not None
    assert "Скрытый" not in (dbh.load_column_values("receiver") or set())


def test_viewer_fulfillment_and_matching_skip_hidden(dbh, db_with_hidden, viewer):
    visible, hidden, unset = db_with_hidden
    assert dbh.open_db_connection()
    today = QDate.currentDate()
    payments = dbh.load_fulfillmentpayments_from_db(today, today)
    assert [row[3] for row in payments] == ["Видимый"]
    entries = dbh.get_paymentsum_for_period(today.toPython(), today.toPython())
    assert {entry.event_id for items in entries.values() for entry in items} == {visible}


def test_editor_fulfillment_keeps_hidden(dbh, db_with_hidden):
    assert dbh.open_db_connection()
    today = QDate.currentDate()
    assert len(dbh.load_fulfillmentpayments_from_db(today, today)) == 2


def test_viewer_connection_is_read_only(dbh, db_with_hidden, viewer):
    assert dbh.open_db_connection()
    query = QSqlQuery()
    assert not query.exec("UPDATE event SET notes = 'x'")
    assert not dbh.set_setting("marker", "x")
    assert dbh.insert_event(["r", 0, int(RowType.LIABILITY)] + [None] * 14) is None


def test_editor_connection_is_writable_after_viewer_connection(dbh, db_with_hidden):
    edition.set_viewer(True)
    assert dbh.open_db_connection()
    edition.set_viewer(False)
    assert dbh.open_db_connection()
    assert dbh.set_setting("marker", "x")


def test_viewer_refuses_to_write_master(machine_a, channel, viewer):
    with machine_a as dbh:
        with pytest.raises(SyncError):
            push_master(dbh, channel, PARAMS)
    assert channel.read_master_info() is None


def test_viewer_channel_methods_refuse_to_write(channel, tmp_path, viewer):
    source = tmp_path / "source.db"
    source.write_bytes(b"data")
    from tests.test_sync import master_info
    for action in (lambda: channel.upload_master(source, master_info()),
                   lambda: channel.write_master_info(master_info()),
                   channel.backup_master,
                   lambda: channel.remove_old_backups(30)):
        with pytest.raises(SyncError):
            action()
    assert not channel.folder.exists()


def test_viewer_ignores_local_change_counter(connected, channel):
    machine_a, machine_b = connected
    with machine_a as dbh:
        edit(dbh, "local edit")
        edition.set_viewer(True)
        try:
            assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
        finally:
            edition.set_viewer(False)
    assert channel.read_master_info().sync_token == read_meta(machine_b.file)["sync_token"]


def test_viewer_pulls_master_without_local_copy(connected, channel, backup_folder):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from editor")
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
    for copy in backup_folder.glob("before_sync_*.db"):
        copy.unlink()
    with machine_a as dbh:
        edit(dbh, "local edit ignored")
        edition.set_viewer(True)
        try:
            assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
            assert dbh.get_setting("marker") == "from editor"
            assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
        finally:
            edition.set_viewer(False)
    assert not list(backup_folder.glob("before_sync_*.db"))


def test_viewer_connects_to_foreign_master(connected, make_machine, channel):
    machine_a, _ = connected
    fresh = make_machine("viewer")
    with fresh as dbh:
        edition.set_viewer(True)
        try:
            assert synchronize(dbh, channel, PARAMS) == SyncAction.FOREIGN_DB
            pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
            assert dbh.get_setting("marker") == "a"
        finally:
            edition.set_viewer(False)


def test_finplan_model_read_only_blocks_changes(qapp):
    model = FinPlanTableModel(read_only=True)
    model.load_values({31101: [5] * 12})
    cell = model.index(model.categories.index(31101), 1)
    assert not (model.flags(cell) & Qt.ItemFlag.ItemIsEditable)
    assert not model.setData(cell, "100", Qt.ItemDataRole.EditRole)
    assert not model.clear_values([cell])
    assert model.values[31101][0] == 5


def test_finplan_model_is_editable_by_default(qapp):
    model = FinPlanTableModel()
    cell = model.index(model.categories.index(31101), 1)
    assert model.flags(cell) & Qt.ItemFlag.ItemIsEditable
    assert model.setData(cell, "100", Qt.ItemDataRole.EditRole)


def test_make_read_only_blocks_inputs_but_keeps_listed_widgets(qapp):
    root = QWidget()
    line, text, spin = QLineEdit(root), QPlainTextEdit(root), QDoubleSpinBox(root)
    check, combo, kept = QCheckBox(root), QComboBox(root), QComboBox(root)
    make_read_only(root, keep=(kept,))
    assert line.isReadOnly() and text.isReadOnly() and spin.isReadOnly()
    for widget in (check, combo, spin):
        assert widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        assert widget.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert not kept.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


def test_updater_uses_separate_channel_for_viewer(viewer):
    import base.updater as updater
    try:
        importlib.reload(updater)
        assert updater.VERSION_FILE == "version-viewer.json"
        assert updater.APP_EXE == "FinanceCalenderViewer.exe"
    finally:
        edition.set_viewer(False)
        importlib.reload(updater)
    assert updater.APP_EXE == "FinanceCalender.exe"
    assert updater.VERSION_FILE != "version-viewer.json"


def test_viewer_pull_report_hides_hidden_events(qapp, connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        hidden = add_event(dbh.local_db_path(), hidden=1, receiver="СЕКРЕТ-ПОСТАВЩИК", total="987654.32")
        add_payment(dbh.local_db_path(), hidden, date_str(QDate.currentDate()), "111.11")
        shown = add_event(dbh.local_db_path(), hidden=0, receiver="ОТКРЫТЫЙ-ПОСТАВЩИК", total="500.00")
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
    edition.set_viewer(True)
    try:
        with machine_a as dbh:
            report = SyncReport()
            assert synchronize(dbh, channel, PARAMS, report) == SyncAction.PULL
            text = "\n".join(tree_texts(SyncChangesDialog("m", pull_tabs(report))))
    finally:
        edition.set_viewer(False)
    assert "СЕКРЕТ-ПОСТАВЩИК" not in text and "987654" not in text and "111.11" not in text
    assert "ОТКРЫТЫЙ-ПОСТАВЩИК" in text


def test_viewer_personal_frequency_skips_hidden(dbh, work_db_path):
    create_db(work_db_path, DB_VERSION)
    run_sql(work_db_path, "INSERT INTO personal (id, name, department, archived, position) VALUES (7, 'Иванов', 'Отдел', 0, 1)")
    add_event(work_db_path, hidden=0, category=1101, responsible="7")
    add_event(work_db_path, hidden=1, category=1102, responsible="7")
    assert dbh.open_db_connection()
    assert set(dbh.load_personal_data()[1]) == {1101, 1102}
    dbh.db.close()
    edition.set_viewer(True)
    try:
        assert dbh.open_db_connection()
        assert set(dbh.load_personal_data()[1]) == {1101}
    finally:
        edition.set_viewer(False)
