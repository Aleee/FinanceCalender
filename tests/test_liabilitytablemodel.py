import sqlite3
from decimal import Decimal

import pytest
from PySide6.QtCore import QItemSelectionModel, QPersistentModelIndex, Qt

from base.liability import Col, FilterFlags, HeaderFooterSubtype, PaymentType, RowType, TermCategory
from gui.eventwidget import EventWidget
from gui.liabilitytablemodel import LiabilityTableModel, RowFormatting
from tests.test_liabilitystore import fill_rich_db
from tests.test_readpath import DB_VALUE, QT_VALUE, add_event, add_payment, day, db_file, models, open_models, run_sql

PERSONAL = {1: ("Иванов",), 2: ("Петров",)}
DISPLAY = Qt.ItemDataRole.DisplayRole
EDIT = Qt.ItemDataRole.EditRole
STYLE = LiabilityTableModel.styleRole
DECIMAL = LiabilityTableModel.decimalValueRole


def cell(models, event_id: int, column: int, role=DISPLAY):
    return models.table.index_by_id(event_id, column).data(role)


@pytest.fixture
def rich(db_file, open_models):
    fill_rich_db(db_file)
    run_sql(db_file, "UPDATE event SET contractdocument_id = 5 WHERE id % 9 = 0 AND type = 2")
    models = open_models(db_file)
    models.table.personal_dict = PERSONAL
    return models


def make_kinds(path) -> dict[str, int]:
    ids = {
        "liability": add_event(path, category=1101, total="1234.5", due=day(-3), receiver="ООО Ромашка", responsible="2"),
        "header": add_event(path, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY),
        "footer": add_event(path, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY),
        "final": add_event(path, row_type=RowType.FINALFOOTER, category=None, total=None),
    }
    add_payment(path, ids["liability"], day(0), "200.50")
    run_sql(path, "UPDATE event SET name = 'Аренда', descr = 'Договор 1', createdate = ?, nds = 20, notes = 'заметка' WHERE id = ?",
            day(-10), ids["liability"])
    run_sql(path, "UPDATE event SET receiver = 'Раздел 1.1' WHERE id = ?", ids["header"])
    return ids


def test_liability_cells_in_every_role(db_file, open_models):
    ids = make_kinds(db_file)
    models = open_models(db_file)
    models.table.personal_dict = PERSONAL
    event_id = ids["liability"]
    due, created = models.table.index_by_id(event_id, Col.DUEDATE), models.table.index_by_id(event_id, Col.INCURRENCEDATE)

    assert [cell(models, event_id, column) for column in (Col.RECEIVER, Col.NAME, Col.DESCR)] == ["ООО Ромашка", "Аренда", "Договор 1"]
    assert cell(models, event_id, Col.REMAINAMOUNT) == "1 034,00"
    assert cell(models, event_id, Col.TOTALAMOUNT) == "1 234,50"
    assert cell(models, event_id, Col.TODAYSHARE) == "200,50"
    assert cell(models, event_id, Col.PAYMENTTYPE) == "По факту"
    assert cell(models, event_id, Col.RESPONSIBLE) == "Петров"
    assert due.data(DISPLAY) == models.table.index_by_id(event_id, Col.DUEDATE).data(DISPLAY)
    assert due.data(QT_VALUE).toString("yyyy-MM-dd") == day(-3)
    assert created.data(QT_VALUE).toString("yyyy-MM-dd") == day(-10)
    assert cell(models, event_id, Col.REMAINAMOUNT, QT_VALUE) == Decimal("1034.00")
    assert cell(models, event_id, Col.REMAINAMOUNT, DB_VALUE) == "1034.0"
    assert cell(models, event_id, Col.TODAYSHARE, QT_VALUE) == Decimal("200.50")
    assert cell(models, event_id, Col.LASTPAYMENTDATE, DB_VALUE) == day(0)
    assert cell(models, event_id, Col.FILTERFLAGS, QT_VALUE) & FilterFlags.DUE
    assert cell(models, event_id, Col.FILTERFLAGS, DB_VALUE) == int(cell(models, event_id, Col.FILTERFLAGS, QT_VALUE))
    assert cell(models, event_id, Col.NDS, QT_VALUE) == 20
    assert cell(models, event_id, Col.NOTES, DB_VALUE) == "заметка"
    assert cell(models, event_id, Col.CATEGORY, QT_VALUE) == 1101
    assert cell(models, event_id, Col.RESPONSIBLE, QT_VALUE) == 2
    assert cell(models, event_id, Col.FEATURED, EDIT) == 0
    assert cell(models, event_id, Col.TOTALAMOUNT, EDIT) == "1234.5"
    assert cell(models, event_id, Col.REMAINAMOUNT, EDIT) is None
    assert cell(models, event_id, Col.TOTALAMOUNT, DECIMAL) is None
    assert cell(models, event_id, Col.NAME, Qt.ItemDataRole.ToolTipRole) is None
    assert cell(models, event_id, Col.NAME, Qt.ItemDataRole.TextAlignmentRole) is None


