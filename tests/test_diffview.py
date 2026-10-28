import sqlite3
from datetime import datetime
from decimal import Decimal

from PySide6.QtWidgets import QTabWidget

from base.diffview import ADDED, CHANGED, REMOVED, build_entries, format_time, summary_lines
from base.syncdiff import DbDiff, TableDiff
from base.version import DB_VERSION
from gui.syncchangesdialog import DiffView, SyncChangesDialog
from tests.dbtools import create_db
from tests.test_syncdiff import insert_event, insert_payment


def event_row(row_id: int, receiver: str = "ООО Ромашка", name: str = "Аренда", amount: str = "100", due: str = "2026-10-15") -> dict:
    return {"id": row_id, "receiver": receiver, "name": name, "totalamount": amount, "duedate": due}


def payment_row(row_id: int, event_id: int, amount: str = "40", title: str = "ООО Ромашка — Аренда") -> dict:
    return {"id": row_id, "eventid": event_id, "sum": amount, "paymentdate": "2026-10-11", "event_title": title}


def sample_diff() -> DbDiff:
    events = TableDiff(added=[event_row(1)], changed=[(event_row(2, amount="50"), event_row(2, amount="60", due="2026-11-01"))],
                       removed=[event_row(3, receiver="ИП Иванов")])
    payments = TableDiff(added=[payment_row(10, 1, "40")], removed=[payment_row(11, 3, "8.5"), payment_row(12, 2, "1")])
    events.origins = {1: ("2026-10-11T14:32:00", "Иванов"), 2: ("2026-10-11T14:40:00", "Петров")}
    return DbDiff({"event": events, "payment": payments})


def many_events_diff(count: int = 12) -> DbDiff:
    added = [event_row(index, receiver=f"Получатель {index:02d}") for index in range(1, count + 1)]
    return DbDiff({"event": TableDiff(added=added, removed=[event_row(100, receiver="Удалённый")]),
                   "payment": TableDiff(added=[payment_row(200, 1)])})


def test_entries_have_separate_amount_and_date_columns():
    entries = {(entry.table, entry.action, entry.event_id): entry for entry in build_entries(sample_diff())}
    added = entries[("event", ADDED, 1)]
    assert (added.title, added.amount_text, added.date_text, added.kind) == ("ООО Ромашка — Аренда", "100,00", "15.10.2026", "Платеж")
    assert (added.author, added.changed_at) == ("Иванов", datetime(2026, 10, 11, 14, 32))
    payment = entries[("payment", ADDED, 1)]
    assert (payment.title, payment.amount_text, payment.date_text, payment.kind) == ("ООО Ромашка — Аренда", "40,00", "11.10.2026", "Оплата")


def test_changed_entry_marks_changed_amount_and_date():
    changed = next(entry for entry in build_entries(sample_diff()) if entry.action == CHANGED)
    assert changed.amount_text == "60,00" and changed.amount_changed and changed.date_changed
    assert changed.changes == [("Сумма", "50,00", "60,00"), ("Срок оплаты", "15.10.2026", "01.11.2026")]
    assert changed.changes_text == "Сумма: 50,00 → 60,00; Срок оплаты: 15.10.2026 → 01.11.2026"


def test_removed_event_cannot_be_opened_but_removed_payment_of_live_event_can():
    entries = build_entries(sample_diff())
    removed_event = next(entry for entry in entries if entry.table == "event" and entry.action == REMOVED)
    assert removed_event.event_id is None
    removed_payments = {entry.amount_text: entry for entry in entries if entry.table == "payment" and entry.action == REMOVED}
    assert removed_payments["8,50"].event_id is None
    assert removed_payments["1,00"].event_id == 2


def test_summary_lines_count_actions_and_sum_amounts():
    assert summary_lines(build_entries(sample_diff())) == [
        "Платежи: добавлено 1 на 100,00, изменено 1, удалено 1 на 100,00",
        "Оплаты: добавлено 1 на 40,00, удалено 2 на 9,50"]
    assert build_entries(sample_diff())[0].amount == Decimal("100")


def paid_diff() -> DbDiff:
    events = TableDiff(added=[event_row(1), event_row(2), event_row(3)], removed=[event_row(4, receiver="ИП Иванов"), event_row(5)])
    payments = TableDiff(added=[payment_row(10, 1, "100"), payment_row(11, 2, "60"), payment_row(12, 3, "40"), payment_row(13, 3, "60")],
                         removed=[payment_row(14, 4, "100"), payment_row(15, 5, "30")])
    return DbDiff({"event": events, "payment": payments})


def test_fully_paid_payment_is_merged_with_its_payments():
    entries = build_entries(paid_diff())
    merged = {entry.parent_id: entry for entry in entries if entry.merged}
    assert set(merged) == {1, 3, 4}
    assert [entry.amount_text for entry in merged[3].merged] == ["40,00", "60,00"]
    assert merged[1].kind == "Платеж + оплата" and merged[1].details == "Оплачен полностью 11.10.2026"
    assert merged[1].tables == {"event", "payment"} and merged[1].action == ADDED and merged[4].action == REMOVED
    assert merged[1].details_tooltip == "Оплата 100,00 от 11.10.2026"
    assert len(entries) == 7
    assert [entry.amount_text for entry in entries if entry.table == "payment"] == ["60,00", "30,00"]


def test_summary_counts_merged_payments_separately():
    assert summary_lines(build_entries(paid_diff())) == [
        "Платежи: добавлено 3 на 300,00, удалено 2 на 200,00",
        "Оплаты: добавлено 4 на 260,00, удалено 2 на 130,00"]


