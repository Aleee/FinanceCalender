import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QEvent

import base.edition as edition
from base.payment import PaymentEntry
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.matchingdialog import SAVED_FILES_LIMIT, MatchingDialog
from tests.conftest import FakeSettingsHandler

SETTINGS = {"CSVparser/columnstoparse": "0,2,5,8,7,9,6", "CSVparser/rowperiod": "1",
            "CSVparser/rowtransactionstart": "9", "CSVparser/knownunp": "", "CSVparser/patterns": "",
            "CSVparser/nomatchpatterns": ""}

STATEMENT_ROWS = [(5, "750,00", "ИП Петров", "ЗА РЕМОНТ"), (6, "99,99", "ООО Гамма", "КАНЦТОВАРЫ"),
                  (6, "200,00", "ООО Омега", "УСЛУГИ")]
CALENDAR_ROWS = [(3, "750.00", "Сервис-Принт", "Оргтехника"), (7, "450.00", "ЧУП Дельта", "Уборка"),
                 (6, "200.00", "ООО Омега", "Услуги")]


def write_statement(path: Path, rows=STATEMENT_ROWS) -> Path:
    lines = [[""] * 10 for _ in range(8)]
    lines[0][0] = "ВЫПИСКА ПО СЧЕТУ С 01.10.2026 ПО 10.10.2026"
    for number, (day, debit, receiver, descr) in enumerate(rows):
        lines.append([f"{day:02d}.10.2026", str(number), "1", "", "", "100", receiver, debit, "0,00", descr])
    path.write_text("\n".join(";".join(row) for row in lines) + "\n", encoding="windows-1251")
    return path


def fake_db(calendar_rows=CALENDAR_ROWS):
    calendar: dict[date, list[PaymentEntry]] = {}
    for number, (day, amount, receiver, name) in enumerate(calendar_rows):
        calendar.setdefault(date(2026, 10, day), []).append(
            PaymentEntry(Decimal(amount), f"{name} ({receiver})", receiver, number, number, name, key=f"c|{number}"))
    return SimpleNamespace(get_setting=lambda key, default="": SETTINGS.get(key, default),
                           get_paymentsum_for_period=lambda start, end: calendar)


class Calls:
    def __init__(self):
        self.created: list[tuple] = []
        self.edited: list[tuple] = []


@pytest.fixture
def errors(monkeypatch) -> list[str]:
    shown: list[str] = []
    monkeypatch.setattr(ErrorInfoMessageBox, "exec", lambda self: shown.append(self.text()) or 0)
    return shown


@pytest.fixture
def statement(tmp_path) -> Path:
    return write_statement(tmp_path / "statement.csv")


@pytest.fixture
def settings_handler(tmp_path) -> FakeSettingsHandler:
    return FakeSettingsHandler(tmp_path / "settings.ini")


@pytest.fixture
def make_dialog(qapp, settings_handler):
    opened = []
    calls = Calls()

    def factory(handler=None):
        dialog = MatchingDialog(handler or settings_handler, fake_db(),
                                lambda amount, fee_date, parent: calls.created.append((amount, fee_date)) or True,
                                lambda entry, amount, parent: calls.edited.append((entry, amount)) or True,
                                lambda path, totals, parent: None)
        opened.append(dialog)
        return dialog

    factory.calls = calls
    yield factory
    for dialog in opened:
        dialog.close()
    qapp.processEvents()
    for dialog in opened:
        dialog.deleteLater()
    qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def saved_state(handler) -> dict:
    return json.loads(handler.settings.value("Matching/state"))


def select_rows(table, *rows):
    table.clearSelection()
    for row in rows:
        table.selectRow(row)


def row_amounts(table) -> list[str]:
    return [table.item(row, 1).text() for row in range(table.rowCount())]


def test_load_csv_fills_lists_and_enables_buttons(make_dialog, statement):
    dialog = make_dialog()
    assert not dialog.ui.pb_refresh.isEnabled()
    dialog.load_csv(str(statement))
    assert dialog.ui.pb_refresh.isEnabled()
    assert dialog.ui.tw_statement.rowCount() == 2
    assert dialog.ui.tw_calendar.rowCount() == 2
    assert not dialog.ui.pb_link.isEnabled()


def test_broken_file_reports_error_and_keeps_previous_result(make_dialog, statement, tmp_path, errors):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    result, path = dialog.match_result, dialog.csv_path
    broken = tmp_path / "broken.csv"
    broken.write_bytes(b"not;a;statement\n")
    dialog.load_csv(str(broken))
    assert len(errors) == 1
    assert dialog.match_result is result and dialog.csv_path == path
    dialog.load_csv(str(tmp_path / "missing.csv"))
    assert len(errors) == 2
    assert dialog.csv_path == path


