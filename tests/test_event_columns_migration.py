import sqlite3
from pathlib import Path

import pytest

from tests.dbtools import create_db, fetch_all, read_version, table_columns

DROPPED_COLUMNS = ["remainamount", "todayshare", "lastpaymentdate", "filterflags"]
KEPT_COLUMNS = ["receiver", "id", "type", "contractdocument_id", "category", "subcategory", "name", "totalamount", "nds",
                "duedate", "createdate", "paymenttype", "descr", "responsible", "notes", "featured", "hidden", "receivernocase"]


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
