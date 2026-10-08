import os
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import base.backup as backupmod
import base.dbhandler as dbmod
from base.migrations import MIGRATIONS


class FakeSettingsHandler:
    def __init__(self, ini_path: Path):
        self.settings: QSettings = QSettings(str(ini_path), QSettings.Format.IniFormat)


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="session")
def shared_dbh(qapp):
    # DBHandler регистрирует в Qt подключение по умолчанию, поэтому на все тесты он один
    return dbmod.DBHandler(None)


@pytest.fixture
def work_db_path(tmp_path: Path) -> Path:
    return tmp_path / "db" / "db.db"


@pytest.fixture
def backup_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "backup"
    folder.mkdir()
    return folder


@pytest.fixture
def dbh(shared_dbh, tmp_path: Path, work_db_path: Path, backup_folder: Path, monkeypatch):
    monkeypatch.setattr(dbmod, "db_path", lambda: str(work_db_path))
    monkeypatch.setattr(dbmod, "backup_dir", lambda: str(backup_folder))
    monkeypatch.setattr(backupmod, "db_path", lambda: str(work_db_path))
    monkeypatch.setattr(dbmod, "MIGRATIONS", dict(MIGRATIONS))
    monkeypatch.setattr(shared_dbh, "DB_VERSION", dbmod.DBHandler.DB_VERSION)
    shared_dbh.settings_handler = FakeSettingsHandler(tmp_path / "settings.ini")
    yield shared_dbh
    shared_dbh.db.close()


@pytest.fixture
def migrations(dbh) -> dict:
    return dbmod.MIGRATIONS
