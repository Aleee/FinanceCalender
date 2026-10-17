from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont

from base.date import date_displstr, str_date
from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, Col, FilterFlags, HeaderFooterSubtype, PAYMENTTYPE_NAMES, RowType,
                            TermCategory)
from base.liabilitystore import DERIVED_COLUMNS, LiabilityStore, STORED_INDEX, VisibleRow
from gui.commonwidgets.common import RowStyle
from gui.eventsqlmodel import LiabilitySqlTableModel


class LiabilityTableModel(QAbstractTableModel):

    dbValueRole = Qt.ItemDataRole.UserRole + 1
    qtValueRole = Qt.ItemDataRole.UserRole + 2
    decimalValueRole = Qt.ItemDataRole.UserRole + 4
    styleRole = Qt.ItemDataRole.UserRole + 20

    COLUMN_DATA = LiabilitySqlTableModel.COLUMN_DATA
    DECIMAL_COLUMNS = LiabilitySqlTableModel.DECIMAL_COLUMNS
    NON_LIABILITY_VALUES = LiabilitySqlTableModel.NON_LIABILITY_VALUES
    TOTAL_COLUMNS = (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)
    INT_COLUMNS = (Col.ID, Col.TYPE, Col.CONTRACTDOCUMENTID, Col.CATEGORY, Col.SUBCATEGORY, Col.PAYMENTTYPE, Col.NDS,
                   Col.FEATURED, Col.RESPONSIBLE)

    VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    DARKER_RATIO: int = 110

    def __init__(self, store: LiabilityStore, base_model: LiabilitySqlTableModel, parent=None):
        super().__init__(parent)

        self.store = store
        self.base_model = base_model
        self.rows: list[VisibleRow] = []
        self.stored_count: int = 0
        self.style_cache: dict[int, RowStyle] = {}
        self.fonts: dict[bool, QFont] = {}
        self.source_rows: dict[int, int] | None = None

        self.load_store()
        base_model.modelReset.connect(self.reload)
        base_model.cacheUpdateNeeded.connect(self.reload_layout)
        for signal in (base_model.modelReset, base_model.rowsInserted, base_model.rowsRemoved, base_model.cacheUpdateNeeded):
            signal.connect(self.invalidate_source_rows)

    def load_store(self) -> None:
        if self.base_model.paid_load_months is not None:
            self.store.set_paid_load_months(self.base_model.paid_load_months)
        self.store.reload()
        self.take_rows()

    def take_rows(self) -> None:
        self.rows = self.store.visible_rows()
        self.stored_count = self.store.totals().count
        self.style_cache.clear()

    def invalidate_source_rows(self, *_) -> None:
        self.source_rows = None

    def reload(self) -> None:
        self.beginResetModel()
        self.load_store()
        self.endResetModel()

    def change_layout(self, change: Callable[[], None]) -> None:
        self.layoutAboutToBeChanged.emit()
        old_rows = self.rows
        persistent_indexes = self.persistentIndexList()
        old_positions = [(old_rows[index.row()].event_id, index.column()) for index in persistent_indexes]
        change()
        self.take_rows()
        self.changePersistentIndexList(persistent_indexes,
                                       [self.index_by_id(event_id, column) for event_id, column in old_positions])
        self.layoutChanged.emit()

    def reload_layout(self) -> None:
        self.change_layout(self.load_store)

    def load_payment_totals(self) -> None:
        self.store.load_payment_totals()

    def set_filters(self, term: TermCategory, category: int, search: str, responsible: int, paid_today: bool,
                    paid_months_toshow: int, featured: bool) -> None:
        self.change_layout(lambda: self.store.set_filters(term, category, search, responsible, paid_today,
                                                          paid_months_toshow, featured))

    def set_hidden_filter(self, exclude_hidden: bool) -> None:
        self.change_layout(lambda: self.store.set_hidden_filter(exclude_hidden))

    def set_header_filter(self, show: bool) -> None:
        self.change_layout(lambda: self.store.set_header_filter(show))

    def set_footer_filter(self, show: bool) -> None:
        self.change_layout(lambda: self.store.set_footer_filter(show))

    def set_sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.change_layout(lambda: self.store.set_sort(column, order))

    def filter_counters(self) -> tuple[dict[int, int], dict[int, int]]:
        return self.store.filter_counters()

    def header_rows(self) -> list[int]:
        return [position for position, row in enumerate(self.rows) if row.row_type == RowType.HEADER]

    def index_by_id(self, event_id: int, column: int = 0) -> QModelIndex:
        position = self.store.position_of(event_id)
        return QModelIndex() if position is None else self.index(position, column)

    def source_row(self, event_id: int) -> int | None:
        if self.source_rows is None:
            self.source_rows = {self.base_model.raw_value(row, Col.ID): row for row in range(self.base_model.rowCount())}
        return self.source_rows.get(event_id)

    def sourceModel(self) -> LiabilitySqlTableModel:
        return self.base_model

    def mapToSource(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        source_row = self.source_row(self.rows[index.row()].event_id)
        return QModelIndex() if source_row is None else self.base_model.index(source_row, index.column())

    def mapFromSource(self, source_index: QModelIndex) -> QModelIndex:
        if not source_index.isValid():
            return QModelIndex()
        return self.index_by_id(self.base_model.raw_value(source_index.row(), Col.ID), source_index.column())

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(Col)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.COLUMN_DATA[section][0]
            elif role == Qt.ItemDataRole.ToolTipRole:
                return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignHCenter
        return super().headerData(section, orientation, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        if self.rows[index.row()].row_type == RowType.LIABILITY:
            flags |= Qt.ItemFlag.ItemIsSelectable
        return flags

    def setData(self, index, value, /, role=Qt.ItemDataRole.EditRole) -> bool:
        source_index = self.mapToSource(index)
        if not source_index.isValid() or not self.base_model.setData(source_index, value, role):
            return False
        self.reload_layout()
        return True

    def data(self, index, /, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self.rows):
            return None
        row = self.rows[index.row()]
        column = index.column()

        if role == self.dbValueRole:
            return self.db_value(row, column)

        elif role == self.qtValueRole:
            return self.qt_value(row, column)

        elif role == Qt.ItemDataRole.DisplayRole:
            return self.display_value(row, column)

        elif role == Qt.ItemDataRole.FontRole:
            if row.row_type in (RowType.FOOTER, RowType.FINALFOOTER) and column in self.TOTAL_COLUMNS:
                return self.font(True)
            font_bold = self.row_style(row).font_bold
            return None if font_bold is None else self.font(font_bold)

        elif role == self.styleRole:
            return self.row_style(row)

        elif role == self.decimalValueRole:
            if row.row_type in (RowType.FOOTER, RowType.FINALFOOTER) and column in self.TOTAL_COLUMNS:
                return {Col.TOTALAMOUNT: row.total, Col.REMAINAMOUNT: row.remain, Col.TODAYSHARE: row.today_share}[column]

        elif role in (Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.ToolTipRole) and column == Col.DESCR:
            if row.row_type != RowType.LIABILITY:
                return None
            document_id: int = self.qt_value(row, Col.CONTRACTDOCUMENTID)
            if role == Qt.ItemDataRole.DecorationRole:
                return self.base_model.contract_icon if document_id else self.base_model.empty_icon
            return self.base_model.document_tooltip(document_id) if document_id else None

        elif role == Qt.ItemDataRole.EditRole:
            return self.stored_value(row, column)

        return None

    def font(self, bold: bool) -> QFont:
        font = self.fonts.get(bold)
        if font is None:
            font = QFont()
            font.setBold(bold)
            self.fonts[bold] = font
        return font

    def stored_value(self, row: VisibleRow, column: int) -> Any:
        if column in DERIVED_COLUMNS:
            return None
        return self.store.event_values(row.event_id)[STORED_INDEX[column]]

    def db_value(self, row: VisibleRow, column: int) -> Any:
        if column not in DERIVED_COLUMNS:
            return self.stored_value(row, column)
        if row.row_type != RowType.LIABILITY:
            return self.NON_LIABILITY_VALUES.get(column)
        liability = self.store.row_by_id(row.event_id)
        if liability is None:
            return None
        if column == Col.REMAINAMOUNT:
            return str(liability.remain)
        if column == Col.TODAYSHARE:
            return str(liability.today_share)
        if column == Col.LASTPAYMENTDATE:
            return liability.last_payment_date
        return int(liability.filter_flags)

    def qt_value(self, row: VisibleRow, column: int) -> Any:
        db_value = self.db_value(row, column)
        try:
            if column in self.DECIMAL_COLUMNS:
                try:
                    return Decimal(db_value)
                except (InvalidOperation, TypeError):
                    return Decimal(0)
            elif column in self.INT_COLUMNS:
                return int(db_value)
            elif column in (Col.DUEDATE, Col.INCURRENCEDATE):
                return str_date(db_value)
            elif column == Col.FILTERFLAGS:
                return FilterFlags(db_value)
            else:
                return db_value
        except (ValueError, TypeError):
            return None

    @staticmethod
    def money_text(value: Decimal) -> str:
        return "" if value == Decimal(0) else dec_strcommaspace(value)

    def display_value(self, row: VisibleRow, column: int) -> Any:
        row_type = row.row_type
        if row_type == RowType.FOOTER:
            if column == Col.RECEIVER:
                return f"Всего по {CATEGORY_NAMES[row.category][:5]}"
            if column in self.TOTAL_COLUMNS:
                return self.money_text({Col.TOTALAMOUNT: row.total, Col.REMAINAMOUNT: row.remain,
                                        Col.TODAYSHARE: row.today_share}[column])
            return ""
        elif row_type == RowType.FINALFOOTER:
            if column in self.TOTAL_COLUMNS:
                return self.money_text({Col.TOTALAMOUNT: row.total, Col.REMAINAMOUNT: row.remain,
                                        Col.TODAYSHARE: row.today_share}[column])
            if column != Col.RECEIVER:
                return ""
        elif row_type == RowType.HEADER and column != Col.RECEIVER:
            return ""

        if row_type == RowType.LIABILITY:
            if column == Col.PAYMENTTYPE:
                return PAYMENTTYPE_NAMES[self.db_value(row, column)]
            elif column in (Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE):
                return dec_strcommaspace(self.qt_value(row, column))
            elif column in (Col.DUEDATE, Col.INCURRENCEDATE):
                return date_displstr(self.qt_value(row, column))
            elif column == Col.RESPONSIBLE:
                try:
                    return self.base_model.personal_dict[self.qt_value(row, column)][0]
                except KeyError:
                    return "Н/Д"
        return self.stored_value(row, column)

    def row_style(self, row: VisibleRow) -> RowStyle:
        style = self.style_cache.get(row.event_id)
        if style is None:
            style = self.compute_style(row)
            self.style_cache[row.event_id] = style
        return style

    def compute_style(self, row: VisibleRow) -> RowStyle:
        row_formatting = self.base_model.row_formatting
        style = RowStyle(vertical_grid_color=self.VERTICAL_GRID_COLOR)

        if row.row_type == RowType.LIABILITY:
            style.highlight_color = QColor("#CDE8FF")
            filter_flags: FilterFlags = self.store.row_by_id(row.event_id).filter_flags
            due_fore = QColor(row_formatting.due_forecolor)
            today_fore = QColor(row_formatting.today_forecolor)
            due_back = QColor(row_formatting.due_backcolor)
            today_back = QColor(row_formatting.today_backcolor)
            due_condition = (
                    FilterFlags.DUE in filter_flags
                    and self.store.term_filter != TermCategory.DUE
                    and not self.store.paytoday_filter)
            today_condition = (
                    FilterFlags.TODAY in filter_flags
                    and self.store.term_filter != TermCategory.TODAY
                    and not self.store.paytoday_filter)
            if due_condition:
                style.text_color = due_fore
                style.highlighted_text_color = due_fore
                style.background_brush = QBrush(due_back)
                style.vertical_grid_color = due_back.darker(self.DARKER_RATIO)
                style.font_bold = row_formatting.due_textbold
            elif today_condition:
                style.text_color = today_fore
                style.highlighted_text_color = today_fore
                style.background_brush = QBrush(today_back)
                style.vertical_grid_color = today_back.darker(self.DARKER_RATIO)
                style.font_bold = row_formatting.today_textbold
            else:
                style.highlighted_text_color = QColor("black")
                style.background_brush = QBrush(QColor("#FFFFFF"))

        elif row.row_type == RowType.HEADER:
            if row.subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.header_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_section_backcolor))
            elif row.subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.header_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_subsection_backcolor))
            style.font_bold = row_formatting.header_textbold

        elif row.row_type == RowType.FOOTER:
            if row.subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.footer_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_section_backcolor))
            elif row.subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.footer_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_subsection_backcolor))
            style.font_bold = row_formatting.footer_textbold

        elif row.row_type == RowType.FINALFOOTER:
            style.background_brush = QBrush(self.FINALFOOTER_BACK_COLOR)
            style.font_bold = True

        return style
