import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QDate

from base.contract import ContractDocumentData, PaymentDueType
from tests.dbtools import create_db, fetch_all, table_columns


@pytest.fixture
def old_db(dbh, work_db_path: Path) -> Path:
    create_db(work_db_path, 8)
    with closing(sqlite3.connect(work_db_path)) as con, con:
        con.execute("INSERT INTO contractor (id, name) VALUES (1, 'ООО Ромашка')")
        con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '1', '2026-01-01')")
    return work_db_path


@pytest.fixture
def migrated_db(dbh, old_db: Path) -> Path:
    assert dbh.migrate_db()
    assert dbh.open_db_connection()
    return old_db


def document(document_id: int = 0, monthly: bool = False, monthly_amount: Decimal | None = None,
             monthly_name: str = "") -> ContractDocumentData:
    return ContractDocumentData(
        document_id=document_id, contractor_id=1, contractor_name="", contract_id=1, contract_number="1",
        contract_date=QDate(2026, 1, 1), document_type=3, position_id=0, document_name="Акт", description="",
        payment_type=PaymentDueType.PREPAYMENT, monthly=monthly, monthly_amount=monthly_amount,
        monthly_name=monthly_name)


def test_migration_to_v9_adds_monthly_columns(dbh, old_db):
    with closing(sqlite3.connect(old_db)) as con, con:
        con.execute("INSERT INTO contractdocument (id, contract_id, document_name) VALUES (1, 1, 'Акт')")

    assert dbh.migrate_db()

    assert table_columns(old_db, "contractdocument")[-3:] == ["monthly", "monthlyamount", "monthlyname"]
    assert fetch_all(old_db, "SELECT monthly, monthlyamount, monthlyname FROM contractdocument") == [(0, None, None)]


def test_monthly_document_roundtrip(dbh, migrated_db):
    document_id = dbh.save_document_data(document(monthly=True, monthly_amount=Decimal("5600.39")))
    assert document_id

    loaded = dbh.load_document_data(document_id)
    assert loaded.monthly is True
    assert loaded.monthly_amount == Decimal("5600.39")


def test_monthly_amount_is_dropped_when_flag_is_off(dbh, migrated_db):
    document_id = dbh.save_document_data(document(monthly=True, monthly_amount=Decimal("100")))
    assert dbh.save_document_data(document(document_id, monthly=False, monthly_amount=Decimal("100"))) == document_id

    loaded = dbh.load_document_data(document_id)
    assert loaded.monthly is False
    assert loaded.monthly_amount is None


def test_monthly_name_roundtrip_and_dropped_when_flag_is_off(dbh, migrated_db):
    document_id = dbh.save_document_data(document(monthly=True, monthly_name="  Аренда за {месяц} {год} г. "))
    assert dbh.load_document_data(document_id).monthly_name == "Аренда за {месяц} {год} г."

    assert dbh.save_document_data(document(document_id, monthly=False, monthly_name="Аренда")) == document_id
    assert dbh.load_document_data(document_id).monthly_name == ""
    assert fetch_all(migrated_db, "SELECT monthlyname FROM contractdocument") == [(None,)]


def test_monthly_without_amount(dbh, migrated_db):
    document_id = dbh.save_document_data(document(monthly=True))

    loaded = dbh.load_document_data(document_id)
    assert loaded.monthly is True
    assert loaded.monthly_amount is None