def test_unknown_responsible_is_shown_as_not_available(db_file, open_models):
    ids = make_kinds(db_file)
    models = open_models(db_file)
    models.table.personal_dict = {7: ("Кто-то",)}
    assert cell(models, ids["liability"], Col.RESPONSIBLE) == "Н/Д"


def test_service_rows_cells(db_file, open_models):
    ids = make_kinds(db_file)
    models = open_models(db_file)
    models.table.personal_dict = PERSONAL

    assert cell(models, ids["header"], Col.RECEIVER) == "Раздел 1.1"
    assert all(cell(models, ids["header"], column) == "" for column in range(len(Col)) if column != Col.RECEIVER)

    assert cell(models, ids["footer"], Col.RECEIVER) == "Всего по 1.1. "
    assert cell(models, ids["footer"], Col.TOTALAMOUNT) == "1 234,50"
    assert cell(models, ids["footer"], Col.REMAINAMOUNT) == "1 034,00"
    assert cell(models, ids["footer"], Col.TODAYSHARE) == "200,50"
    assert cell(models, ids["footer"], Col.NAME) == ""
    assert [cell(models, ids["footer"], column, DECIMAL) for column in (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)] == \
           [Decimal("1234.50"), Decimal("1034.00"), Decimal("200.50")]

    assert [cell(models, ids["final"], column, DECIMAL) for column in (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)] == \
           [Decimal("1234.50"), Decimal("1034.00"), Decimal("200.50")]
    assert cell(models, ids["final"], Col.TOTALAMOUNT) == "1 234,50"
    assert cell(models, ids["final"], Col.NAME) == ""

    for key in ("header", "footer", "final"):
        assert cell(models, ids[key], Col.FILTERFLAGS, QT_VALUE) == FilterFlags.NONE
        assert cell(models, ids[key], Col.LASTPAYMENTDATE, DB_VALUE) == ""
        assert cell(models, ids[key], Col.TODAYSHARE, DB_VALUE) == "0.0"


def test_empty_totals_are_shown_as_blank(db_file, open_models):
    add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    paid = add_event(db_file, category=1101, total="10.00")
    add_payment(db_file, paid, day(-1), "10.00")
    models = open_models(db_file)
    models.apply(TermCategory.PAID)
    table = models.table
    footer_row = next(row for row in table.rows if row.row_type == RowType.FOOTER)
    assert cell(models, footer_row.event_id, Col.TOTALAMOUNT) == "10,00"
    assert cell(models, footer_row.event_id, Col.REMAINAMOUNT) == ""
    assert cell(models, footer_row.event_id, Col.TODAYSHARE) == ""


def test_row_styles_follow_formatting_and_filters(db_file, open_models):
    due = add_event(db_file, category=1101, due=day(-1))
    today = add_event(db_file, category=1101, due=day(0))
    future = add_event(db_file, category=1101, due=day(10))
    top_header = add_event(db_file, row_type=RowType.HEADER, category=1000, total=None, subcategory=HeaderFooterSubtype.TOPLEVELNOEVENTS)
    sub_header = add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    top_footer = add_event(db_file, row_type=RowType.FOOTER, category=1000, total=None, subcategory=HeaderFooterSubtype.TOPLEVELNOEVENTS)
    sub_footer = add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    final = add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    models = open_models(db_file)
    formatting = RowFormatting(due_textbold=True, due_forecolor="#112233", due_backcolor="#ffeeee",
                               today_forecolor="#445566", today_backcolor="#eeffee",
                               header_section_forecolor="#010101", header_section_backcolor="#020202",
                               header_subsection_backcolor="#030303", footer_section_backcolor="#040404",
                               footer_subsection_backcolor="#050505")
    assert models.table.set_row_formatting(formatting)
    models.apply()

    def style(event_id: int):
        return cell(models, event_id, Col.NAME, STYLE)

    assert style(due).text_color.name() == "#112233" and style(due).background_brush.color().name() == "#ffeeee"
    assert style(due).font_bold is True
    assert style(today).text_color.name() == "#445566" and style(today).font_bold is True
    assert style(future).background_brush.color().name() == "#ffffff" and style(future).font_bold is None
    assert style(future).highlight_color.name() == "#cde8ff"
    assert style(top_header).text_color.name() == "#010101" and style(top_header).background_brush.color().name() == "#020202"
    assert style(sub_header).background_brush.color().name() == "#030303"
    assert style(top_footer).background_brush.color().name() == "#040404"
    assert style(sub_footer).background_brush.color().name() == "#050505"
    assert style(final).background_brush.color().name() == LiabilityTableModel.FINALFOOTER_BACK_COLOR.name()
    assert style(final).font_bold is True

    models.apply(TermCategory.DUE)
    assert style(due).font_bold is None and style(due).text_color is None
    models.apply(TermCategory.UNPAID, paid_today=True)
    assert models.table.rowCount() == 0

    assert not models.table.set_row_formatting(RowFormatting(due_forecolor=None))
    assert models.table.row_formatting is formatting


