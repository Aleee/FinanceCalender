import hashlib
from pathlib import Path

import pytest
from PySide6.QtCore import QDateTime, QObject, Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog

import base.edition as edition
import gui.settingsdialog as sdmod
from base.updater import UpdateInfo
from base.version import DB_VERSION
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.settingsdialog import SettingsDialog
from tests.conftest import FakeSettingsHandler
from tests.dbtools import create_db, fetch_all, read_meta
from tests.test_readpath import run_sql


class Handler(FakeSettingsHandler):

    def __init__(self, ini_path: Path, backup_folder: Path):
        super().__init__(ini_path)
        self.calls: list[str] = []
        self.applied_values: list = []
        self.backup_folder = backup_folder

    def save_settings(self) -> None:
        self.calls.append("save_settings")

    def apply_settings(self, apply_geometry: bool = False) -> None:
        self.calls.append("apply_settings")
        self.applied_values.append(self.settings.value("Columns/descr"))

    def backup_path(self) -> str:
        return self.settings.value("Backup/path", "") or str(self.backup_folder)

    def set_backup_path(self, path: str) -> None:
        self.settings.setValue("Backup/path", path)


class FakeChecker(QObject):
    check_finished = Signal()
    update_available = Signal(object)

    def __init__(self):
        super().__init__()
        self.checking = False
        self.last_check_time = QDateTime.currentDateTime()
        self.last_check_result = "ok"
        self.checks = 0

    def check(self) -> None:
        self.checks += 1


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
def checker(qapp, monkeypatch) -> FakeChecker:
    fake = FakeChecker()
    monkeypatch.setattr(qapp, "update_checker", fake, raising=False)
    monkeypatch.setattr(qapp, "app_version", "test", raising=False)
    yield fake


@pytest.fixture
def stand(tmp_path, shared_dbh, monkeypatch, qapp, checker):
    path = create_db(tmp_path / "db" / "db.db", DB_VERSION)
    run_sql(path, "INSERT INTO department (id, name) VALUES (1, 'Отдел')")
    run_sql(path, "INSERT INTO position (id, department, name) VALUES (1, 1, 'Директор')")
    run_sql(path, "INSERT INTO position (id, department, name) VALUES (2, 1, 'Бухгалтер')")
    run_sql(path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'Иванов', 1, 1, 0)")
    run_sql(path, "INSERT INTO personal (id, name, department, position, archived) VALUES (2, 'Петров', 1, 2, 0)")
    backup_folder = tmp_path / "backups"
    backup_folder.mkdir()
    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(path))
    assert shared_dbh.db.open()
    monkeypatch.setattr(sdmod, "load_calendar_exceptions", lambda dbh, year: {"holidays": [], "workbank": []})
    monkeypatch.setattr(sdmod, "save_calendar_exceptions", lambda dbh, year, data: None)
    handler = Handler(tmp_path / "ui_settings.ini", backup_folder)
    opened: list[SettingsDialog] = []

    class Stand:
        pass

    result = Stand()
    result.path, result.handler, result.dbh, result.checker = path, handler, shared_dbh, checker
    result.backup_folder = backup_folder

    def factory() -> SettingsDialog:
        dialog = SettingsDialog(handler, shared_dbh)
        opened.append(dialog)
        return dialog

    result.open = factory
    yield result
    for dialog in opened:
        dialog.close()
        dialog.deleteLater()
    qapp.processEvents()
    shared_dbh.db.close()
    shared_dbh.db.setConnectOptions("")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def personal_rows(path: Path) -> list[tuple]:
    return fetch_all(path, "SELECT id, name, department, position, archived FROM personal ORDER BY id")


def test_accept_saves_personal_then_settings_then_applies(stand, prompts):
    dialog = stand.open()
    dialog.ui.chb_dataintable_descr.setChecked(False)
    order: list[str] = []
    original = stand.dbh.save_personal_data
    stand.dbh.save_personal_data = lambda data: order.append("personal") or original(data)
    try:
        dialog.accept()
    finally:
        del stand.dbh.save_personal_data
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert order == ["personal"]
    assert stand.handler.calls == ["save_settings", "apply_settings"]
    assert stand.handler.applied_values == [0]
    assert prompts.errors == []


