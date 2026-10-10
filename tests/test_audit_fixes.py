import sqlite3
from pathlib import Path

import pytest
from PySide6.QtSql import QSqlTableModel

from base.backup import save_backup
from gui.paymenthistorymodel import PaymentHistoryTableModel
from tests.dbtools import create_db, read_meta
from tests.test_readpath import add_event, add_payment, day, db_file, models, open_models, run_sql  # noqa: F401


def new_event_data(receiver: str = "ООО Новое") -> list:
    return [receiver, 0, 1, 0, 1101, 0, "n", "100.00", 0, day(5), day(0), 0, "d", 1, "", 0, 0, receiver.lower()]


def make_payment_model() -> PaymentHistoryTableModel:
    payment_model = PaymentHistoryTableModel()
    payment_model.setTable("payment")
    payment_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
    payment_model.select()
    return payment_model


def query_all(path: Path, sql: str, *params) -> list[tuple]:
    con = sqlite3.connect(path)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def prepare_events_with_payments(models) -> list[int]:
    ids = [add_event(models.path) for _ in range(5)]
    for event_id in ids:
        for _ in range(3):
            add_payment(models.path, event_id, day(-1), "1.00")
    models.base.select()
    return ids


def test_inserted_event_id_is_known_right_after_insert(models):
    prepare_events_with_payments(models)
    assert models.base.insert_row(new_event_data()) is not None
    stored = query_all(models.path, "SELECT MAX(id) FROM event")[0][0]
    assert models.base.last_inserted_id == stored


def test_refund_keeps_event_id_even_though_payment_is_inserted_after(models, shared_dbh):
    prepare_events_with_payments(models)
    payment_model = make_payment_model()
    assert shared_dbh.run_in_transaction(
        lambda: models.base.insert_row(new_event_data()) is not None
        and payment_model.append_row([models.base.last_inserted_id, day(5), "-100.00", day(0)]))
    event_id = query_all(models.path, "SELECT MAX(id) FROM event")[0][0]
    payment_id = query_all(models.path, "SELECT MAX(id) FROM payment")[0][0]
    assert models.base.last_inserted_id == event_id != payment_id
    assert query_all(models.path, "SELECT eventid, sum FROM payment WHERE id = ?", payment_id) == [(event_id, "-100.00")]


def test_failed_refund_payment_leaves_no_event(models, shared_dbh):
    prepare_events_with_payments(models)
    events_before = query_all(models.path, "SELECT COUNT(*) FROM event")[0][0]
    payment_model = make_payment_model()
    assert not shared_dbh.run_in_transaction(
        lambda: models.base.insert_row(new_event_data()) is not None
        and payment_model.append_row([models.base.last_inserted_id, day(5), "-100.00", day(0)])
        and False)
    models.base.select()
    assert query_all(models.path, "SELECT COUNT(*) FROM event")[0][0] == events_before
    assert models.base.rowCount() == events_before


def test_failed_submit_reverts_insert(models, monkeypatch):
    prepare_events_with_payments(models)
    rows_before = models.base.rowCount()
    monkeypatch.setattr(models.base, "submitAll", lambda: False)
    assert models.base.insert_row(new_event_data()) is None
    assert models.base.rowCount() == rows_before
    assert models.base.last_inserted_id == 0


def test_deleting_event_removes_its_payments_only(models, shared_dbh):
    ids = prepare_events_with_payments(models)
    target, other = ids[1], ids[2]
    row = models.source_row(target)
    assert shared_dbh.run_in_transaction(lambda: shared_dbh.delete_payments_by_event(target) and models.base.delete_row(row) != 0)
    assert query_all(models.path, "SELECT COUNT(*) FROM event WHERE id = ?", target)[0][0] == 0
    assert query_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", target)[0][0] == 0
    assert query_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", other)[0][0] == 3
    assert query_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid NOT IN (SELECT id FROM event)")[0][0] == 0


def test_failed_event_deletion_restores_payments(models, shared_dbh):
    ids = prepare_events_with_payments(models)
    target = ids[1]
    assert not shared_dbh.run_in_transaction(lambda: shared_dbh.delete_payments_by_event(target) and False)
    assert query_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", target)[0][0] == 3


def test_transaction_rolls_back_on_exception(models, shared_dbh):
    def broken() -> bool:
        shared_dbh.set_setting("marker", "changed")
        raise RuntimeError("boom")

    shared_dbh.set_setting("marker", "original")
    assert not shared_dbh.run_in_transaction(broken)
    assert shared_dbh.get_setting("marker") == "original"
    assert shared_dbh.set_setting("marker", "next")


def test_personal_data_is_saved_atomically(models, shared_dbh):
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'a', 1, NULL, 0)")
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (2, 'b', 1, NULL, 0)")
    shared_dbh.personal_data_max_id = 1
    assert not shared_dbh.save_personal_data([[1, "changed", 1, 0, 0], [2, "duplicate", 1, 0, 0]])
    assert query_all(models.path, "SELECT name FROM personal ORDER BY id") == [("a",), ("b",)]
    assert shared_dbh.save_personal_data([[1, "changed", 1, 0, 0]])
    assert query_all(models.path, "SELECT name FROM personal ORDER BY id") == [("changed",), ("b",)]


def test_deleting_position_clears_it_from_personal(models, shared_dbh):
    run_sql(models.path, "INSERT INTO position (id, department, name) VALUES (7, 1, 'boss')")
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'a', 1, 7, 0)")
    assert shared_dbh.delete_position(7)
    assert query_all(models.path, "SELECT COUNT(*) FROM position")[0][0] == 0
    assert query_all(models.path, "SELECT position FROM personal")[0][0] is None


class FakeSettings:
    def __init__(self, folder: Path):
        self.folder = folder

    def backup_path(self) -> str:
        return str(self.folder)


def test_backup_is_consistent_copy_made_by_vacuum(dbh, work_db_path, backup_folder):
    create_db(work_db_path, dbh.DB_VERSION, {"marker": "original"})
    assert dbh.migrate_db()
    dbh.open_db_connection()
    dbh.set_setting("marker", "changed")
    saved_at = save_backup(FakeSettings(backup_folder), dbh)
    assert saved_at.isValid()
    copies = list(backup_folder.glob("backup_*.db"))
    assert len(copies) == 1
    assert read_meta(copies[0])["marker"] == "changed"
    assert not list(backup_folder.glob("*.db-journal"))


def test_backup_to_missing_folder_is_reported(dbh, work_db_path, backup_folder):
    create_db(work_db_path, dbh.DB_VERSION)
    dbh.open_db_connection()
    assert not save_backup(FakeSettings(backup_folder / "missing"), dbh).isValid()


def test_backup_failure_is_reported(dbh, work_db_path, backup_folder, monkeypatch):
    create_db(work_db_path, dbh.DB_VERSION)
    dbh.open_db_connection()
    monkeypatch.setattr(dbh, "copy_db_file", lambda target: False)
    assert not save_backup(FakeSettings(backup_folder), dbh).isValid()


def test_migration_closes_database_when_version_is_unreadable(dbh, work_db_path):
    work_db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(work_db_path)
    con.execute("CREATE TABLE unrelated (x INTEGER)")
    con.commit()
    con.close()
    assert not dbh.migrate_db()
    assert not dbh.db.isOpen()
