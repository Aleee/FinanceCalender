import random
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QItemSelectionModel, QPersistentModelIndex, Qt

from base.liability import Col, HeaderFooterSubtype, PaymentType, RowType, TermCategory
from base.liabilitystore import LiabilityStore
from gui.eventsqlmodel import RowFormatting
from gui.eventwidget import EventWidget
from gui.liabilitytablemodel import LiabilityTableModel
from tests.test_liabilitystore import fill_rich_db
from tests.test_readpath import DB_VALUE, QT_VALUE, add_event, add_payment, day, db_file, models, open_models, run_sql

PERSONAL = {1: ("Иванов",), 2: ("Петров",)}
CELL_ROLES = (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, DB_VALUE, QT_VALUE,
              LiabilityTableModel.decimalValueRole)


class Pair:

    def __init__(self, models):
        self.models = models
        models.base.personal_dict = PERSONAL
        self.table = LiabilityTableModel(LiabilityStore(models.base.db_handler), models.base)
        self.table.set_header_filter(True)
        self.table.set_footer_filter(True)
        self.args: dict = {}
        self.apply()

    def apply(self, term=TermCategory.UNPAID, category=0, search="", responsible=0, paid_today=False,
              featured=False, months=3) -> None:
        self.args = dict(term=term, category=category, search=search, responsible=responsible, paid_today=paid_today,
                         featured=featured, months=months)
        self.models.apply(**self.args)
        self.table.set_filters(term, category, search, responsible, paid_today, months, featured)


@pytest.fixture
def rich(db_file, open_models):
    fill_rich_db(db_file)
    run_sql(db_file, "UPDATE event SET contractdocument_id = 5 WHERE id % 9 = 0 AND type = 2")
    return Pair(open_models(db_file))


def style_tuple(style) -> tuple:
    def color(value):
        return None if value is None else value.name()

    brush = None if style.background_brush is None else style.background_brush.color().name()
    return (color(style.text_color), color(style.highlighted_text_color), color(style.highlight_color), brush,
            color(style.vertical_grid_color), style.font_bold)


def font_bold(value):
    return None if value is None else value.bold()


def assert_cells_equal_chain(pair: Pair, label=None) -> int:
    chain, table = pair.models.proxy2, pair.table
    assert table.rowCount() == chain.rowCount(), label
    assert table.columnCount() == chain.columnCount() == len(Col)
    assert table.stored_count == chain.stored_count
    base = pair.models.base
    for row in range(chain.rowCount()):
        for column in range(len(Col)):
            expected, actual = chain.index(row, column), table.index(row, column)
            for role in CELL_ROLES:
                assert actual.data(role) == expected.data(role), (label, row, column, role)
            assert font_bold(actual.data(Qt.ItemDataRole.FontRole)) == font_bold(expected.data(Qt.ItemDataRole.FontRole)), (label, row, column)
            assert style_tuple(actual.data(LiabilityTableModel.styleRole)) == style_tuple(expected.data(LiabilityTableModel.styleRole)), (label, row, column)
            tooltip = expected.data(Qt.ItemDataRole.ToolTipRole)
            assert actual.data(Qt.ItemDataRole.ToolTipRole) == tooltip, (label, row, column)
            decoration = expected.data(Qt.ItemDataRole.DecorationRole)
            if decoration is None:
                assert actual.data(Qt.ItemDataRole.DecorationRole) is None
            else:
                assert actual.data(Qt.ItemDataRole.DecorationRole).cacheKey() == decoration.cacheKey()
            for flag in (Qt.ItemFlag.ItemIsEnabled, Qt.ItemFlag.ItemIsSelectable):
                assert bool(table.flags(actual) & flag) == bool(chain.flags(expected) & flag), (label, row, column)
    return chain.rowCount()