def test_hide_selected_removes_entries_and_is_remembered_for_the_file(make_dialog, statement, settings_handler):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    select_rows(dialog.ui.tw_calendar, 0)
    dialog.hide_selected()
    assert dialog.ui.tw_statement.rowCount() == 1
    assert dialog.ui.tw_calendar.rowCount() == 1
    assert dialog.ui.tw_hidden.rowCount() == 2
    assert len(saved_state(settings_handler)[dialog.csv_hash]["hidden"]) == 2

    other = make_dialog()
    other.load_csv(str(statement))
    assert other.ui.tw_statement.rowCount() == 1
    assert other.ui.tw_calendar.rowCount() == 1


def test_marks_of_other_statement_do_not_affect_this_one(make_dialog, statement, tmp_path):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    dialog.hide_selected()
    changed = write_statement(tmp_path / "other.csv", STATEMENT_ROWS + [(8, "5,00", "ООО Бета", "ПРОЧЕЕ")])
    other = make_dialog()
    other.load_csv(str(changed))
    assert other.ui.tw_hidden.rowCount() == 0
    assert other.ui.tw_statement.rowCount() == 3


def test_restore_selected_and_restore_all(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0, 1)
    dialog.hide_selected()
    assert dialog.ui.tw_statement.rowCount() == 0
    assert dialog.ui.pb_restoreall.isEnabled()
    select_rows(dialog.ui.tw_hidden, 0)
    dialog.restore_selected()
    assert dialog.ui.tw_statement.rowCount() == 1
    dialog.restore_hidden()
    assert dialog.ui.tw_statement.rowCount() == 2
    assert not dialog.ui.pb_restoreall.isEnabled()


def test_link_with_equal_sums_does_not_ask(make_dialog, statement, monkeypatch, settings_handler):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    monkeypatch.setattr(dialog, "ask_link_with_difference", lambda *args: pytest.fail("asked"))
    select_rows(dialog.ui.tw_statement, 0)
    select_rows(dialog.ui.tw_calendar, 0)
    assert dialog.ui.pb_link.isEnabled()
    dialog.link_selected()
    assert dialog.ui.tw_linked.rowCount() == 1
    assert dialog.ui.tw_statement.rowCount() == 1
    assert dialog.ui.tw_calendar.rowCount() == 1
    assert len(saved_state(settings_handler)[dialog.csv_hash]["links"]) == 1


def test_link_cancelled_when_sums_differ(make_dialog, statement, monkeypatch):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    monkeypatch.setattr(dialog, "ask_link_with_difference", lambda *args: None)
    select_rows(dialog.ui.tw_statement, 1)
    select_rows(dialog.ui.tw_calendar, 1)
    dialog.link_selected()
    assert dialog.ui.tw_linked.rowCount() == 0
    assert dialog.ui.tw_statement.rowCount() == 2
    assert make_dialog.calls.edited == []


def test_link_with_difference_without_correction_keeps_amounts(make_dialog, statement, monkeypatch):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    asked = []
    monkeypatch.setattr(dialog, "ask_link_with_difference",
                        lambda statement_sum, calendar_sum, can_correct: asked.append(
                            (statement_sum, calendar_sum, can_correct)) or "link")
    select_rows(dialog.ui.tw_statement, 1)
    select_rows(dialog.ui.tw_calendar, 1)
    dialog.link_selected()
    assert asked == [(Decimal("99.99"), Decimal("450.00"), True)]
    assert dialog.ui.tw_linked.rowCount() == 1
    assert make_dialog.calls.edited == []


def test_link_with_correction_edits_calendar_payment_first(make_dialog, statement, monkeypatch):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    monkeypatch.setattr(dialog, "ask_link_with_difference", lambda *args: "correct")
    select_rows(dialog.ui.tw_statement, 1)
    select_rows(dialog.ui.tw_calendar, 1)
    dialog.link_selected()
    assert [amount for entry, amount in make_dialog.calls.edited] == [Decimal("99.99")]
    assert dialog.ui.tw_linked.rowCount() == 1


def test_link_with_correction_declined_in_edit_dialog_does_not_link(make_dialog, statement, monkeypatch):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    dialog.edit_event = lambda entry, amount, parent: False
    monkeypatch.setattr(dialog, "ask_link_with_difference", lambda *args: "correct")
    select_rows(dialog.ui.tw_statement, 1)
    select_rows(dialog.ui.tw_calendar, 1)
    dialog.link_selected()
    assert dialog.ui.tw_linked.rowCount() == 0


