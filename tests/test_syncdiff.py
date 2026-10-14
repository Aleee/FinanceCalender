import sqlite3
from pathlib import Path

import pytest

from base.syncdiff import describe_other_table, describe_row, field_changes, format_value
from tests.dbtools import create_db


def insert_event(path: Path, event_id: int, receiver: str = "ООО Ромашка", name: str = "Поставка", amount: str = "100.00",
                 duedate: str = "2026-10-15") -> None:
    con = sqlite3.connect(path)
    con.execute("INSERT INTO event (id, receiver, name, totalamount, duedate) VALUES (?, ?, ?, ?, ?)",
                (event_id, receiver, name, amount, duedate))
    con.commit()
    con.close()


def insert_payment(path: Path, payment_id: int, event_id: int, amount: str, paymentdate: str = "2026-10-11") -> None:
    con = sqlite3.connect(path)
    con.execute("INSERT INTO payment (id, eventid, paymentdate, sum) VALUES (?, ?, ?, ?)", (payment_id, event_id, paymentdate, amount))
    con.commit()
    con.close()


@pytest.fixture
def old_db(tmp_path) -> Path:
    path = create_db(tmp_path / "old.db", 5)
    insert_event(path, 1)
    insert_event(path, 2, receiver="ИП Иванов", amount="50.00")
    insert_payment(path, 1, 1, "40.00")
    return path


@pytest.fixture
def new_db(tmp_path, old_db) -> Path:
    path = tmp_path / "new.db"
    path.write_bytes(old_db.read_bytes())
    return path


def test_identical_files_have_empty_diff(dbh, old_db, new_db):
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert diff is not None and diff.is_empty


def test_added_changed_removed_events_and_payments(dbh, old_db, new_db):
    insert_event(new_db, 3, receiver="ООО Лютик", name="Аренда", amount="900.00")
    insert_payment(new_db, 2, 3, "300.00")
    insert_payment(new_db, 3, 1, "10.00")
    con = sqlite3.connect(new_db)
    con.execute("UPDATE event SET totalamount = '120.00' WHERE id = 1")
    con.execute("DELETE FROM event WHERE id = 2")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    events, payments = diff.tables["event"], diff.tables["payment"]
    assert [row["id"] for row in events.added] == [3]
    assert [row["id"] for row in events.removed] == [2]
    old_row, new_row = events.changed[0]
    assert (old_row["totalamount"], new_row["totalamount"]) == ("100.00", "120.00")
    assert field_changes(old_row, new_row) == [("Сумма", "100,00", "120,00")]
    assert [(row["id"], row["event_title"]) for row in payments.added] == [(2, "ООО Лютик — Аренда"), (3, "ООО Ромашка — Поставка")]
    assert not payments.removed and not payments.changed
    assert describe_row("event", events.added[0]) == "ООО Лютик — Аренда, 900,00, срок 15.10.2026"
    assert describe_row("event", events.removed[0]) == "ИП Иванов — Поставка, 50,00, срок 15.10.2026"
    assert describe_row("payment", payments.added[0]) == "ООО Лютик — Аренда: 300,00 от 11.10.2026"


def test_contract_tables_are_described_by_names(dbh, old_db, new_db):
    con = sqlite3.connect(new_db)
    con.execute("INSERT INTO contractor (id, name) VALUES (1, 'ООО Ромашка')")
    con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '12', '2026-02-01')")
    con.execute("INSERT INTO contractdocument (id, contract_id, document_name) VALUES (1, 1, 'Приложение 1')")
    con.execute("INSERT INTO contractpaymentterm (document_id, payment_type) VALUES (1, 'RELATIVE')")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert not diff.other_tables
    label = "ООО Ромашка — № 12 от 01.02.2026"
    assert describe_row("contractor", diff.tables["contractor"].added[0]) == "ООО Ромашка"
    assert describe_row("contract", diff.tables["contract"].added[0]) == label
    assert describe_row("contractdocument", diff.tables["contractdocument"].added[0]) == f"{label} — Приложение 1"
    assert describe_row("contractpaymentterm", diff.tables["contractpaymentterm"].added[0]) == f"Сроки оплаты: {label} — Приложение 1"
    assert diff.added_ids("contractpaymentterm") == [1]


def test_changed_contract_and_document_fields(dbh, old_db, new_db):
    for path in (old_db, new_db):
        con = sqlite3.connect(path)
        con.execute("INSERT INTO contractor (id, name) VALUES (1, 'ООО Ромашка'), (2, 'ИП Иванов')")
        con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '12', '2026-02-01')")
        con.execute("INSERT INTO contractdocument (id, contract_id, document_name) VALUES (1, 1, 'Приложение 1')")
        con.commit()
        con.close()
    con = sqlite3.connect(new_db)
    con.execute("UPDATE contract SET contractor_id = 2 WHERE id = 1")
    con.execute("UPDATE contractdocument SET document_name = 'Приложение 2' WHERE id = 1")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert field_changes(*diff.tables["contract"].changed[0]) == [("Контрагент", "ООО Ромашка", "ИП Иванов")]
    assert field_changes(*diff.tables["contractdocument"].changed[0]) == [("Название документа", "Приложение 1", "Приложение 2")]