def test_cells_match_chain_for_filters_and_formatting(rich):
    rnd = random.Random(5)
    checked = 0
    formattings = (RowFormatting(), RowFormatting(due_textbold=True, today_textbold=False, header_textbold=True, footer_textbold=True,
                                                  due_backcolor="#ffeeee", today_backcolor="#eeffee"))
    for formatting in formattings:
        rich.models.base.set_row_formatting(formatting)
        for term in TermCategory:
            rich.apply(term)
            checked += assert_cells_equal_chain(rich, term)
        for _ in range(25):
            rich.apply(rnd.choice(list(TermCategory)), category=rnd.choice((0, 1000, 1101, 1103, 2100)),
                       search=rnd.choice(("", "", "ромашка", "аренда 1")), responsible=rnd.choice((0, 1, 2)),
                       paid_today=rnd.random() < 0.3, featured=rnd.random() < 0.3, months=rnd.choice((3, 12)))
            checked += assert_cells_equal_chain(rich, rich.args)
    assert checked > 300


def test_headers_and_header_rows(rich):
    table = rich.table
    positions = table.header_rows()
    assert positions and all(table.index(row, Col.TYPE).data(DB_VALUE) == RowType.HEADER for row in positions)
    assert positions == [row for row in range(table.rowCount()) if table.index(row, Col.TYPE).data(DB_VALUE) == RowType.HEADER]
    chain = rich.models.proxy2
    for column in range(len(Col)):
        for role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.TextAlignmentRole):
            assert table.headerData(column, Qt.Orientation.Horizontal, role) == chain.headerData(column, Qt.Orientation.Horizontal, role)


def test_map_to_source_and_back(rich):
    table, base = rich.table, rich.models.base
    for row in range(table.rowCount()):
        index = table.index(row, Col.NAME)
        source = table.mapToSource(index)
        assert source.model() is base and source.column() == Col.NAME
        assert base.index(source.row(), Col.ID).data(DB_VALUE) == index.siblingAtColumn(Col.ID).data(DB_VALUE)
        assert table.mapFromSource(source) == index
    hidden_by_filter = [event_id for event_id in rich.table.store.events if rich.table.store.position_of(event_id) is None]
    assert hidden_by_filter
    source_row = table.source_row(hidden_by_filter[0])
    assert source_row is not None
    assert not table.mapFromSource(base.index(source_row, 0)).isValid()


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


def test_set_data_writes_through_base_model_and_refreshes(db_file, open_models):
    event_id = add_event(db_file, category=1101, featured=0, hidden=0)
    other = add_event(db_file, category=1101, featured=1)
    pair = Pair(open_models(db_file))
    table = pair.table
    index = table.index_by_id(event_id, Col.FEATURED)
    assert index.data(Qt.ItemDataRole.EditRole) == 0

    assert table.setData(index, 1)
    con = sqlite3.connect(db_file)
    try:
        assert con.execute("SELECT featured FROM event WHERE id = ?", (event_id,)).fetchone()[0] == 1
    finally:
        con.close()
    assert table.index_by_id(event_id, Col.FEATURED).data(Qt.ItemDataRole.EditRole) == 1
    assert table.index_by_id(other, Col.FEATURED).data(Qt.ItemDataRole.EditRole) == 1

    assert not table.setData(table.index_by_id(event_id, Col.REMAINAMOUNT), "5")
    assert table.setData(table.index_by_id(event_id, Col.NOTES), "заметка  ")
    assert table.index_by_id(event_id, Col.NOTES).data(DB_VALUE) == "заметка"


def test_set_data_that_changes_filter_membership_moves_row_out(db_file, open_models):
    event_id = add_event(db_file, category=1101, featured=0)
    keep = add_event(db_file, category=1101, featured=1)
    pair = Pair(open_models(db_file))
    pair.apply(featured=True)
    assert [row.event_id for row in pair.table.store.visible_rows() if row.row_type == RowType.LIABILITY] == [keep]
    assert pair.table.setData(pair.table.index_by_id(keep, Col.FEATURED), 0)
    pair.table.set_filters(TermCategory.UNPAID, 0, "", 0, False, 3, True)
    assert pair.table.rowCount() == 0
    assert pair.table.stored_count == 0


def test_select_of_base_model_resets_table_with_new_rows(db_file, open_models):
    add_event(db_file, category=1101)
    pair = Pair(open_models(db_file))
    resets: list[str] = []
    pair.table.modelReset.connect(lambda: resets.append("reset"))
    new_id = add_event(db_file, category=1102, total="77.00")
    run_sql(db_file, "UPDATE event SET hidden = 1 WHERE category = 1101")
    assert pair.table.index_by_id(new_id).isValid() is False

    pair.models.base.select()
    assert resets == ["reset"]
    assert pair.table.index_by_id(new_id, Col.TOTALAMOUNT).data(QT_VALUE) == Decimal("77.00")
    assert pair.table.stored_count == 2