def test_link_needs_both_lists(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    dialog.link_selected()
    assert dialog.ui.tw_linked.rowCount() == 0
    assert not dialog.ui.pb_link.isEnabled()


def test_unlink_returns_entries_to_lists(make_dialog, statement, settings_handler):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    select_rows(dialog.ui.tw_calendar, 0)
    dialog.link_selected()
    select_rows(dialog.ui.tw_linked, 0)
    assert dialog.ui.pb_unlink.isEnabled()
    dialog.unlink_selected()
    assert dialog.ui.tw_linked.rowCount() == 0
    assert dialog.ui.tw_statement.rowCount() == 2
    assert dialog.ui.tw_calendar.rowCount() == 2
    assert saved_state(settings_handler)[dialog.csv_hash]["links"] == []


def test_create_from_statement_passes_amount_and_date_and_refreshes(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    assert dialog.ui.pb_create.isEnabled()
    before = dialog.refreshed_at
    dialog.create_selected()
    assert make_dialog.calls.created == [(Decimal("750.00"), date(2026, 10, 5))]
    assert dialog.refreshed_at >= before


def test_create_is_unavailable_with_calendar_selection(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0)
    select_rows(dialog.ui.tw_calendar, 0)
    assert not dialog.ui.pb_create.isEnabled()


def test_open_selected_edits_calendar_payment(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_calendar, 0)
    assert dialog.ui.pb_open.isEnabled()
    dialog.open_selected()
    assert len(make_dialog.calls.edited) == 1
    assert make_dialog.calls.edited[0][1] is None


def test_search_hides_rows_and_deselects_them(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    select_rows(dialog.ui.tw_statement, 0, 1)
    dialog.ui.le_searchstatement.setText("99,99")
    visible = [row for row in range(2) if not dialog.ui.tw_statement.isRowHidden(row)]
    assert len(visible) == 1
    selected = dialog.selected_entries(dialog.ui.tw_statement)
    assert [e.amount for e in selected] == [Decimal("99.99")]
    dialog.hide_selected()
    assert dialog.ui.tw_statement.rowCount() == 1
    assert dialog.ui.tw_hidden.rowCount() == 1


def test_selection_summary_shows_counts_and_difference(make_dialog, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    assert dialog.ui.la_selection.text() == ""
    select_rows(dialog.ui.tw_statement, 0)
    select_rows(dialog.ui.tw_calendar, 0)
    text = dialog.ui.la_selection.text()
    assert "в выписке <b>1</b>" in text and "в календаре <b>1</b>" in text


def test_marks_keep_only_last_files(make_dialog, settings_handler, tmp_path):
    dialog = make_dialog()
    for number in range(SAVED_FILES_LIMIT + 3):
        path = write_statement(tmp_path / f"s{number}.csv", STATEMENT_ROWS + [(8, f"{number + 1},00", "ООО", "ПРОЧЕЕ")])
        dialog.load_csv(str(path))
        dialog.hide_keys(("k",))
    state = saved_state(settings_handler)
    assert len(state) == SAVED_FILES_LIMIT
    assert dialog.csv_hash in state


def test_resaving_same_file_moves_it_to_the_end(make_dialog, settings_handler, tmp_path):
    dialog = make_dialog()
    first = write_statement(tmp_path / "a.csv")
    second = write_statement(tmp_path / "b.csv", STATEMENT_ROWS[:2])
    dialog.load_csv(str(first))
    dialog.hide_keys(("k",))
    first_hash = dialog.csv_hash
    dialog.load_csv(str(second))
    dialog.hide_keys(("k",))
    dialog.load_csv(str(first))
    dialog.hide_keys(("k2",))
    assert list(saved_state(settings_handler))[-1] == first_hash


@pytest.mark.parametrize("value", ["not json", "[1, 2]", '{"x": 5}'])
def test_damaged_saved_marks_are_ignored(make_dialog, settings_handler, statement, value):
    settings_handler.settings.setValue("Matching/state", value)
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    assert dialog.ui.tw_statement.rowCount() == 2
    dialog.hide_keys(("k",))
    assert dialog.csv_hash in saved_state(settings_handler)


def test_reject_proposal_is_saved(make_dialog, statement, settings_handler):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    dialog.reject_proposal("pair-key")
    assert saved_state(settings_handler)[dialog.csv_hash]["rejected"] == ["pair-key"]


def test_viewer_mode_hides_create_and_cannot_correct(make_dialog, statement, monkeypatch):
    edition.set_viewer(True)
    try:
        dialog = make_dialog()
        assert dialog.ui.pb_create.isHidden()
        dialog.load_csv(str(statement))
        asked = []
        monkeypatch.setattr(dialog, "ask_link_with_difference",
                            lambda statement_sum, calendar_sum, can_correct: asked.append(can_correct) or None)
        select_rows(dialog.ui.tw_statement, 1)
        select_rows(dialog.ui.tw_calendar, 1)
        dialog.link_selected()
        assert asked == [False]
        assert make_dialog.calls.edited == []
    finally:
        edition.set_viewer(False)


def test_closing_saves_layout(make_dialog, settings_handler, statement):
    dialog = make_dialog()
    dialog.load_csv(str(statement))
    dialog.show()
    dialog.close()
    assert settings_handler.settings.value("Matching/geometry") is not None
