import shutil

import pytest
from PySide6.QtWidgets import QDialog

import base.sync as syncmod
import gui.recoverydialog as recmod
from base.sync import FolderChannel, SyncParams, push_master
from tests.dbtools import create_db


class StubSettings:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def sync_enabled(self) -> bool:
        return self.enabled


@pytest.fixture
def master_channel(dbh, work_db_path, tmp_path, backup_folder, monkeypatch):
    monkeypatch.setattr(syncmod, "backup_dir", lambda: str(backup_folder))
    work_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_db(work_db_path, 4, {"marker": "server"})
    assert dbh.migrate_db()
    channel = FolderChannel(tmp_path / "exchange")
    dbh.open_db_connection()
    push_master(dbh, channel, SyncParams("Автор", "PC", "2026.10.04"))
    dbh.db.close()
    work_db_path.unlink()
    return channel


def make_dialog(dbh, monkeypatch, channel, accepted=True, enabled=True):
    monkeypatch.setattr(recmod.SyncSettingsDialog, "__init__", lambda self, *args, **kwargs: None)
    monkeypatch.setattr(recmod.SyncSettingsDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected)
    monkeypatch.setattr(recmod, "create_sync_channel", lambda handler: channel)
    errors = []
    monkeypatch.setattr(recmod.RecoveryDialog, "_fail", lambda self, message: errors.append(message))
    dialog = recmod.RecoveryDialog(StubSettings(enabled), dbh, offer_sync=True)
    return dialog, errors


def test_fetch_from_server_restores_db(qapp, dbh, work_db_path, master_channel, monkeypatch):
    dialog, errors = make_dialog(dbh, monkeypatch, master_channel)
    dialog.try_fetch_from_server()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert not errors
    assert dbh.open_db_connection()
    assert dbh.get_setting("marker") == "server"


def test_fetch_from_server_cancelled_settings(qapp, dbh, work_db_path, master_channel, monkeypatch):
    dialog, errors = make_dialog(dbh, monkeypatch, master_channel, accepted=False)
    dialog.try_fetch_from_server()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert not work_db_path.exists()


def test_fetch_from_server_sync_disabled(qapp, dbh, work_db_path, master_channel, monkeypatch):
    dialog, errors = make_dialog(dbh, monkeypatch, master_channel, enabled=False)
    dialog.try_fetch_from_server()
    assert errors and not work_db_path.exists()


def test_fetch_from_server_without_master_shows_error(qapp, dbh, work_db_path, tmp_path, monkeypatch):
    dialog, errors = make_dialog(dbh, monkeypatch, FolderChannel(tmp_path / "empty"))
    dialog.try_fetch_from_server()
    assert errors and "нет базы" in errors[0]
    assert dialog.result() != QDialog.DialogCode.Accepted
