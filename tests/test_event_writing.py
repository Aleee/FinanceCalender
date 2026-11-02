from PySide6.QtSql import QSqlTableModel

from base.migrations import change_counter_triggers
from gui.paymenthistorymodel import PaymentHistoryTableModel
from tests.dbtools import fetch_all, read_meta
from tests.test_readpath import add_event, add_payment, day, db_file, models, open_models, run_sql  # noqa: F401


def new_event_data(receiver: str = "ООО Новое") -> list:
    return [receiver, 0, 1, 0, 1101, 0, "n", "100.00", 0, day(5), day(0), 0, "d", 1, "", 0, 0]


def make_payment_model(dbh) -> PaymentHistoryTableModel:
    payment_model = PaymentHistoryTableModel(dbh)
    payment_model.setTable("payment")
    payment_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
    payment_model.select()
    return payment_model


def prepare_events_with_payments(models) -> list[int]:
    ids = [add_event(models.path) for _ in range(5)]
    for event_id in ids:
        for _ in range(3):
            add_payment(models.path, event_id, day(-1), "1.00")
    models.table.reload()
    return ids


def test_inserted_event_id_is_known_right_after_insert(models):
    prepare_events_with_payments(models)
    event_id = models.table.insert_event(new_event_data())
    stored = fetch_all(models.path, "SELECT MAX(id) FROM event")[0][0]
    assert event_id == stored == models.table.last_inserted_id
    assert models.store.event_values(event_id) is not None


def test_refund_keeps_event_id_even_though_payment_is_inserted_after(models, shared_dbh):
    prepare_events_with_payments(models)
    payment_model = make_payment_model(shared_dbh)
    assert shared_dbh.run_in_transaction(
        lambda: models.table.insert_event(new_event_data()) is not None
        and payment_model.append_row([models.table.last_inserted_id, day(5), "-100.00", day(0)]))
    event_id = fetch_all(models.path, "SELECT MAX(id) FROM event")[0][0]
    payment_id = fetch_all(models.path, "SELECT MAX(id) FROM payment")[0][0]
    assert models.table.last_inserted_id == event_id != payment_id
    assert fetch_all(models.path, "SELECT eventid, sum FROM payment WHERE id = ?", payment_id) == [(event_id, "-100.00")]


def test_failed_refund_payment_leaves_no_event(models, shared_dbh):
    prepare_events_with_payments(models)
    events_before = fetch_all(models.path, "SELECT COUNT(*) FROM event")[0][0]
    payment_model = make_payment_model(shared_dbh)
    assert not shared_dbh.run_in_transaction(
        lambda: models.table.insert_event(new_event_data()) is not None
        and payment_model.append_row([models.table.last_inserted_id, day(5), "-100.00", day(0)])
        and False)
    models.table.reload()
    assert fetch_all(models.path, "SELECT COUNT(*) FROM event")[0][0] == events_before
    assert len(models.store.events) == events_before


def test_failed_insert_leaves_no_event_and_keeps_last_inserted_id(models):
    prepare_events_with_payments(models)
    events_before = len(models.store.events)
    run_sql(models.path, "CREATE TRIGGER block_insert BEFORE INSERT ON event BEGIN SELECT RAISE(ABORT, 'blocked'); END")
    assert models.table.insert_event(new_event_data()) is None
    assert len(models.store.events) == events_before
    assert fetch_all(models.path, "SELECT COUNT(*) FROM event")[0][0] == events_before
    assert models.table.last_inserted_id == 0


def test_failed_edit_changes_nothing_and_reloads_table(models):
    ids = prepare_events_with_payments(models)
    before = fetch_all(models.path, "SELECT * FROM event WHERE id = ?", ids[0])
    run_sql(models.path, "CREATE TRIGGER block_update BEFORE UPDATE ON event BEGIN SELECT RAISE(ABORT, 'blocked'); END")
    assert not models.table.edit_event(ids[0], new_event_data("ООО Другое"))
    assert fetch_all(models.path, "SELECT * FROM event WHERE id = ?", ids[0]) == before
    assert models.value(ids[0], 0) == "ООО Ромашка"


def test_edit_without_changes_does_not_touch_change_counter(models):
    ids = prepare_events_with_payments(models)
    run_sql(models.path, "INSERT INTO meta (key, value) VALUES ('change_counter', '0')")
    for trigger in change_counter_triggers():
        run_sql(models.path, trigger)
    counter_before = read_meta(models.path)["change_counter"]
    assert models.table.edit_event(ids[0], list(models.store.event_values(ids[0])))
    assert read_meta(models.path)["change_counter"] == counter_before
    assert models.table.edit_event(ids[0], new_event_data("ООО Другое"))
    assert int(read_meta(models.path)["change_counter"]) > int(counter_before)


def test_edit_event_that_does_not_exist_fails(models):
    prepare_events_with_payments(models)
    assert not models.table.edit_event(99999, new_event_data())


def test_deleting_event_removes_its_payments_only(models, shared_dbh):
    ids = prepare_events_with_payments(models)
    target, other = ids[1], ids[2]
    assert shared_dbh.run_in_transaction(lambda: shared_dbh.delete_payments_by_event(target) and models.table.delete_event(target))
    assert models.store.event_values(target) is None
    assert fetch_all(models.path, "SELECT COUNT(*) FROM event WHERE id = ?", target)[0][0] == 0
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", target)[0][0] == 0
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", other)[0][0] == 3
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid NOT IN (SELECT id FROM event)")[0][0] == 0


def test_deleted_event_is_restored_with_payments(models, shared_dbh):
    ids = prepare_events_with_payments(models)
    target = ids[1]
    event, payments = shared_dbh.load_event_backup(target)
    assert len(payments) == 3
    events_before = fetch_all(models.path, "SELECT * FROM event WHERE id = ?", target)
    payments_before = fetch_all(models.path, "SELECT * FROM payment WHERE eventid = ?", target)
    assert shared_dbh.run_in_transaction(lambda: shared_dbh.delete_payments_by_event(target) and models.table.delete_event(target))
    assert models.table.restore_event(event, payments)
    assert models.table.last_inserted_id == target
    assert models.store.event_values(target) is not None
    assert fetch_all(models.path, "SELECT * FROM event WHERE id = ?", target) == events_before
    assert fetch_all(models.path, "SELECT * FROM payment WHERE eventid = ?", target) == payments_before
