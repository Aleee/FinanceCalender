from pathlib import Path

import pytest

from base.contract import SavedContractValues
from tests.dbtools import create_db, fetch_all, read_meta, read_version, table_columns

COLUMNS = ["contractdocumentid", "receiver", "category", "subcategory", "name", "nds", "paymenttype", "descr", "responsible", "hidden"]


@pytest.fixture
def old_db(dbh, work_db_path: Path) -> Path:
    create_db(work_db_path, 4)
    return work_db_path


@pytest.fixture
def migrated_db(dbh, old_db: Path) -> Path:
    assert dbh.migrate_db()
    assert dbh.open_db_connection()
    return old_db


def values(doc_id: int = 7, name: str = "Услуги") -> SavedContractValues:
    return SavedContractValues(doc_id, "ООО Ромашка", 2, 3, name, 20, 1, "описание", 4, 0)


def test_migration_to_v6_recreates_savedvalues_table(dbh, old_db):
    assert dbh.migrate_db()
    assert read_version(old_db) == 6
    assert table_columns(old_db, "contractsavedvalues") == COLUMNS


def test_migration_to_v6_keeps_savedvalues_triggers(dbh, old_db):
    assert dbh.migrate_db()
    triggers = fetch_all(old_db, "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'contractsavedvalues'")
    assert sorted(name for (name,) in triggers) == [f"trg_contractsavedvalues_{action}" for action in ("delete", "insert", "update")]


def test_save_and_load_contract_values(dbh, migrated_db):
    assert dbh.load_contractdocumentvalues(7) is None
    assert dbh.save_contractdocumentvalues(values())
    assert dbh.load_contractdocumentvalues(7) == values()


def test_save_contract_values_updates_existing_row(dbh, migrated_db):
    assert dbh.save_contractdocumentvalues(values())
    assert dbh.save_contractdocumentvalues(values(name="Другое"))
    assert dbh.save_contractdocumentvalues(values(doc_id=8))
    assert fetch_all(migrated_db, "SELECT COUNT(*) FROM contractsavedvalues") == [(2,)]
    assert dbh.load_contractdocumentvalues(7).name == "Другое"


def test_save_contract_values_increases_change_counter(dbh, migrated_db):
    before = int(read_meta(migrated_db)["change_counter"])
    assert dbh.save_contractdocumentvalues(values())
    assert int(read_meta(migrated_db)["change_counter"]) > before