def test_contract_marker_and_tooltip(db_file, open_models):
    bound = add_event(db_file, category=1101)
    unbound = add_event(db_file, category=1101)
    missing = add_event(db_file, category=1101)
    con = sqlite3.connect(db_file)
    try:
        con.execute("INSERT INTO contractor (id, name) VALUES (1, 'ООО Поставщик')")
        con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '15/А', '2026-02-03')")
        con.execute("INSERT INTO contractdocument (id, contract_id, document_type, document_name) VALUES (1, 1, 1, 'Счет №7')")
        con.execute("UPDATE event SET contractdocument_id = 1 WHERE id = ?", (bound,))
        con.execute("UPDATE event SET contractdocument_id = 99 WHERE id = ?", (missing,))
        con.commit()
    finally:
        con.close()
    models = open_models(db_file)
    table = models.table

    assert table.index_by_id(bound, Col.DESCR).data(Qt.ItemDataRole.DecorationRole).cacheKey() == table.contract_icon.cacheKey()
    assert table.index_by_id(unbound, Col.DESCR).data(Qt.ItemDataRole.DecorationRole).cacheKey() == table.empty_icon.cacheKey()
    assert table.index_by_id(bound, Col.DESCR).data(Qt.ItemDataRole.ToolTipRole) == \
           "Договор № 15/А от 03.02.2026\nКонтрагент: ООО Поставщик\nДокумент: Счет №7"
    assert table.index_by_id(unbound, Col.DESCR).data(Qt.ItemDataRole.ToolTipRole) is None
    assert "данные договора не найдены" in table.index_by_id(missing, Col.DESCR).data(Qt.ItemDataRole.ToolTipRole)
    assert table.index_by_id(bound, Col.NAME).data(Qt.ItemDataRole.DecorationRole) is None
    assert table.document_title(1).document_name == "Счет №7"
    table.document_titles.clear()
    assert table.document_title(99) is None


def test_headers_and_header_rows(rich):
    table = rich.table
    positions = table.header_rows()
    assert positions and all(table.index(row, Col.TYPE).data(DB_VALUE) == RowType.HEADER for row in positions)
    assert positions == [row for row in range(table.rowCount()) if table.index(row, Col.TYPE).data(DB_VALUE) == RowType.HEADER]
    assert table.headerData(Col.RECEIVER, Qt.Orientation.Horizontal, DISPLAY) == "Получатель платежа"
    assert table.headerData(Col.ID, Qt.Orientation.Horizontal, DISPLAY) == ""
    assert table.headerData(Col.TODAYSHARE, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole) == ""
    assert table.headerData(Col.NAME, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole) == Qt.AlignmentFlag.AlignHCenter
    assert table.columnCount() == len(Col) == len(table.COLUMN_DATA)
    assert table.rowCount(table.index(0, 0)) == 0


