import shutil
import sqlite3
from pathlib import Path

import pytest

from base.migrations import CHANGELOG_DATA_TABLES
from base.version import DB_VERSION
from tests.dbtools import create_db, fetch_all, read_version, table_columns


DROPPED_COLUMNS = ["remainamount", "todayshare", "lastpaymentdate", "filterflags"]
KEPT_COLUMNS = ["receiver", "id", "type", "contractdocument_id", "category", "subcategory", "name", "totalamount", "nds",
                "duedate", "createdate", "paymenttype", "descr", "responsible", "notes", "featured", "hidden"]


@pytest.fixture
def legacy_db(work_db_path: Path) -> Path:
    create_db(work_db_path, 3, legacy_event=True)
    con = sqlite3.connect(work_db_path)
    try:
        con.executemany(
            "INSERT INTO event (receiver, type, category, name, remainamount, totalamount, duedate, todayshare, "
            "lastpaymentdate, filterflags, featured, hidden, receivernocase) VALUES (?, 2, 1101, 'name', '10.0', ?, "
            "'2026-01-01', '5.0', '2026-01-01', 2, ?, 0, ?)",
            [("ООО Ромашка", "100.00", 1, "ооо ромашка"), ("ИП Иванов", "250.50", 0, "ип иванов")])
        con.execute("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (1, '2026-01-01', '90.00', '2026-01-01')")
        con.commit()
    finally:
        con.close()
    return work_db_path


def test_computed_columns_are_dropped(dbh, legacy_db):
    assert dbh.migrate_db()
    assert read_version(legacy_db) == dbh.DB_VERSION
    assert table_columns(legacy_db, "event") == KEPT_COLUMNS


def test_remaining_data_is_preserved(dbh, legacy_db):
    columns = ", ".join(KEPT_COLUMNS)
    before = fetch_all(legacy_db, f"SELECT {columns} FROM event ORDER BY id")
    payments_before = fetch_all(legacy_db, "SELECT * FROM payment")
    assert dbh.migrate_db()
    assert fetch_all(legacy_db, f"SELECT {columns} FROM event ORDER BY id") == before
    assert fetch_all(legacy_db, "SELECT * FROM payment") == payments_before


def test_autoincrement_continues_after_migration(dbh, legacy_db):
    assert dbh.migrate_db()
    con = sqlite3.connect(legacy_db)
    try:
        con.execute("DELETE FROM event WHERE id = 2")
        new_id = con.execute("INSERT INTO event (receiver, type) VALUES ('x', 2)").lastrowid
        con.commit()
    finally:
        con.close()
    assert new_id == 3


def test_migrated_db_passes_integrity_check(dbh, legacy_db):
    assert dbh.migrate_db()
    assert dbh.check_db_file_integrity()


def test_legacy_db_is_not_accepted_without_migration(dbh, legacy_db):
    assert not dbh.check_db_file_integrity()


def test_copy_with_old_structure_is_saved_before_migration(dbh, legacy_db, backup_folder):
    assert dbh.migrate_db()
    copy_path = backup_folder / "before_migration_v3.db"
    assert read_version(copy_path) == 3
    assert set(DROPPED_COLUMNS) <= set(table_columns(copy_path, "event"))


def test_migration_is_applied_once(dbh, legacy_db):
    assert dbh.migrate_db()
    assert dbh.migrate_db()
    assert table_columns(legacy_db, "event") == KEPT_COLUMNS


def test_trailing_whitespace_is_trimmed(dbh, legacy_db):
    con = sqlite3.connect(legacy_db)
    try:
        con.execute("UPDATE event SET name = 'a' || char(10) || 'b' || char(10) || ' ', descr = 'text ' || char(13) || char(10), "
                    "notes = NULL WHERE id = 1")
        con.commit()
    finally:
        con.close()
    assert dbh.migrate_db()
    assert fetch_all(legacy_db, "SELECT name, descr, notes FROM event WHERE id = 1") == [("a\nb", "text", None)]
    assert fetch_all(legacy_db, "SELECT name, descr, notes FROM event WHERE id = 2") == [("name", None, None)]


FAKEDATA = Path(__file__).parent / "fakedata" / "db" / "db.db"


def table_names(path) -> list[str]:
    rows = fetch_all(path, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return sorted(row[0] for row in rows)


@pytest.mark.parametrize("start", [3, 7, 10])
def test_migrations_reach_current_schema(dbh, work_db_path, start):
    create_db(work_db_path, start, legacy_event=(start == 3))
    assert dbh.migrate_db()
    assert read_version(work_db_path) == DB_VERSION
    assert len(table_columns(work_db_path, "event")) == dbh.EVENT_TABLE_COLUMNUM
    assert len(table_columns(work_db_path, "payment")) == dbh.PAYMENT_TABLE_COLUMNUM
    triggers = {row[0] for row in fetch_all(work_db_path, "SELECT name FROM sqlite_master WHERE type='trigger'")}
    for table in CHANGELOG_DATA_TABLES:
        assert {f"trg_{table}_log_insert", f"trg_{table}_log_update", f"trg_{table}_log_delete"} <= triggers
    assert fetch_all(work_db_path, "PRAGMA integrity_check") == [("ok",)]
    assert fetch_all(work_db_path, "PRAGMA foreign_key_check") == []


def test_helper_schema_columns_match_migrated_fakedata(dbh, work_db_path, tmp_path):
    helper_path = create_db(tmp_path / "helper.db", DB_VERSION)
    work_db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FAKEDATA, work_db_path)
    assert dbh.migrate_db()
    helper_tables = table_names(helper_path)
    assert set(helper_tables) <= set(table_names(work_db_path))
    for table in helper_tables:
        assert table_columns(helper_path, table) == table_columns(work_db_path, table), table
    assert "changelog" in helper_tables
    log_triggers = "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_%_log_%' ORDER BY name"
    assert fetch_all(helper_path, log_triggers) == fetch_all(work_db_path, log_triggers)
