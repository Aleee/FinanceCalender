import hashlib
import json
import shutil
import sqlite3
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from platform import node

import pytest

import base.edition as edition
from base.liability import EVENT_COLUMN_NAMES
from base.migrations import CHANGELOG_DATA_TABLES, CHANGELOG_TABLE
from tests.dbtools import create_db, fetch_all, read_meta

LOG_SQL = "SELECT tablename, recordid, action, field, oldvalue, newvalue FROM changelog ORDER BY id"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def event_data(**values) -> list:
    data = [None] * len(EVENT_COLUMN_NAMES)
    for name, value in values.items():
        data[EVENT_COLUMN_NAMES.index(name)] = value
    return data


def log_rows(path: Path) -> list[tuple]:
    return fetch_all(path, LOG_SQL)


def execute(path: Path, sql: str, *params) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(sql, params)
        con.commit()
    finally:
        con.close()


@pytest.fixture
def current_db(dbh, work_db_path) -> Path:
    create_db(work_db_path, 4)
    assert dbh.migrate_db()
    assert dbh.open_db_connection()
    return work_db_path


@pytest.fixture
def event_id(dbh, current_db) -> int:
    new_id = dbh.insert_event(event_data(receiver="ООО Ромашка", type=2, name="Аренда", totalamount="100.00", duedate="2026-10-15"))
    assert new_id is not None
    return new_id


def test_migration_creates_table_and_triggers(current_db):
    assert fetch_all(current_db, f"SELECT COUNT(*) FROM {CHANGELOG_TABLE}") == [(0,)]
    triggers = {name for (name,) in fetch_all(current_db, "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'trg_%_log_%'")}
    assert triggers == {f"trg_{table}_log_{action}" for table in CHANGELOG_DATA_TABLES for action in ("insert", "update", "delete")}


def test_insert_is_logged_with_snapshot(current_db, event_id):
    [(table, record, action, field, old, new)] = log_rows(current_db)
    assert (table, record, action, field, old) == ("event", event_id, "insert", None, None)
    snapshot = json.loads(new)
    assert snapshot["name"] == "Аренда" and snapshot["totalamount"] == "100.00" and snapshot["id"] == event_id


def test_update_logs_only_changed_columns(dbh, current_db, event_id):
    execute(current_db, f"DELETE FROM {CHANGELOG_TABLE}")
    assert dbh.update_event(event_id, event_data(id=event_id, receiver="ООО Ромашка", type=2, name="Аренда офиса",
                                                  totalamount="120.00", duedate="2026-10-15"))
    assert log_rows(current_db) == [("event", event_id, "update", "name", "Аренда", "Аренда офиса"),
                                    ("event", event_id, "update", "totalamount", "100.00", "120.00")]


def test_unchanged_update_logs_nothing(dbh, current_db, event_id):
    execute(current_db, f"DELETE FROM {CHANGELOG_TABLE}")
    assert dbh.update_event(event_id, event_data(id=event_id, receiver="ООО Ромашка", type=2, name="Аренда",
                                                  totalamount="100.00", duedate="2026-10-15"))
    assert dbh.update_event_field(event_id, "notes", None)
    assert log_rows(current_db) == []


def test_delete_is_logged_with_old_values(dbh, current_db, event_id):
    execute(current_db, f"DELETE FROM {CHANGELOG_TABLE}")
    assert dbh.delete_event(event_id)
    [(table, record, action, field, old, new)] = log_rows(current_db)
    assert (table, record, action, field, new) == ("event", event_id, "delete", None, None)
    assert json.loads(old)["receiver"] == "ООО Ромашка"


