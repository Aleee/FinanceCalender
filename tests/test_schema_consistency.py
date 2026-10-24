import shutil
from pathlib import Path

import pytest

from base.migrations import CHANGELOG_DATA_TABLES
from base.version import DB_VERSION
from tests.dbtools import create_db, fetch_all, read_version, table_columns

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
