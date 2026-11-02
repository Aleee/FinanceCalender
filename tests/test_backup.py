import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QDate

import base.backup as backupmod
from base.backup import clean_service_copies, save_backup
from base.lockinfo import lock_holders
from tests.dbtools import create_db, read_meta


class FakeSettings:
    def __init__(self, folder: Path):
        self.folder = folder

    def backup_path(self) -> str:
        return str(self.folder)


def test_backup_is_consistent_copy_made_by_vacuum(dbh, work_db_path, backup_folder):
    create_db(work_db_path, dbh.DB_VERSION, {"marker": "original"})
    assert dbh.migrate_db()
    dbh.open_db_connection()
    dbh.set_setting("marker", "changed")
    saved_at = save_backup(FakeSettings(backup_folder), dbh)
    assert saved_at.isValid()
    copies = list(backup_folder.glob("backup_*.db"))
    assert len(copies) == 1
    assert read_meta(copies[0])["marker"] == "changed"
    assert not list(backup_folder.glob("*.db-journal"))


def test_backup_identical_to_previous_is_not_kept(dbh, work_db_path, backup_folder):
    create_db(work_db_path, dbh.DB_VERSION)
    assert dbh.migrate_db()
    dbh.open_db_connection()
    assert save_backup(FakeSettings(backup_folder), dbh).isValid()
    [first] = backup_folder.glob("backup_*.db")
    first.rename(backup_folder / "backup_20000101-000000.db")
    (backup_folder / "backup_pretrim_20000101.db").write_bytes(b"other")
    assert save_backup(FakeSettings(backup_folder), dbh).isValid()
    assert sorted(path.name for path in backup_folder.glob("backup_*.db")) == ["backup_20000101-000000.db",
                                                                              "backup_pretrim_20000101.db"]
    dbh.set_setting("marker", "changed")
    assert save_backup(FakeSettings(backup_folder), dbh).isValid()
    assert len(list(backup_folder.glob("backup_2*.db"))) == 2


def test_backup_to_missing_folder_is_reported(dbh, work_db_path, backup_folder):
    create_db(work_db_path, dbh.DB_VERSION)
    dbh.open_db_connection()
    assert not save_backup(FakeSettings(backup_folder / "missing"), dbh).isValid()


def test_backup_failure_is_reported(dbh, work_db_path, backup_folder, monkeypatch):
    create_db(work_db_path, dbh.DB_VERSION)
    dbh.open_db_connection()
    monkeypatch.setattr(dbh, "copy_db_file", lambda target: False)
    assert not save_backup(FakeSettings(backup_folder), dbh).isValid()


def settings_with_period(days):
    return SimpleNamespace(settings=SimpleNamespace(value=lambda key, default=None: days))


def stamp(days_ago: int) -> str:
    return QDate.currentDate().addDays(-days_ago).toString("yyyyMMdd")


def test_old_service_copies_removed_recent_and_foreign_kept(backup_folder, monkeypatch):
    monkeypatch.setattr(backupmod, "backup_dir", lambda: str(backup_folder))
    old, recent = stamp(91), stamp(10)
    names = [f"conflict_{old}-101010-000001.db", f"discarded_{old}-101010-000001.db", f"db_corrupt_{old}-101010.db",
             f"before_sync_{old}-101010-000001.db", f"before_restore_{old}-101010.db",
             f"conflict_{recent}-101010-000001.db", f"before_sync_{recent}-101010-000001.db", "before_migration_v7.db", "notes.txt", "conflict_bad.db"]
    for name in names:
        (backup_folder / name).write_bytes(b"x")
    assert clean_service_copies(settings_with_period(30))
    assert sorted(p.name for p in backup_folder.iterdir()) == sorted(names[5:])


def test_service_copies_follow_longer_user_period(backup_folder, monkeypatch):
    monkeypatch.setattr(backupmod, "backup_dir", lambda: str(backup_folder))
    kept, removed = f"before_sync_{stamp(150)}-101010-000001.db", f"conflict_{stamp(200)}-101010-000001.db"
    for name in (kept, removed):
        (backup_folder / name).write_bytes(b"x")
    assert clean_service_copies(settings_with_period(180))
    assert [p.name for p in backup_folder.iterdir()] == [kept]
    assert clean_service_copies(settings_with_period(9999))
    assert [p.name for p in backup_folder.iterdir()] == [kept]
    assert clean_service_copies(settings_with_period("неверно"))
    assert list(backup_folder.iterdir()) == []


windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Restart Manager есть только в Windows")


@windows_only
def test_lock_holders_sees_own_process(tmp_path):
    busy = tmp_path / "busy.db"
    busy.write_bytes(b"data")
    assert lock_holders(busy) == "не найдены"
    with open(busy, "rb"):
        assert f"PID {os.getpid()}, наш процесс" in lock_holders(busy)
    assert lock_holders(busy) == "не найдены"


@windows_only
def test_rename_with_retry_logs_diagnostics_for_busy_file(tmp_path, monkeypatch):
    busy = tmp_path / "db.db"
    busy.write_bytes(b"data")
    messages: list[str] = []
    monkeypatch.setattr(backupmod, "RENAME_ATTEMPTS", 3)
    monkeypatch.setattr(backupmod, "RENAME_PAUSE_SECONDS", 0)
    monkeypatch.setattr(backupmod.log, "w", messages.append)
    with open(busy, "rb"):
        with pytest.raises(PermissionError):
            backupmod.rename_with_retry(busy, tmp_path / "db_temp.db")
    diagnostics = [text for text in messages if text.startswith("Диагностика занятого файла db.db")]
    assert len(diagnostics) == 2
    assert "попытка 1 из 3" in diagnostics[0] and "попытка 3 из 3" in diagnostics[1]
    assert "db.db (4 байт)" in diagnostics[0]
    assert "наш процесс" in diagnostics[0]


def test_lock_holders_never_raises(tmp_path):
    assert isinstance(lock_holders(tmp_path / "missing.db"), str)