def test_layout_change_keeps_persistent_index_of_surviving_row(rich):
    table = rich.table
    target = next(row for row in table.store.visible_rows() if row.row_type == RowType.LIABILITY)
    persistent = QPersistentModelIndex(table.index_by_id(target.event_id, Col.NAME))
    signals: list[str] = []
    table.layoutAboutToBeChanged.connect(lambda *_: signals.append("about"))
    table.layoutChanged.connect(lambda *_: signals.append("changed"))

    table.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
    assert signals == ["about", "changed"]
    assert persistent.isValid() and persistent.row() == table.store.position_of(target.event_id)
    assert table.index(persistent.row(), Col.ID).data(DB_VALUE) == target.event_id
    assert persistent.column() == Col.NAME

    table.set_filters(TermCategory.PAID, 0, "", 0, False, 3, False)
    if table.store.position_of(target.event_id) is None:
        assert not persistent.isValid()
    else:
        assert table.index(persistent.row(), Col.ID).data(DB_VALUE) == target.event_id


def test_view_selection_survives_filter_change_if_row_stays_visible(rich):
    view = EventWidget()
    table = rich.table
    view.setModel(table)
    target = next(row for row in table.store.visible_rows() if row.row_type == RowType.LIABILITY and row.category == 1101)
    index = table.index_by_id(target.event_id)
    view.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)

    table.set_filters(TermCategory.UNPAID, 1101, "", 0, False, 3, False)
    assert view.currentIndex().isValid()
    assert view.currentIndex().siblingAtColumn(Col.ID).data(DB_VALUE) == target.event_id
    assert view.selectionModel().selectedRows()[0].siblingAtColumn(Col.ID).data(DB_VALUE) == target.event_id

    table.set_filters(TermCategory.UNPAID, 1102, "", 0, False, 3, False)
    assert not view.currentIndex().isValid()


