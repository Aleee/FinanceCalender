import shutil
import sqlite3
from pathlib import Path

import gui.recoverydialog as recmod
from tests.conftest import FakeSettingsHandler
from tests.dbtools import create_db


def make_files(work_db_path: Path, tmp_path: Path) -> Path:
    work_db_path.parent.mkdir(parents=True, exist_ok=True)
    work_db_path.write_bytes(b"old database")
    new_file = tmp_path / "new.db"
    new_file.write_bytes(b"new database")
    return new_file


def test_switch_db_files_replaces_file(dbh, work_db_path, tmp_path):
    new_file = make_files(work_db_path, tmp_path)
    assert dbh.switch_db_files(str(new_file))
    assert work_db_path.read_bytes() == b"new database"
    assert not (work_db_path.parent / "db_new.db").exists()


def test_switch_db_files_keeps_old_db_when_copy_fails(dbh, work_db_path, tmp_path, monkeypatch):
    new_file = make_files(work_db_path, tmp_path)

    def broken_copy(src, dst, *args, **kwargs):
        Path(dst).write_bytes(b"trunc")
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "copy", broken_copy)
    assert not dbh.switch_db_files(str(new_file))
    assert work_db_path.read_bytes() == b"old database"
    assert not (work_db_path.parent / "db_new.db").exists()


def test_switch_db_files_keeps_old_db_when_source_missing(dbh, work_db_path, tmp_path):
    make_files(work_db_path, tmp_path)
    assert not dbh.switch_db_files(str(tmp_path / "missing.db"))
    assert work_db_path.read_bytes() == b"old database"


def test_locked_db_is_reported_as_busy_not_corrupt(dbh, work_db_path):
    create_db(work_db_path, dbh.DB_VERSION)
    holder = sqlite3.connect(work_db_path, isolation_level=None)
    holder.execute("BEGIN EXCLUSIVE")
    try:
        dbh.db.setConnectOptions("QSQLITE_BUSY_TIMEOUT=0")
        dbh.db.setDatabaseName(str(work_db_path))
        assert dbh.db.open()
        assert dbh.get_db_version() is None
        assert dbh.db_busy
    finally:
        holder.close()
        dbh.db.close()
    assert dbh.check_db_file_integrity()
    assert not dbh.db_busy


def test_recovery_keeps_copy_of_replaced_db(qapp, dbh, work_db_path, backup_folder, tmp_path, monkeypatch):
    new_file = make_files(work_db_path, tmp_path)
    monkeypatch.setattr(recmod, "db_path", lambda: str(work_db_path))
    monkeypatch.setattr(recmod, "backup_dir", lambda: str(backup_folder))
    monkeypatch.setattr(recmod.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(new_file), ""))
    monkeypatch.setattr(dbh, "make_migrated_copy", lambda path: str(new_file))
    dialog = recmod.RecoveryDialog(FakeSettingsHandler(tmp_path / "settings.ini"), dbh, cancel_available=True)
    dialog.try_recover()
    copies = list(backup_folder.glob("db_corrupt_*.db"))
    assert len(copies) == 1
    assert copies[0].read_bytes() == b"old database"
    assert work_db_path.read_bytes() == b"new database"


def test_damaged_pages_fail_integrity_check(dbh, work_db_path):
    create_db(work_db_path, dbh.DB_VERSION)
    with sqlite3.connect(work_db_path) as connection:
        connection.executemany("INSERT INTO event (receiver, name) VALUES (?, ?)",
                               [(f"receiver {i}", "x" * 200) for i in range(500)])
    connection.close()
    assert dbh.check_db_file_integrity()
    data = bytearray(work_db_path.read_bytes())
    page_size = int.from_bytes(data[16:18], "big")
    last_page = len(data) // page_size - 1
    data[last_page * page_size:last_page * page_size + 40] = bytes([255]) * 40
    work_db_path.write_bytes(bytes(data))
    assert not dbh.check_db_file_integrity()
