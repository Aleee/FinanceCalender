import shutil
from pathlib import Path

import pytest

from base.backup import restore_backup
from tests.dbtools import create_db, read_meta, read_version, table_columns

CLIENT_VERSION = 3


@pytest.fixture(autouse=True)
def fake_migrations(dbh, migrations) -> None:
    migrations.clear()
    migrations[2] = ["INSERT INTO meta (key, value) VALUES ('key2', 'x')"]
    migrations[3] = ["INSERT INTO meta (key, value) VALUES ('key3', 'y')"]
    dbh.DB_VERSION = CLIENT_VERSION


@pytest.fixture
def old_db(work_db_path: Path) -> Path:
    return create_db(work_db_path, 1)


@pytest.fixture
def current_db(work_db_path: Path) -> Path:
    return create_db(work_db_path, CLIENT_VERSION)


def test_migrate_applies_chain_to_current_version(dbh, old_db):
    assert dbh.migrate_db()
    assert read_version(old_db) == CLIENT_VERSION
    assert read_meta(old_db)["key2"] == "x"
    assert read_meta(old_db)["key3"] == "y"


def test_migrate_applies_schema_changes(dbh, old_db, migrations):
    migrations[2] = ["ALTER TABLE event ADD COLUMN col2 TEXT"]
    migrations[3] = ["ALTER TABLE event ADD COLUMN col3 TEXT"]
    assert dbh.migrate_db()
    assert {"col2", "col3"} <= set(table_columns(old_db, "event"))


def test_migrate_calls_function_step(dbh, old_db, migrations):
    migrations[2] = [lambda handler: handler.set_setting("from_function", "1")]
    assert dbh.migrate_db()
    assert read_meta(old_db)["from_function"] == "1"


def test_migrated_db_passes_integrity_check(dbh, old_db):
    assert dbh.migrate_db()
    assert dbh.check_db_file_integrity()


def test_migrate_saves_copy_before_migration(dbh, old_db, backup_folder):
    assert dbh.migrate_db()
    copy_path = backup_folder / "before_migration_v1.db"
    assert copy_path.is_file()
    assert read_version(copy_path) == 1


def test_migrate_current_version_changes_nothing(dbh, current_db, backup_folder):
    meta_before = read_meta(current_db)
    assert dbh.migrate_db()
    assert read_meta(current_db) == meta_before
    assert not any(backup_folder.iterdir())


def test_migrate_twice_changes_nothing(dbh, old_db):
    assert dbh.migrate_db()
    meta_after_first = read_meta(old_db)
    assert dbh.migrate_db()
    assert read_meta(old_db) == meta_after_first


def test_migrate_sql_error_rolls_back_everything(dbh, work_db_path, migrations):
    db = create_db(work_db_path, 2)
    migrations[3] = ["ALTER TABLE event ADD COLUMN col3 TEXT",
                     "INSERT INTO meta (key, value) VALUES ('key3', 'y')",
                     "INSERT INTO no_such_table VALUES (1)"]
    assert not dbh.migrate_db()
    assert read_version(db) == 2
    assert "col3" not in table_columns(db, "event")
    assert "key3" not in read_meta(db)


def test_migrate_function_error_rolls_back_everything(dbh, work_db_path, migrations):
    def broken(handler):
        handler.set_setting("half_done", "1")
        raise RuntimeError("boom")

    db = create_db(work_db_path, 2)
    migrations[3] = ["ALTER TABLE event ADD COLUMN col3 TEXT", broken]
    assert not dbh.migrate_db()
    assert read_version(db) == 2
    assert "col3" not in table_columns(db, "event")
    assert "half_done" not in read_meta(db)


def test_migrate_fails_when_step_is_not_described(dbh, work_db_path, migrations):
    db = create_db(work_db_path, 2)
    del migrations[3]
    assert not dbh.migrate_db()
    assert read_version(db) == 2


def test_migrate_refuses_db_newer_than_client(dbh, work_db_path, backup_folder):
    db = create_db(work_db_path, CLIENT_VERSION + 1)
    assert not dbh.migrate_db()
    assert read_version(db) == CLIENT_VERSION + 1
    assert not any(backup_folder.iterdir())


def test_migrate_garbage_file_returns_false(dbh, work_db_path):
    work_db_path.parent.mkdir(parents=True)
    work_db_path.write_bytes(b"this is not a sqlite database" * 100)
    assert not dbh.migrate_db()


def test_make_migrated_copy_migrates_only_the_copy(dbh, current_db, tmp_path):
    old_backup = create_db(tmp_path / "old_backup.db", 1)
    old_backup_bytes = old_backup.read_bytes()
    result = dbh.make_migrated_copy(str(old_backup))
    assert result is not None
    assert read_version(Path(result)) == CLIENT_VERSION
    assert old_backup.read_bytes() == old_backup_bytes
    assert read_version(current_db) == CLIENT_VERSION


def test_make_migrated_copy_rejects_newer_file(dbh, current_db, tmp_path):
    newer = create_db(tmp_path / "newer.db", CLIENT_VERSION + 1)
    assert dbh.make_migrated_copy(str(newer)) is None
    assert not (current_db.parent / "db_restore_temp.db").exists()


def test_make_migrated_copy_rejects_garbage(dbh, current_db, tmp_path):
    garbage = tmp_path / "garbage.db"
    garbage.write_bytes(b"this is not a sqlite database" * 100)
    assert dbh.make_migrated_copy(str(garbage)) is None
    assert not (current_db.parent / "db_restore_temp.db").exists()


def test_restore_backup_from_old_version(dbh, work_db_path, tmp_path):
    create_db(work_db_path, CLIENT_VERSION, {"marker": "current session"})
    dbh.open_db_connection()
    old_backup = create_db(tmp_path / "old_backup.db", 1, {"marker": "from backup"})
    old_backup_bytes = old_backup.read_bytes()
    assert restore_backup(dbh, str(old_backup))
    assert dbh.is_db_connected()
    dbh.db.close()
    assert read_version(work_db_path) == CLIENT_VERSION
    assert read_meta(work_db_path)["marker"] == "from backup"
    assert read_meta(work_db_path)["key3"] == "y"
    assert old_backup.read_bytes() == old_backup_bytes
    assert not (work_db_path.parent / "db_restore_temp.db").exists()


def test_restore_backup_failure_keeps_working_db(dbh, work_db_path, tmp_path):
    create_db(work_db_path, CLIENT_VERSION, {"marker": "current session"})
    dbh.open_db_connection()
    garbage = tmp_path / "garbage.db"
    garbage.write_bytes(b"this is not a sqlite database" * 100)
    assert not restore_backup(dbh, str(garbage))
    assert dbh.is_db_connected()
    dbh.db.close()
    assert read_meta(work_db_path)["marker"] == "current session"
    assert not (work_db_path.parent / "db_restore_temp.db").exists()
