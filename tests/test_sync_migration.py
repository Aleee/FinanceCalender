import re
import shutil
import sqlite3
from pathlib import Path

import pytest

from base.backup import restore_backup
from base.migrations import DATA_TABLES
from tests.dbtools import create_db, fetch_all, read_meta, read_version


def execute(path: Path, sql: str, *params) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(sql, params)
        con.commit()
    finally:
        con.close()


def counter(path: Path) -> int:
    return int(read_meta(path)["change_counter"])


def reset_counter(path: Path) -> None:
    execute(path, "UPDATE meta SET value = '0' WHERE key = 'change_counter'")


@pytest.fixture
def v4_db(work_db_path: Path) -> Path:
    create_db(work_db_path, 4)
    con = sqlite3.connect(work_db_path)
    try:
        con.execute("INSERT INTO event (receiver, type, name, totalamount) VALUES ('ООО Ромашка', 2, 'name', '100.00')")
        con.execute("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (1, '2026-01-01', '90.00', '2026-01-01')")
        con.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", [("dup", "first"), ("dup", "second"), ("dup", "third")])
        con.commit()
    finally:
        con.close()
    return work_db_path


@pytest.fixture
def v5_db(dbh, v4_db: Path) -> Path:
    assert dbh.migrate_db()
    reset_counter(v4_db)
    return v4_db


def test_migration_to_v5_adds_sync_keys(dbh, v4_db):
    assert dbh.migrate_db()
    meta = read_meta(v4_db)
    assert read_version(v4_db) == 5
    assert re.fullmatch(r"[0-9a-f]{32}", meta["db_uuid"])
    assert re.fullmatch(r"[0-9a-f]{32}", meta["sync_token"])
    assert meta["db_uuid"] != meta["sync_token"]


def test_migration_to_v5_marks_db_as_changed(dbh, v4_db):
    assert dbh.migrate_db()
    assert counter(v4_db) == 1


def test_migration_to_v5_keeps_data(dbh, v4_db):
    event_before = fetch_all(v4_db, "SELECT * FROM event")
    payment_before = fetch_all(v4_db, "SELECT * FROM payment")
    assert dbh.migrate_db()
    assert fetch_all(v4_db, "SELECT * FROM event") == event_before
    assert fetch_all(v4_db, "SELECT * FROM payment") == payment_before


def test_migration_to_v5_collapses_meta_duplicates(dbh, v4_db):
    assert dbh.migrate_db()
    assert fetch_all(v4_db, "SELECT value FROM meta WHERE key = 'dup'") == [("first",)]
    with pytest.raises(sqlite3.IntegrityError):
        execute(v4_db, "INSERT INTO meta (key, value) VALUES ('dup', 'again')")


def test_migrated_v5_passes_integrity_check(dbh, v4_db):
    assert dbh.migrate_db()
    assert dbh.check_db_file_integrity()


def test_second_migration_changes_nothing(dbh, v4_db):
    assert dbh.migrate_db()
    meta_after_first = read_meta(v4_db)
    assert dbh.migrate_db()
    assert read_meta(v4_db) == meta_after_first


def test_every_data_table_has_three_triggers(v5_db):
    tables = {name for (name,) in fetch_all(v5_db, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    tables -= {"meta", "sqlite_sequence"}
    assert tables == set(DATA_TABLES)
    triggers = fetch_all(v5_db, "SELECT tbl_name, COUNT(*) FROM sqlite_master WHERE type = 'trigger' GROUP BY tbl_name")
    assert {table: count for table, count in triggers if table != "meta"} == dict.fromkeys(tables, 3)


@pytest.mark.parametrize("table", DATA_TABLES)
def test_data_table_writes_increase_counter(v5_db, table):
    columns = [f'"{row[1]}"' for row in fetch_all(v5_db, f'PRAGMA table_info("{table}")')]
    execute(v5_db, f'DELETE FROM "{table}"')
    reset_counter(v5_db)

    execute(v5_db, f'INSERT INTO "{table}" ({", ".join(columns)}) VALUES ({", ".join("1" for _ in columns)})')
    assert counter(v5_db) == 1
    execute(v5_db, f'UPDATE "{table}" SET {columns[0]} = 2')
    assert counter(v5_db) == 2
    execute(v5_db, f'DELETE FROM "{table}"')
    assert counter(v5_db) == 3


def test_service_keys_do_not_increase_counter(v5_db):
    execute(v5_db, "UPDATE meta SET value = 'new' WHERE key = 'sync_token'")
    execute(v5_db, "UPDATE meta SET value = 'new' WHERE key = 'db_uuid'")
    execute(v5_db, "UPDATE meta SET value = '5' WHERE key = 'db_version'")
    execute(v5_db, "DELETE FROM meta WHERE key = 'sync_token'")
    execute(v5_db, "INSERT INTO meta (key, value) VALUES ('sync_token', 'again')")
    assert counter(v5_db) == 0


def test_settings_in_meta_increase_counter_only_when_value_changes(v5_db):
    execute(v5_db, "INSERT INTO meta (key, value) VALUES ('setting', 'a')")
    assert counter(v5_db) == 1
    execute(v5_db, "UPDATE meta SET value = 'a' WHERE key = 'setting'")
    assert counter(v5_db) == 1
    execute(v5_db, "UPDATE meta SET value = 'b' WHERE key = 'setting'")
    assert counter(v5_db) == 2
    execute(v5_db, "DELETE FROM meta WHERE key = 'setting'")
    assert counter(v5_db) == 3


def test_set_setting_with_same_value_does_not_increase_counter(dbh, v5_db):
    dbh.open_db_connection()
    assert dbh.set_setting("setting", "a")
    assert dbh.set_setting("setting", "a")
    dbh.db.close()
    assert counter(v5_db) == 1


def test_restore_backup_of_current_version_marks_db_as_changed(dbh, v5_db, tmp_path):
    backup = tmp_path / "backup.db"
    shutil.copy(v5_db, backup)
    assert counter(backup) == 0
    dbh.open_db_connection()
    assert restore_backup(dbh, str(backup))
    dbh.db.close()
    assert counter(v5_db) > 0
    assert counter(backup) == 0