def test_save_and_restore_selection_around_reload(rich, qapp):
    view = EventWidget()
    table = rich.table
    view.setModel(table)
    target = next(row for row in table.store.visible_rows() if row.row_type == RowType.LIABILITY)
    view.selectionModel().setCurrentIndex(table.index_by_id(target.event_id),
                                          QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
    table.beforeReload.connect(view.save_selection)
    table.afterReload.connect(view.restore_selection)

    table.reload()
    assert not view.currentIndex().isValid()
    for _ in range(3):
        qapp.processEvents()
    assert view.currentIndex().siblingAtColumn(Col.ID).data(DB_VALUE) == target.event_id


def test_reload_emits_signals_and_resets(db_file, open_models, qapp):
    add_event(db_file, category=1101)
    models = open_models(db_file)
    events: list[str] = []
    models.table.beforeReload.connect(lambda: events.append("before"))
    models.table.afterReload.connect(lambda: events.append("after"))
    models.table.modelAboutToBeReset.connect(lambda: events.append("about"))
    models.table.modelReset.connect(lambda: events.append("reset"))
    models.table.reload()
    assert events == ["before", "about", "reset"]
    qapp.processEvents()
    assert events[-1] == "after"


def test_set_data_writes_to_database_and_refreshes(db_file, open_models):
    event_id = add_event(db_file, category=1101, featured=0, hidden=0)
    other = add_event(db_file, category=1101, featured=1)
    models = open_models(db_file)
    table = models.table
    index = table.index_by_id(event_id, Col.FEATURED)
    assert index.data(EDIT) == 0

    assert table.setData(index, 1)
    con = sqlite3.connect(db_file)
    try:
        assert con.execute("SELECT featured FROM event WHERE id = ?", (event_id,)).fetchone()[0] == 1
    finally:
        con.close()
    assert table.index_by_id(event_id, Col.FEATURED).data(EDIT) == 1
    assert table.index_by_id(other, Col.FEATURED).data(EDIT) == 1

    assert not table.setData(table.index_by_id(event_id, Col.REMAINAMOUNT), "5")
    assert not table.setData(table.index_by_id(event_id, Col.ID), 77)
    assert not table.setData(table.index_by_id(event_id, Col.NOTES), "x", Qt.ItemDataRole.DisplayRole)
    assert not table.setData(table.index(-1, 0), "x")
    assert table.setData(table.index_by_id(event_id, Col.NOTES), "заметка  ")
    assert table.index_by_id(event_id, Col.NOTES).data(DB_VALUE) == "заметка"


def test_set_data_that_changes_filter_membership_moves_row_out(db_file, open_models):
    event_id = add_event(db_file, category=1101, featured=0)
    keep = add_event(db_file, category=1101, featured=1)
    models = open_models(db_file)
    models.apply(featured=True)
    assert models.visible() == [keep]
    assert models.table.setData(models.table.index_by_id(keep, Col.FEATURED), 0)
    assert models.table.rowCount() == 0
    assert models.table.stored_count == 0
    assert event_id not in models.visible()


def test_reload_picks_up_external_changes(db_file, open_models):
    add_event(db_file, category=1101)
    models = open_models(db_file)
    new_id = add_event(db_file, category=1102, total="77.00")
    assert not models.table.index_by_id(new_id).isValid()
    models.table.reload()
    models.apply()
    assert models.table.index_by_id(new_id, Col.TOTALAMOUNT).data(QT_VALUE) == Decimal("77.00")
    assert models.table.stored_count == 2


def test_insert_edit_and_delete_update_table(db_file, open_models):
    existing = add_event(db_file, category=1101, total="100.00")
    models = open_models(db_file)
    table = models.table
    layouts: list[str] = []
    table.layoutChanged.connect(lambda *_: layouts.append("layout"))

    data = ["ООО Ромашка", 0, int(RowType.LIABILITY), 0, 1102, 0, "name", "250.00", 0, day(5), day(0),
            int(PaymentType.NORMAL), "descr", "1", "", 0, 0]
    new_id = table.insert_event(data)
    assert new_id is not None and table.last_inserted_id == new_id
    index = table.index_by_id(new_id, Col.REMAINAMOUNT)
    assert index.isValid() and index.data(QT_VALUE) == Decimal("250.00")
    assert table.stored_count == 2
    assert len(layouts) == 1

    data = ["ИП Иванов", existing, int(RowType.LIABILITY), 0, 1101, 0, "changed", "300.00", 0, day(7), day(0),
            int(PaymentType.NORMAL), "descr", "2", "", 0, 0]
    assert table.edit_event(existing, data)
    assert table.index_by_id(existing, Col.RECEIVER).data(DISPLAY) == "ИП Иванов"
    assert table.index_by_id(existing, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal("300.00")

    assert table.delete_event(new_id)
    assert not table.index_by_id(new_id).isValid()
    assert table.stored_count == 1
    assert not table.delete_event(new_id)
    assert not table.edit_event(new_id, data)


def test_edit_that_makes_row_paid_moves_it_between_terms(db_file, open_models):
    event_id = add_event(db_file, category=1101, total="100.00", due=day(-1))
    add_payment(db_file, event_id, day(-1), "100.00")
    models = open_models(db_file)
    assert models.visible() == []
    data = list(models.store.event_values(event_id))
    data[7] = "500.00"
    assert models.table.edit_event(event_id, data)
    assert models.visible() == [event_id]
    assert models.table.index_by_id(event_id, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal("400.00")


def test_payment_totals_are_applied_after_load_payment_totals_and_relayout(db_file, open_models):
    event_id = add_event(db_file, category=1101, total="500.00", due=day(-1))
    models = open_models(db_file)
    table = models.table
    assert table.index_by_id(event_id, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal("500.00")
    add_payment(db_file, event_id, day(0), "500.00")
    table.load_payment_totals()
    table.set_filters(TermCategory.UNPAID, 0, "", 0, False, 3, False)
    assert table.index_by_id(event_id, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal(0)
    assert table.index_by_id(event_id, Col.TODAYSHARE).data(QT_VALUE) == Decimal("500.00")


def test_set_sort_through_model(db_file, open_models):
    first = add_event(db_file, category=1101, total="30.00", due=day(1))
    second = add_event(db_file, category=1101, total="10.00", due=day(2))
    models = open_models(db_file)

    def order() -> list[int]:
        return [models.table.index(row, Col.ID).data(DB_VALUE) for row in range(models.table.rowCount())
                if models.table.index(row, Col.ID).data(DB_VALUE) in (first, second)]

    assert order() == [first, second]
    models.table.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.AscendingOrder)
    assert order() == [second, first]
    models.table.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
    assert order() == [first, second]


def test_table_reading_does_not_write(rich):
    monitor = sqlite3.connect(rich.path)
    try:
        version_before = monitor.execute("PRAGMA data_version").fetchone()[0]
        content_before = list(monitor.iterdump())
        for term in TermCategory:
            rich.apply(term)
            for row in range(rich.table.rowCount()):
                for column in range(len(Col)):
                    for role in (DISPLAY, EDIT, DB_VALUE, QT_VALUE, DECIMAL, STYLE, Qt.ItemDataRole.FontRole,
                                 Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.ToolTipRole):
                        rich.table.index(row, column).data(role)
        rich.table.reload()
        rich.table.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
        assert monitor.execute("PRAGMA data_version").fetchone()[0] == version_before
        assert list(monitor.iterdump()) == content_before
    finally:
        monitor.close()