def test_payment_changes_are_logged(dbh, current_db, event_id):
    payment_id = dbh.insert_payment([event_id, "2026-10-10", "30.00", "2026-10-10"])
    assert payment_id is not None
    execute(current_db, f"DELETE FROM {CHANGELOG_TABLE}")
    assert dbh.update_payment(payment_id, date(2026, 10, 11), Decimal("40.00"), Decimal("150.00"))
    assert log_rows(current_db) == [("payment", payment_id, "update", "paymentdate", "2026-10-10", "2026-10-11"),
                                    ("payment", payment_id, "update", "sum", "30.00", "40.00"),
                                    ("event", event_id, "update", "totalamount", "100.00", "150.00")]
    assert dbh.delete_payment(payment_id)
    assert log_rows(current_db)[-1][:3] == ("payment", payment_id, "delete")


def test_records_carry_author_and_machine(current_db, event_id):
    assert fetch_all(current_db, f"SELECT author, machine FROM {CHANGELOG_TABLE}") == [("tester", node())]


def test_author_follows_current_settings(dbh, current_db, monkeypatch):
    dbh.db.close()
    monkeypatch.setattr(dbh.settings_handler, "sync_author", lambda: "Иванов", raising=False)
    assert dbh.open_db_connection()
    assert dbh.insert_event(event_data(receiver="Р", type=2, name="Н")) is not None
    assert fetch_all(current_db, f"SELECT author FROM {CHANGELOG_TABLE}") == [("Иванов",)]


def test_session_keys_and_log_do_not_change_counter(dbh, current_db):
    meta = read_meta(current_db)
    assert meta["changelog_author"] == "tester" and meta["changelog_machine"] == node()
    assert meta["change_counter"] == "1"
    dbh.insert_event(event_data(receiver="Р", type=2, name="Н"))
    assert read_meta(current_db)["change_counter"] == "2"


def test_old_records_are_removed_on_open(dbh, current_db):
    def add_record(moment: datetime) -> None:
        execute(current_db, f"INSERT INTO {CHANGELOG_TABLE} (changed_at, tablename, recordid, action) VALUES (?, 'event', 1, 'insert')",
                moment.strftime(TIME_FORMAT))

    add_record(datetime.now() - timedelta(days=200))
    add_record(datetime.now() - timedelta(days=170))
    add_record(datetime.now())
    dbh.db.close()
    assert dbh.open_db_connection()
    assert fetch_all(current_db, f"SELECT COUNT(*) FROM {CHANGELOG_TABLE}") == [(2,)]


def test_new_column_is_logged_only_after_rebuild(dbh, current_db, event_id):
    dbh.db.close()
    execute(current_db, "ALTER TABLE event ADD COLUMN extra TEXT")
    assert dbh.open_db_connection()
    execute(current_db, f"DELETE FROM {CHANGELOG_TABLE}")
    execute(current_db, "UPDATE event SET extra = 'a' WHERE id = ?", event_id)
    assert log_rows(current_db) == []
    assert dbh.db.transaction()
    dbh.rebuild_changelog_triggers()
    assert dbh.db.commit()
    execute(current_db, "UPDATE event SET extra = 'b' WHERE id = ?", event_id)
    assert log_rows(current_db) == [("event", event_id, "update", "extra", "a", "b")]


def test_log_is_not_a_changed_table_in_diff(dbh, current_db, event_id, tmp_path):
    before = tmp_path / "before.db"
    dbh.db.close()
    shutil.copy(current_db, before)
    assert dbh.open_db_connection()
    assert dbh.update_event_field(event_id, "notes", "заметка")
    diff = dbh.read_db_diff(str(before), str(current_db))
    assert diff.other_tables == {}
    assert [new["notes"] for _, new in diff.tables["event"].changed] == ["заметка"]


def test_viewer_does_not_touch_file(dbh, current_db):
    dbh.db.close()
    execute(current_db, "DELETE FROM meta WHERE key IN ('changelog_author', 'changelog_machine')")
    before = hashlib.sha256(current_db.read_bytes()).hexdigest()
    edition.set_viewer(True)
    try:
        assert dbh.open_db_connection()
    finally:
        edition.set_viewer(False)
    dbh.db.close()
    assert hashlib.sha256(current_db.read_bytes()).hexdigest() == before