def test_accept_writes_csv_settings_to_database(stand, prompts):
    dialog = stand.open()
    dialog.ui.spb_csv_rowperiod.setValue(7)
    dialog.ui.le_csv_unp.setText("123456789, 987654321")
    dialog.ui.te_csv_patterns.setPlainText("шаблон")
    dialog.accept()
    meta = read_meta(stand.path)
    assert meta["CSVparser/rowperiod"] == "7"
    assert meta["CSVparser/knownunp"] == "123456789, 987654321"
    assert meta["CSVparser/patterns"] == "шаблон"


@pytest.mark.parametrize("field, value, fragment", [
    ("le_backuppath", "Z:\\нет\\такой\\папки", "Папка для резервного копирования"),
    ("le_csv_columns", "1,2", "семи столбцов"),
    ("le_csv_unp", "12345", "УНП"),
])
def test_invalid_input_blocks_saving_everything(stand, prompts, field, value, fragment):
    dialog = stand.open()
    before = file_hash(stand.path)
    dialog.ui.chb_dataintable_descr.setChecked(False)
    getattr(dialog.ui, field).setText(value)
    dialog.accept()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert len(prompts.errors) == 1 and fragment in prompts.errors[0]
    assert stand.handler.calls == ["save_settings"]
    assert stand.handler.settings.value("Columns/descr") is None
    assert file_hash(stand.path) == before


def test_position_held_by_two_active_workers_blocks_saving(stand, prompts):
    run_sql(stand.path, "UPDATE personal SET position = 1 WHERE id = 2")
    dialog = stand.open()
    dialog.accept()
    assert len(prompts.errors) == 1 and "занятая сразу несколькими" in prompts.errors[0]
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert stand.handler.calls == ["save_settings"]


def test_archived_worker_may_share_position(stand, prompts):
    run_sql(stand.path, "UPDATE personal SET position = 1, archived = 1 WHERE id = 2")
    dialog = stand.open()
    dialog.accept()
    assert prompts.errors == [] and dialog.result() == QDialog.DialogCode.Accepted


def test_failed_personal_save_stops_before_settings(stand, prompts, monkeypatch):
    dialog = stand.open()
    dialog.ui.chb_dataintable_descr.setChecked(False)
    monkeypatch.setattr(stand.dbh, "save_personal_data", lambda data: False)
    dialog.accept()
    assert len(prompts.errors) == 1 and "персонала" in prompts.errors[0]
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert stand.handler.calls == ["save_settings"]
    assert stand.handler.settings.value("Columns/descr") is None


def test_cancel_writes_nothing_but_remembers_page(stand, prompts):
    dialog = stand.open()
    before = file_hash(stand.path)
    dialog.ui.chb_dataintable_descr.setChecked(False)
    dialog.ui.lw_menu.setCurrentRow(2)
    dialog.reject()
    assert stand.handler.calls == ["save_settings"]
    assert stand.handler.settings.value("Columns/descr") is None
    assert str(stand.handler.settings.value("SettingsDialog/lastpage")) == "2"
    assert file_hash(stand.path) == before


def test_closing_disconnects_update_checker(stand, prompts):
    dialog = stand.open()
    dialog.manual_check = True
    dialog.reject()
    assert dialog.update_checker is None
    dialog.manual_check = True
    stand.checker.update_available.emit(UpdateInfo("2999.01.01", DB_VERSION, "a.zip", "x", ""))
    stand.checker.check_finished.emit()
    assert prompts.questions == []


def test_manual_update_check_asks_once_and_saves_on_yes(stand, prompts):
    dialog = stand.open()
    info = UpdateInfo("2999.01.01", DB_VERSION, "a.zip", "x", "")
    stand.checker.update_available.emit(info)
    assert prompts.questions == [] and dialog.result() != QDialog.DialogCode.Accepted
    dialog.ui.pb_checkupdates.click()
    assert stand.checker.checks == 1
    prompts.answer = YesNoMessagebox.NO_RETURN_VALUE
    stand.checker.update_available.emit(info)
    stand.checker.update_available.emit(info)
    assert len(prompts.questions) == 1 and "2999.01.01" in prompts.questions[0]
    assert dialog.result() != QDialog.DialogCode.Accepted
    dialog.ui.pb_checkupdates.click()
    prompts.answer = YesNoMessagebox.YES_RETURN_VALUE
    stand.checker.update_available.emit(info)
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert stand.handler.calls.count("apply_settings") == 1


