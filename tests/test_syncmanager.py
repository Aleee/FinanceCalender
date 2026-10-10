from datetime import date, datetime, timedelta
from pathlib import Path
from platform import node

import pytest
from PySide6.QtCore import QTimer

import gui.settings as settingsmod
from base.backup import clean_backup_folder
from base.sync import AuthError, FolderChannel, MasterInfo, MasterUpdatingError, NetworkError, SyncAction, SyncError
from base.version import APP_VERSION
from base.yandexchannel import YandexDiskApiChannel
from gui.settings import SettingsHandler
from gui.syncconflictdialog import SyncConflictDialog
from gui.syncmanager import (SYNC_ACTION_MESSAGE, SYNC_STATUS_TEXT, create_sync_channel, create_sync_params,
                             describe_master, failure_status_text, master_age_days, token_days_left)


@pytest.fixture
def settings_handler(qapp, tmp_path, monkeypatch) -> SettingsHandler:
    monkeypatch.setattr(settingsmod, "settings_path", lambda: str(tmp_path / "settings.ini"))
    monkeypatch.setattr(settingsmod, "from_stored_path", lambda value: value)
    monkeypatch.setattr(settingsmod, "to_stored_path", lambda value: value)
    return SettingsHandler(None)


def test_every_action_has_status_text():
    assert set(SYNC_STATUS_TEXT) == set(SyncAction)


def test_messages_only_for_actions_without_automatic_result():
    assert set(SYNC_ACTION_MESSAGE) == {SyncAction.CLIENT_OUTDATED}


def test_channel_uses_folder_from_settings(settings_handler, tmp_path):
    settings_handler.set_sync_folder(str(tmp_path / "exchange"))
    channel = create_sync_channel(settings_handler)
    assert isinstance(channel, FolderChannel)
    assert channel.folder == Path(tmp_path / "exchange")


def test_params_come_from_settings(settings_handler):
    settings_handler.settings.setValue("Sync/author", "Иванов")
    settings_handler.settings.setValue("Sync/backupkeepdays", 7)
    params = create_sync_params(settings_handler)
    assert (params.author, params.machine, params.app_version, params.long_backup_keep_days) == ("Иванов", node(), APP_VERSION, 7)


def test_describe_master():
    info = MasterInfo("u", "t", 5, "Иванов", "PC-1", "2026-10-09T14:05:33", "v")
    assert describe_master(info) == "09.10.2026 14:05, Иванов (PC-1)"


def test_describe_master_with_broken_time_keeps_raw_text():
    info = MasterInfo("u", "t", 5, "Иванов", "PC-1", "вчера", "v")
    assert describe_master(info) == "вчера, Иванов (PC-1)"


def test_master_age_in_days():
    old = (datetime.now() - timedelta(days=10, hours=1)).isoformat(timespec="seconds")
    assert master_age_days(MasterInfo("u", "t", 5, "a", "m", old, "v")) == 10


def test_master_age_with_broken_time_is_unknown():
    assert master_age_days(MasterInfo("u", "t", 5, "a", "m", "вчера", "v")) is None


@pytest.mark.parametrize("button_name, take, overwrite", [
    ("take_master_button", True, False),
    ("overwrite_button", False, True),
    ("cancel_button", False, False),
])
def test_conflict_dialog_reports_chosen_button(qapp, button_name, take, overwrite):
    dialog = SyncConflictDialog("09.10.2026 14:05, Иванов (PC-1)")
    QTimer.singleShot(0, getattr(dialog, button_name).click)
    dialog.exec()
    assert (dialog.take_master_chosen(), dialog.overwrite_chosen()) == (take, overwrite)


def test_failure_status_texts():
    assert failure_status_text(NetworkError("x")) == "нет связи"
    assert failure_status_text(AuthError("x")) == "токен недействителен"
    assert failure_status_text(MasterUpdatingError("x")) == "общая база обновляется"
    assert failure_status_text(SyncError("x")) == "ОШИБКА"


def test_channel_type_follows_settings(settings_handler, tmp_path):
    assert isinstance(create_sync_channel(settings_handler), FolderChannel)
    settings_handler.settings.setValue("Sync/channel", "yandex")
    settings_handler.settings.setValue("Sync/token", " abc ")
    channel = create_sync_channel(settings_handler)
    assert isinstance(channel, YandexDiskApiChannel)
    assert (channel.token, channel.folder) == ("abc", "app:/")


def test_token_days_left(settings_handler):
    assert token_days_left(settings_handler) is None
    settings_handler.settings.setValue("Sync/channel", "yandex")
    assert token_days_left(settings_handler) is None
    settings_handler.settings.setValue("Sync/tokenexpires", (date.today() + timedelta(days=12)).isoformat())
    assert token_days_left(settings_handler) == 12
    settings_handler.settings.setValue("Sync/tokenexpires", (date.today() - timedelta(days=1)).isoformat())
    assert token_days_left(settings_handler) == -1


def test_cleanup_removes_old_backups_and_keeps_conflict_migration_and_foreign_files(settings_handler, backup_folder):
    old = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d-%H%M%S")
    fresh = datetime.now().strftime("%Y%m%d-%H%M%S")
    old_names = [f"backup_{old}.db", f"before_sync_{old}-123456.db"]
    kept_names = [f"backup_{fresh}.db", f"before_sync_{fresh}-123456.db", f"conflict_{old}-123456.db",
                  "before_migration_v4.db", "notes.txt", "before_sync_notadate.db"]
    for name in old_names + kept_names:
        (backup_folder / name).write_bytes(b"x")
    settings_handler.set_backup_path(str(backup_folder))
    settings_handler.settings.setValue("Backup/cleanupperiod", 30)
    assert clean_backup_folder(settings_handler)
    assert sorted(item.name for item in backup_folder.iterdir()) == sorted(kept_names)