def test_insert_edit_and_delete_through_base_model_update_table(db_file, open_models):
    existing = add_event(db_file, category=1101, total="100.00")
    pair = Pair(open_models(db_file))
    table, base = pair.table, pair.models.base

    data = ["ООО Ромашка", 0, int(RowType.LIABILITY), 0, 1102, 0, "name", "250.00", 0, day(5), day(0),
            int(PaymentType.NORMAL), "descr", "1", "", 0, 0]
    assert base.insert_row(data) is not None
    new_id = base.last_inserted_id
    index = table.index_by_id(new_id, Col.REMAINAMOUNT)
    assert index.isValid() and index.data(QT_VALUE) == Decimal("250.00")
    assert table.stored_count == 2

    data = ["ИП Иванов", existing, int(RowType.LIABILITY), 0, 1101, 0, "changed", "300.00", 0, day(7), day(0),
            int(PaymentType.NORMAL), "descr", "2", "", 0, 0]
    assert base.edit_row(table.mapToSource(table.index_by_id(existing)).row(), data) is not None
    assert table.index_by_id(existing, Col.RECEIVER).data(Qt.ItemDataRole.DisplayRole) == "ИП Иванов"
    assert table.index_by_id(existing, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal("300.00")

    assert base.delete_row(table.mapToSource(table.index_by_id(new_id)).row()) == new_id
    assert not table.index_by_id(new_id).isValid()
    assert table.stored_count == 1


def test_payment_totals_are_applied_after_load_payment_totals_and_relayout(db_file, open_models):
    event_id = add_event(db_file, category=1101, total="500.00", due=day(-1))
    pair = Pair(open_models(db_file))
    table = pair.table
    assert table.index_by_id(event_id, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal("500.00")
    add_payment(db_file, event_id, day(0), "500.00")
    table.load_payment_totals()
    table.set_filters(TermCategory.UNPAID, 0, "", 0, False, 3, False)
    assert table.index_by_id(event_id, Col.REMAINAMOUNT).data(QT_VALUE) == Decimal(0)
    assert table.index_by_id(event_id, Col.TODAYSHARE).data(QT_VALUE) == Decimal("500.00")


def test_flags_make_only_liability_rows_selectable(db_file, open_models):
    liability = add_event(db_file)
    service = {row_type: add_event(db_file, row_type=row_type, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
               for row_type in (RowType.HEADER, RowType.FOOTER, RowType.FINALFOOTER)}
    pair = Pair(open_models(db_file))
    table = pair.table
    assert table.flags(table.index(-1, 0)) == Qt.ItemFlag.NoItemFlags
    for event_id, row_type in [(liability, RowType.LIABILITY)] + [(event_id, row_type) for row_type, event_id in service.items()]:
        for column in range(len(Col)):
            flags = table.flags(table.index_by_id(event_id, column))
            assert bool(flags & Qt.ItemFlag.ItemIsSelectable) == (row_type == RowType.LIABILITY), (row_type, column)
            assert flags & Qt.ItemFlag.ItemIsEnabled


def test_table_reading_does_not_write(db_file, open_models):
    fill_rich_db(db_file)
    pair = Pair(open_models(db_file))
    monitor = sqlite3.connect(db_file)
    try:
        version_before = monitor.execute("PRAGMA data_version").fetchone()[0]
        content_before = list(monitor.iterdump())
        for term in TermCategory:
            pair.apply(term)
            for row in range(pair.table.rowCount()):
                for column in range(len(Col)):
                    for role in CELL_ROLES + (Qt.ItemDataRole.FontRole, LiabilityTableModel.styleRole):
                        pair.table.index(row, column).data(role)
        pair.models.base.select()
        pair.table.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
        assert monitor.execute("PRAGMA data_version").fetchone()[0] == version_before
        assert list(monitor.iterdump()) == content_before
    finally:
        monitor.close()
