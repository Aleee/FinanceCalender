import getpass

import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog

import gui.settings as settingsmod
import gui.syncsettingsdialog as dialogmod
from base.sync import AuthError, SyncError
from gui.settings import SettingsHandler
from gui.syncsettingsdialog import SyncSettingsDialog


@pytest.fixture
def settings_handler(qapp, tmp_path, monkeypatch) -> SettingsHandler:
    monkeypatch.setattr(settingsmod, "settings_path", lambda: str(tmp_path / "settings.ini"))
    monkeypatch.setattr(settingsmod, "from_stored_path", lambda value: value)
    monkeypatch.setattr(settingsmod, "to_stored_path", lambda value: value)
    return SettingsHandler(None)


@pytest.fixture
def messages(monkeypatch) -> list[str]:
    shown: list[str] = []

    class FakeMessageBox:
        def __init__(self, text, is_info=False, parent=None):
            shown.append(text)

        def exec(self):
            return 0

    monkeypatch.setattr(dialogmod, "ErrorInfoMessageBox", FakeMessageBox)
    return shown


def test_defaults(settings_handler):
    assert not settings_handler.sync_enabled()
    assert settings_handler.sync_folder() == ""
    assert settings_handler.sync_author() == getpass.getuser()
    assert settings_handler.sync_interval_minutes() == 5
    assert settings_handler.sync_long_backup_keep_days() == 60


def test_dialog_saves_values(settings_handler, tmp_path, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(True)
    dialog.ui.le_folder.setText(str(tmp_path))
    dialog.ui.le_author.setText("  Иванов ")
    dialog.ui.spb_interval.setValue(10)
    dialog.ui.spb_keepdays.setValue(14)
    dialog.save_and_accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert settings_handler.sync_enabled()
    assert settings_handler.sync_folder() == str(tmp_path)
    assert settings_handler.sync_author() == "Иванов"
    assert settings_handler.sync_interval_minutes() == 10
    assert settings_handler.sync_long_backup_keep_days() == 14
    assert messages == []


def test_dialog_loads_saved_values(settings_handler, tmp_path):
    settings_handler.settings.setValue("Sync/enabled", 1)
    settings_handler.settings.setValue("Sync/interval", 15)
    settings_handler.set_sync_folder(str(tmp_path))
    dialog = SyncSettingsDialog(settings_handler)
    assert dialog.ui.chb_enabled.isChecked()
    assert dialog.ui.spb_interval.value() == 15
    assert dialog.ui.le_folder.text() == str(tmp_path)


def test_dialog_rejects_missing_folder_when_enabled(settings_handler, tmp_path, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(True)
    dialog.ui.le_folder.setText(str(tmp_path / "no_such_folder"))
    dialog.save_and_accept()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert len(messages) == 1
    assert not settings_handler.sync_enabled()


def test_dialog_rejects_empty_author_when_enabled(settings_handler, tmp_path, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(True)
    dialog.ui.le_folder.setText(str(tmp_path))
    dialog.ui.le_author.setText("   ")
    dialog.save_and_accept()
    assert len(messages) == 1
    assert not settings_handler.sync_enabled()


def test_disabled_sync_does_not_require_folder(settings_handler, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(False)
    dialog.save_and_accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert messages == []


def test_channel_defaults_keep_folder_mode(settings_handler):
    assert settings_handler.sync_channel_type() == "folder"
    assert settings_handler.sync_token() == ""
    assert settings_handler.sync_disk_folder() == "app:/"
    assert settings_handler.sync_token_expires() == ""


def test_unknown_channel_type_falls_back_to_folder(settings_handler):
    settings_handler.settings.setValue("Sync/channel", "ftp")
    assert settings_handler.sync_channel_type() == "folder"


def test_dialog_shows_only_rows_of_selected_channel(settings_handler):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.cmb_channel.setCurrentIndex(dialog.ui.cmb_channel.findData("yandex"))
    assert dialog.ui.le_token.isVisibleTo(dialog) and not dialog.ui.le_folder.isVisibleTo(dialog)
    dialog.ui.cmb_channel.setCurrentIndex(dialog.ui.cmb_channel.findData("folder"))
    assert dialog.ui.le_folder.isVisibleTo(dialog) and not dialog.ui.le_token.isVisibleTo(dialog)


def test_dialog_saves_yandex_settings(settings_handler, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(True)
    dialog.ui.cmb_channel.setCurrentIndex(dialog.ui.cmb_channel.findData("yandex"))
    dialog.ui.le_token.setText("  secret ")
    dialog.ui.de_tokenexpires.setDate(QDate(2027, 5, 20))
    dialog.ui.le_diskfolder.setText("app:/sub")
    dialog.save_and_accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert settings_handler.sync_channel_type() == "yandex"
    assert settings_handler.sync_token() == "secret"
    assert settings_handler.sync_token_expires() == "2027-05-20"
    assert settings_handler.sync_disk_folder() == "app:/sub"
    assert messages == []


def test_dialog_without_token_expiry_saves_empty_value(settings_handler):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(False)
    dialog.save_and_accept()
    assert settings_handler.sync_token_expires() == ""


def test_dialog_loads_saved_token_expiry(settings_handler):
    settings_handler.settings.setValue("Sync/tokenexpires", "2027-05-20")
    dialog = SyncSettingsDialog(settings_handler)
    assert dialog.ui.de_tokenexpires.date() == QDate(2027, 5, 20)


def test_dialog_requires_token_for_yandex(settings_handler, messages):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.chb_enabled.setChecked(True)
    dialog.ui.cmb_channel.setCurrentIndex(dialog.ui.cmb_channel.findData("yandex"))
    dialog.ui.le_token.setText("  ")
    dialog.save_and_accept()
    assert len(messages) == 1
    assert not settings_handler.sync_enabled()


class FakeChannel:
    def __init__(self, error: SyncError | None):
        self.error = error

    def check_connection(self):
        if self.error:
            raise self.error


def test_check_connection_reports_success_and_failure(settings_handler, messages, monkeypatch):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.le_token.setText("secret")
    monkeypatch.setattr(dialogmod, "create_yandex_channel", lambda token, folder: FakeChannel(None))
    dialog.check_connection()
    assert messages == ["Подключение работает"]
    monkeypatch.setattr(dialogmod, "create_yandex_channel", lambda token, folder: FakeChannel(AuthError("Токен недействителен")))
    dialog.check_connection()
    assert messages[-1] == "Подключиться не удалось: Токен недействителен"


def test_check_connection_without_token_does_not_call_channel(settings_handler, messages, monkeypatch):
    dialog = SyncSettingsDialog(settings_handler)
    dialog.ui.le_token.setText("")
    monkeypatch.setattr(dialogmod, "create_yandex_channel", lambda token, folder: pytest.fail("channel must not be created"))
    dialog.check_connection()
    assert len(messages) == 1
