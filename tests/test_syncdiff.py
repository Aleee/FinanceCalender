import sqlite3
from pathlib import Path

import pytest

from base.syncdiff import describe_changes, diff_summary, format_diff
from tests.dbtools import create_db


def insert_event(path: Path, event_id: int, receiver: str = "ООО Ромашка", name: str = "Поставка", amount: str = "100.00",
                 duedate: str = "2026-10-15") -> None:
    con = sqlite3.connect(path)
    con.execute("INSERT INTO event (id, receiver, name, totalamount, duedate, receivernocase) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, receiver, name, amount, duedate, receiver.lower()))
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
    assert diff_summary(diff) == "" and format_diff(diff) == ""


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
    assert describe_changes(old_row, new_row) == "сумма: 100.00 → 120.00"
    assert [(row["id"], row["event_title"]) for row in payments.added] == [(2, "ООО Лютик — Аренда"), (3, "ООО Ромашка — Поставка")]
    assert not payments.removed and not payments.changed
    assert diff_summary(diff) == "Платежи: добавлено 1, изменено 1, удалено 1\nОплаты: добавлено 2"
    text = format_diff(diff)
    assert "+ ООО Лютик — Аренда, 900.00, срок 15.10.2026" in text
    assert "~ ООО Ромашка — Поставка, 120.00, срок 15.10.2026 (сумма: 100.00 → 120.00)" in text
    assert "− ИП Иванов — Поставка, 50.00, срок 15.10.2026" in text


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
    con.execute("INSERT INTO contractor (id, name) VALUES (1, 'Новый')")
    con.execute("INSERT INTO meta (key, value) VALUES ('sync_token', 'x'), ('change_counter', '7')")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old_db), str(new_db))
    assert diff.other_tables == {"contractor": (1, 0)}
    assert "Изменены также: контрагенты" in diff_summary(diff)
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


def test_long_lists_are_truncated(dbh, old_db, new_db):
    for event_id in range(10, 50):
        insert_event(new_db, event_id)
    text = format_diff(dbh.read_db_diff(str(old_db), str(new_db)))
    assert "… и ещё 10" in text