def test_format_value_uses_readable_names():
    assert format_value("1156.9", "sum") == "1 156,90"
    assert format_value(1101, "category") == "1.1. Заработная плата с налогами на з/п"
    assert format_value(2, "paymenttype") == "Предоплата"
    assert (format_value(0, "hidden"), format_value(1, "featured")) == ("нет", "да")
    assert format_value(20, "nds") == "20%"
    assert format_value("", "sum") == "—" and format_value("2026-10-15") == "15.10.2026"
    assert format_value("не число", "sum") == "не число" and format_value(9999, "category") == "9999"


def test_responsible_is_shown_by_name(dbh, old_db, new_db):
    for path in (old_db, new_db):
        con = sqlite3.connect(path)
        con.execute("INSERT INTO personal (id, name) VALUES (1, 'Иванов И.'), (2, 'Петров П.')")
        con.execute("UPDATE event SET responsible = '1' WHERE id = 1")
        con.commit()
        con.close()
    con = sqlite3.connect(new_db)
    con.execute("UPDATE event SET responsible = '2' WHERE id = 1")
    con.commit()
    con.close()
    old_row, new_row = dbh.read_db_diff(str(old_db), str(new_db)).tables["event"].changed[0]
    assert field_changes(old_row, new_row) == [("Ответственный", "Иванов И.", "Петров П.")]


def test_removed_payment_uses_old_event_title(dbh, old_db, new_db):
    con = sqlite3.connect(new_db)
    con.execute("DELETE FROM payment WHERE id = 1")
    con.execute("DELETE FROM event WHERE id = 1")
    con.commit()
    con.close()
    removed = dbh.read_db_diff(str(old_db), str(new_db)).tables["payment"].removed
    assert removed[0]["event_title"] == "ООО Ромашка — Поставка"


def test_other_tables_counted_and_service_meta_ignored(dbh, old_db, new_db):
    con = sqlite3.connect(new_db)
    con.execute("INSERT INTO department (id, name) VALUES (1, 'Новый')")
    con.execute("INSERT INTO meta (key, value) VALUES ('sync_token', 'x'), ('change_counter', '7')")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert diff.other_tables == {"department": (1, 0)}
    assert describe_other_table("department", diff.other_tables["department"]).startswith("Отделы:")
    con = sqlite3.connect(new_db)
    con.execute("INSERT INTO meta (key, value) VALUES ('Calendar/2028/holidays', '1')")
    con.commit()
    con.close()
    assert dbh.read_db_diff(str(old_db), str(new_db)).other_tables["meta"] == (1, 0)


def test_missing_columns_in_old_file_are_ignored(dbh, old_db, new_db):
    con = sqlite3.connect(new_db)
    con.execute("ALTER TABLE payment ADD COLUMN extra TEXT")
    con.execute("UPDATE payment SET extra = 'v'")
    con.commit()
    con.close()
    assert dbh.read_db_diff(str(old_db), str(new_db)).is_empty


def test_unreadable_file_gives_none(dbh, old_db, tmp_path):
    broken = tmp_path / "broken.db"
    broken.write_text("не база данных")
    assert dbh.read_db_diff(str(old_db), str(broken)) is None


def test_finplan_and_fulfillmentdata_are_compared_by_natural_key(dbh, old_db, new_db):
    for path in (old_db, new_db):
        con = sqlite3.connect(path)
        con.execute("INSERT INTO finplan (year, category, m1) VALUES (2027, 10000, 100), (2027, 21000, 200)")
        con.commit()
        con.close()
    con = sqlite3.connect(new_db)
    con.execute("UPDATE finplan SET m1 = 150 WHERE category = 10000")
    con.execute("DELETE FROM finplan WHERE category = 21000")
    con.execute("INSERT INTO finplan (year, category, m1) VALUES (2028, 10000, 5)")
    con.execute("INSERT INTO fulfillmentdata (startdate, enddate, \"10000\") VALUES ('2026-06-01', '2026-06-30', 9603)")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert not diff.other_tables
    finplan = diff.tables["finplan"]
    assert diff.added_ids("finplan") == ["2028/10000"] and [row["rowkey"] for row in finplan.removed] == ["2027/21000"]
    assert describe_row("finplan", finplan.added[0]) == "Финплан 2028: 1. Остаток средств на начало периода"
    assert field_changes(*finplan.changed[0]) == [("Январь", "100,00", "150,00")]
    assert describe_row("fulfillmentdata", diff.tables["fulfillmentdata"].added[0]) == "Исполнение за 01.06.2026 — 30.06.2026"