def test_position_can_be_added_but_not_duplicated(stand, prompts, monkeypatch):
    dialog = stand.open()
    dialog.ui.cmb_positions_department.setCurrentIndex(0)
    answers = iter([("Секретарь", True), ("Директор", True)])
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: next(answers))
    dialog.add_position()
    assert [row[0] for row in fetch_all(stand.path, "SELECT name FROM position ORDER BY id")] == ["Директор", "Бухгалтер", "Секретарь"]
    dialog.add_position()
    assert len(fetch_all(stand.path, "SELECT id FROM position")) == 3
    assert any("уже есть" in text for text in prompts.errors)


def test_removing_position_clears_it_from_workers(stand, prompts):
    dialog = stand.open()
    dialog.ui.cmb_positions_department.setCurrentIndex(0)
    item = next(dialog.ui.lw_positions.item(row) for row in range(dialog.ui.lw_positions.count())
                if dialog.ui.lw_positions.item(row).text() == "Директор")
    dialog.ui.lw_positions.setCurrentItem(item)
    prompts.answer = YesNoMessagebox.NO_RETURN_VALUE
    dialog.remove_position()
    assert len(fetch_all(stand.path, "SELECT id FROM position")) == 2
    prompts.answer = YesNoMessagebox.YES_RETURN_VALUE
    dialog.remove_position()
    assert fetch_all(stand.path, "SELECT name FROM position") == [("Бухгалтер",)]
    assert personal_rows(stand.path)[0][3] is None
    assert personal_rows(stand.path)[1][3] == 2


def test_restore_backup_needs_confirmation_and_a_file(stand, prompts, monkeypatch):
    dialog = stand.open()
    monkeypatch.setattr(sdmod, "restore_backup", lambda dbh, path: pytest.fail("restore must not run"))
    prompts.answer = YesNoMessagebox.NO_RETURN_VALUE
    assert not dialog.request_restore_backup()
    prompts.answer = YesNoMessagebox.YES_RETURN_VALUE
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("", ""))
    assert not dialog.request_restore_backup()


def test_failed_restore_is_reported_and_dialog_stays_open(stand, prompts, monkeypatch):
    dialog = stand.open()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(stand.path), ""))
    monkeypatch.setattr(sdmod, "restore_backup", lambda dbh, path: False)
    assert not dialog.request_restore_backup()
    assert len(prompts.errors) == 1 and "ошибка" in prompts.errors[0]


def test_viewer_mode_saves_ui_settings_but_never_the_database(stand, prompts):
    before = file_hash(stand.path)
    edition.set_viewer(True)
    try:
        dialog = stand.open()
        assert dialog.ui.lw_menu.item(SettingsDialog.MENU_ROW_STORAGE).isHidden()
        assert dialog.ui.pb_pers_add.isHidden() and dialog.ui.pb_position_remove.isHidden()
        dialog.ui.chb_dataintable_descr.setChecked(False)
        dialog.ui.lv_personal.setCurrentIndex(dialog.ui.lv_personal.model().index(0, 0))
        dialog.ui.spb_csv_rowperiod.setValue(9)
        dialog.accept()
    finally:
        edition.set_viewer(False)
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert stand.handler.calls == ["save_settings", "apply_settings"]
    assert prompts.errors == []
    assert file_hash(stand.path) == before
    assert "CSVparser/rowperiod" not in read_meta(stand.path)


def test_viewer_mode_hides_the_unavailable_start_page(stand, prompts):
    stand.handler.settings.setValue("SettingsDialog/lastpage", SettingsDialog.MENU_ROW_STORAGE)
    edition.set_viewer(True)
    try:
        dialog = stand.open()
        assert dialog.ui.lw_menu.currentRow() != SettingsDialog.MENU_ROW_STORAGE
    finally:
        edition.set_viewer(False)
