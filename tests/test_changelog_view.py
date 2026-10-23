from datetime import date
from decimal import Decimal
from platform import node

from base.changelog import build_operations
from base.syncdiff import format_value
from gui.changelogdialog import ChangeLogDialog
from tests.test_changelog import current_db, event_data, event_id, execute  # noqa: F401


def operations_of(dbh, event: int, resolvers=None):
    records, payments = dbh.load_changelog(event)
    return build_operations(records, payments, resolvers)


def test_history_collects_event_and_payment_operations(dbh, current_db, event_id):
    payment_id = dbh.insert_payment([event_id, "2026-10-10", "30.00", "2026-10-10"])
    assert dbh.update_event_field(event_id, "name", "Аренда офиса")
    assert dbh.update_payment(payment_id, date(2026, 10, 11), Decimal("40.00"), Decimal("100.00"))
    assert dbh.delete_payment(payment_id)

    operations = operations_of(dbh, event_id)

    first = f"{format_value('30.00', 'sum')} от {format_value('2026-10-10')}"
    last = f"{format_value('40.00', 'sum')} от {format_value('2026-10-11')}"
    assert [operation.title for operation in operations] == [
        f"Оплата {last} удалена", f"Оплата {last} изменена", "Платеж изменён", f"Оплата {first} добавлена", "Платеж добавлен"]


def test_update_operation_lists_changed_fields(dbh, current_db, event_id):
    assert dbh.update_event_field(event_id, "totalamount", "120.00")
    operation = operations_of(dbh, event_id)[0]
    assert operation.title == "Платеж изменён"
    assert operation.fields == [("Сумма", format_value("100.00", "totalamount"), format_value("120.00", "totalamount"))]
    assert (operation.author, operation.machine) == ("tester", node())


def test_insert_and_delete_show_snapshot_without_service_columns(dbh, current_db, event_id):
    assert dbh.delete_event(event_id)
    delete, insert = operations_of(dbh, event_id)
    titles = [title for title, _, _ in insert.fields]
    assert "Получатель" in titles and "Id" not in titles and "На контроле" not in titles
    assert all(old == "—" for _, old, _ in insert.fields)
    assert all(new == "—" for _, _, new in delete.fields)
    assert ("Получатель", "ООО Ромашка", "—") in delete.fields


def test_history_is_limited_to_the_selected_event(dbh, current_db, event_id):
    other = dbh.insert_event(event_data(receiver="Другой", type=2, name="Иное"))
    assert dbh.insert_payment([other, "2026-10-10", "5.00", "2026-10-10"]) is not None
    assert [operation.title for operation in operations_of(dbh, event_id)] == ["Платеж добавлен"]


def test_resolvers_replace_stored_values(dbh, current_db, event_id):
    assert dbh.update_event_field(event_id, "responsible", "7")
    operation = operations_of(dbh, event_id, {"responsible": lambda value: {"7": "Иванов"}.get(value)})[0]
    assert operation.fields == [("Ответственный", "—", "Иванов")]


def test_dialog_filters_by_scope_and_shows_machine_in_tooltip(qapp, dbh, current_db, event_id):
    assert dbh.insert_payment([event_id, "2026-10-10", "30.00", "2026-10-10"]) is not None
    dialog = ChangeLogDialog(operations_of(dbh, event_id), "Аренда")
    assert dialog.tree.topLevelItemCount() == 2
    assert dialog.tree.topLevelItem(0).text(1) == "tester"
    assert node() in dialog.tree.topLevelItem(0).toolTip(1)
    dialog.cmb_scope.setCurrentIndex(2)
    assert dialog.tree.topLevelItemCount() == 1
    assert dialog.tree.topLevelItem(0).text(2).startswith("Оплата")


def test_dialog_without_records_shows_empty_note(qapp):
    dialog = ChangeLogDialog([], "Аренда")
    dialog.show()
    assert dialog.la_empty.isVisible() and not dialog.tree.isVisible()