def test_merged_row_is_found_by_payment_filter_and_openable(qapp):
    view = DiffView(paid_diff(), openable=True)
    view.proxy.set_filters({ADDED, CHANGED, REMOVED}, "payment", "")
    assert view.proxy.rowCount() == 5
    assert next(entry for entry in view.entries if entry.merged and entry.parent_id == 1).event_id == 1
    assert next(entry for entry in view.entries if entry.merged and entry.parent_id == 4).event_id is None


def test_format_time_omits_current_year():
    now = datetime(2026, 10, 28, 12, 0)
    assert format_time(datetime(2026, 10, 11, 14, 32), now) == "11.10 14:32"
    assert format_time(datetime(2025, 12, 31, 9, 5), now) == "31.12.2025 09:05"
    assert format_time(None, now) == ""


def test_origins_read_from_changelog_of_new_file(dbh, tmp_path):
    old = create_db(tmp_path / "old.db", DB_VERSION)
    insert_event(old, 1)
    new = tmp_path / "new.db"
    new.write_bytes(old.read_bytes())
    con = sqlite3.connect(new)
    con.execute("DELETE FROM meta WHERE key = 'changelog_author'")
    con.execute("INSERT INTO meta (key, value) VALUES ('changelog_author', 'Иванов')")
    con.commit()
    con.close()
    insert_event(new, 2, receiver="ООО Лютик")
    insert_payment(new, 1, 2, "10.00")
    con = sqlite3.connect(new)
    con.execute("UPDATE event SET totalamount = '120.00' WHERE id = 1")
    con.commit()
    con.close()
    diff = dbh.read_db_diff(str(old), str(new))
    assert diff.tables["event"].origins[2][1] == "Иванов" and diff.tables["event"].origins[1][1] == "Иванов"
    assert diff.tables["payment"].origins[1][1] == "Иванов"
    assert datetime.fromisoformat(diff.tables["event"].origins[2][0])


def test_origins_empty_for_files_without_changelog(dbh, tmp_path):
    old = create_db(tmp_path / "old.db", 5)
    new = tmp_path / "new.db"
    new.write_bytes(old.read_bytes())
    insert_event(new, 1)
    diff = dbh.read_db_diff(str(old), str(new))
    assert diff.tables["event"].added and diff.tables["event"].origins == {}


def test_view_hides_columns_without_data(qapp):
    view = DiffView(DbDiff({"event": TableDiff(added=[event_row(1)])}))
    assert view.table.isColumnHidden(DiffView.CHANGES_COLUMN)
    assert view.table.isColumnHidden(DiffView.AUTHOR_COLUMN) and view.table.isColumnHidden(DiffView.TIME_COLUMN)
    view = DiffView(sample_diff())
    assert not any(view.table.isColumnHidden(column) for column in range(len(DiffView.COLUMNS)))


def test_view_default_sort_puts_payment_next_to_its_event(qapp):
    diff = DbDiff({"event": TableDiff(added=[event_row(1, receiver="Б"), event_row(2, receiver="А")]),
                   "payment": TableDiff(added=[payment_row(10, 1, title="Б — Аренда"), payment_row(11, 2, title="А — Аренда")])})
    view = DiffView(diff)
    rows = [(view.proxy.index(row, 1).data(), view.proxy.index(row, 2).data()) for row in range(view.proxy.rowCount())]
    assert rows == [("Платеж", "А — Аренда"), ("Оплата", "А — Аренда"), ("Платеж", "Б — Аренда"), ("Оплата", "Б — Аренда")]


def test_filters_by_action_table_and_text(qapp):
    view = DiffView(many_events_diff())
    assert view.proxy.rowCount() == 14 and view.lbl_status.text().startswith("Показано 14 из 14")
    view.action_boxes[REMOVED].setChecked(False)
    assert view.proxy.rowCount() == 13
    view.cmb_table.setCurrentIndex(view.cmb_table.findData("payment"))
    assert view.proxy.rowCount() == 1
    view.cmb_table.setCurrentIndex(0)
    view.edt_search.setText("получатель 07")
    assert view.proxy.rowCount() == 1 and view.lbl_status.text().startswith("Показано 1 из 14")
    view.edt_search.clear()
    view.action_boxes[ADDED].setChecked(False)
    assert view.proxy.rowCount() == 0


def test_filters_hidden_for_short_lists(qapp):
    view = DiffView(sample_diff())
    assert not view.action_boxes and view.cmb_table is None and view.edt_search is None


def test_double_click_emits_event_only_when_openable(qapp):
    opened: list[int] = []
    view = DiffView(many_events_diff(), openable=True)
    view.eventActivated.connect(opened.append)
    view.edt_search.setText("получатель 03")
    view.activate_index(view.proxy.index(0, 2))
    view.edt_search.setText("удалённый")
    view.activate_index(view.proxy.index(0, 2))
    assert opened == [3]
    closed_view = DiffView(many_events_diff())
    closed_view.eventActivated.connect(opened.append)
    closed_view.activate_index(closed_view.proxy.index(0, 2))
    assert opened == [3]


def test_dialog_remembers_event_and_geometry(qapp, tmp_path):
    from PySide6.QtCore import QSettings
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    dialog = SyncChangesDialog("m", [("Чужие", sample_diff()), ("Мои", sample_diff())], settings=settings, openable_tabs=("Чужие",))
    tabs = dialog.findChild(QTabWidget)
    assert [view.openable for view in (tabs.widget(0), tabs.widget(1))] == [True, False]
    dialog.show()
    dialog.resize(799, 520)
    dialog.request_event(5)
    assert dialog.event_to_show == 5 and dialog.result() == dialog.DialogCode.Accepted
    reopened = SyncChangesDialog("m", [("Чужие", sample_diff())], settings=settings)
    assert reopened.height() == 520
