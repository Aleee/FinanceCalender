from tests.dbtools import fetch_all
from tests.test_readpath import db_file, models, open_models, run_sql  # noqa: F401
from tests.test_event_writing import prepare_events_with_payments


def test_nested_transaction_is_committed_once_by_outer(models, shared_dbh):
    shared_dbh.set_setting("marker", "original")

    def outer() -> bool:
        assert shared_dbh.run_in_transaction(lambda: shared_dbh.set_setting("marker", "inner"))
        return False

    assert not shared_dbh.run_in_transaction(outer)
    assert shared_dbh.get_setting("marker") == "original"
    assert not shared_dbh.in_transaction
    assert shared_dbh.run_in_transaction(lambda: shared_dbh.set_setting("marker", "next"))
    assert shared_dbh.get_setting("marker") == "next"


def test_transaction_rolls_back_on_exception(models, shared_dbh):
    def broken() -> bool:
        shared_dbh.set_setting("marker", "changed")
        raise RuntimeError("boom")

    shared_dbh.set_setting("marker", "original")
    assert not shared_dbh.run_in_transaction(broken)
    assert shared_dbh.get_setting("marker") == "original"
    assert shared_dbh.set_setting("marker", "next")


def test_failed_event_deletion_restores_payments(models, shared_dbh):
    ids = prepare_events_with_payments(models)
    target = ids[1]
    assert not shared_dbh.run_in_transaction(lambda: shared_dbh.delete_payments_by_event(target) and False)
    assert fetch_all(models.path, "SELECT COUNT(*) FROM payment WHERE eventid = ?", target)[0][0] == 3


def test_personal_data_is_saved_atomically(models, shared_dbh):
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'a', 1, NULL, 0)")
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (2, 'b', 1, NULL, 0)")
    shared_dbh.personal_data_max_id = 1
    assert not shared_dbh.save_personal_data([[1, "changed", 1, 0, 0], [2, "duplicate", 1, 0, 0]])
    assert fetch_all(models.path, "SELECT name FROM personal ORDER BY id") == [("a",), ("b",)]
    assert shared_dbh.save_personal_data([[1, "changed", 1, 0, 0]])
    assert fetch_all(models.path, "SELECT name FROM personal ORDER BY id") == [("changed",), ("b",)]


def test_deleting_position_clears_it_from_personal(models, shared_dbh):
    run_sql(models.path, "INSERT INTO position (id, department, name) VALUES (7, 1, 'boss')")
    run_sql(models.path, "INSERT INTO personal (id, name, department, position, archived) VALUES (1, 'a', 1, 7, 0)")
    assert shared_dbh.delete_position(7)
    assert fetch_all(models.path, "SELECT COUNT(*) FROM position")[0][0] == 0
    assert fetch_all(models.path, "SELECT position FROM personal")[0][0] is None
