from dataclasses import astuple, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QDate, QModelIndex, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPixmap

from base.contract import DocumentTitle
from base.date import date_displstr, str_date
from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, Col, DERIVED_COLUMNS, EVENT_COLUMN_NAMES, FilterFlags, HeaderFooterSubtype,
                            PAYMENTTYPE_NAMES, PeriodField, RowType, STORED_INDEX, TermCategory)
from base.liabilitystore import LiabilityStore, VisibleRow
from gui.commonwidgets.common import RowStyle


@dataclass()
class RowFormatting:
    due_textbold: bool = False
    today_textbold: bool = True
    due_forecolor: str = "#aa0000"
    today_forecolor: str = "black"
    due_backcolor: str = "white"
    today_backcolor: str = "white"

    header_textbold: bool = False
    header_section_forecolor: str = "black"
    header_section_backcolor: str = "#ccdce3"
    header_subsection_forecolor: str = "black"
    header_subsection_backcolor: str = "#e4e0d9"

    footer_textbold: bool = False
    footer_section_forecolor: str = "black"
    footer_section_backcolor: str = "#decbc9"
    footer_subsection_forecolor: str = "black"
    footer_subsection_backcolor: str = "#e9dcdb"

    vertical_grid: bool = True


class LiabilityTableModel(QAbstractTableModel):

    beforeReload = Signal()
    afterReload = Signal()

    # 0 = заголовок, #1 = видимость
    COLUMN_DATA = {
        Col.RECEIVER: ("Получатель платежа", True),
        Col.ID: ("", False),
        Col.TYPE: ("", False),
        Col.CONTRACTDOCUMENTID: ("", False),
        Col.CATEGORY: ("Категория", False),
        Col.SUBCATEGORY: ("", False),
        Col.NAME: ("Наименование (предмет) платежа", True),
        Col.REMAINAMOUNT: ("Остаток платежа", True),
        Col.TOTALAMOUNT: ("Сумма платежа", True),
        Col.NDS: ("", False),
        Col.DUEDATE: ("Срок оплаты", True),
        Col.INCURRENCEDATE: ("Дата возникновения", True),
        Col.PAYMENTTYPE: ("Вид платежа", True),
        Col.DESCR: ("Основание платежа", True),
        Col.RESPONSIBLE: ("Ответственный", True),
        Col.NOTES: ("", False),
        Col.TODAYSHARE: ("Оплата сегодня", True),
        Col.LASTPAYMENTDATE: ("Последняя оплата", False),
        Col.FILTERFLAGS: ("", False),
        Col.FEATURED: ("", True),
        Col.HIDDEN: ("", True),
    }

    DECIMAL_COLUMNS = [
        Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE
    ]

    NON_LIABILITY_VALUES = {Col.TODAYSHARE: "0.0", Col.LASTPAYMENTDATE: "", Col.FILTERFLAGS: int(FilterFlags.NONE)}
    TOTAL_COLUMNS = (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)
    INT_COLUMNS = (Col.ID, Col.TYPE, Col.CONTRACTDOCUMENTID, Col.CATEGORY, Col.SUBCATEGORY, Col.PAYMENTTYPE, Col.NDS,
                   Col.FEATURED, Col.RESPONSIBLE)

    ICON_SIZE = 16

    dbValueRole = Qt.ItemDataRole.UserRole + 1
    qtValueRole = Qt.ItemDataRole.UserRole + 2
    decimalValueRole = Qt.ItemDataRole.UserRole + 4
    styleRole = Qt.ItemDataRole.UserRole + 20

    VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    DARKER_RATIO: int = 110

    def __init__(self, store: LiabilityStore, paid_load_months: int | None = None, parent=None):
        super().__init__(parent)

        self.store = store
        self.db_handler = store.db_handler
        self.paid_load_months: int | None = paid_load_months
        self.rows: list[VisibleRow] = []
        self.stored_count: int = 0
        self.style_cache: dict[int, RowStyle] = {}
        self.fonts: dict[bool, QFont] = {}
        self._personal_dict: dict = {}
        self.paid_mode: bool = False
        self.document_titles: dict[int, DocumentTitle] = {}
        self.last_inserted_id: int = 0
        self.contract_icon = QIcon(":/icon-table/designer/icons/attachment.svg")
        self.monthly_icon = QIcon(":/icon-table/designer/icons/attachment_monthly.svg")
        empty_pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        empty_pixmap.fill(Qt.GlobalColor.transparent)
        self.empty_icon = QIcon(empty_pixmap)
        # temp
        self.row_formatting = RowFormatting()

        self.load_store()

    @property
    def personal_dict(self) -> dict:
        return self._personal_dict

    @personal_dict.setter
    def personal_dict(self, value: dict) -> None:
        self._personal_dict = value
        self.store.responsible_names = {person_id: person[0] for person_id, person in value.items()}

    @property
    def current_date(self) -> QDate:
        return self.store.current_date

    def load_store(self) -> None:
        self.document_titles.clear()
        if self.paid_load_months is not None:
            self.store.set_paid_load_months(self.paid_load_months)
        self.store.reload()
        self.take_rows()

    def take_rows(self) -> None:
        self.rows = self.store.visible_rows()
        self.stored_count = self.store.totals().count
        self.style_cache.clear()

    def reload(self) -> None:
        self.beforeReload.emit()
        self.beginResetModel()
        self.load_store()
        self.endResetModel()
        QTimer.singleShot(0, self, self.afterReload.emit)

    def set_paid_load_months(self, months: int) -> None:
        if months == self.paid_load_months:
            return
        self.paid_load_months = months
        self.reload()

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

    def load_payment_totals(self) -> None:
        self.store.load_payment_totals()

    def refresh_event(self, event_id: int) -> None:
        self.change_layout(lambda: self.store.refresh_event(event_id))

    def set_filters(self, term: TermCategory, category: int, search: str, responsible: int, paid_today: bool,
                    paid_months_toshow: int, featured: bool, date_from: QDate | None = None,
                    date_to: QDate | None = None, period_field: PeriodField = PeriodField.DUEDATE) -> None:
        def apply_filters() -> None:
            self.store.set_filters(term, category, search, responsible, paid_today, paid_months_toshow, featured,
                                   date_from, date_to, period_field)
            paid_mode = term == TermCategory.PAID
            if paid_mode != self.paid_mode:
                self.paid_mode = paid_mode
                self.store.set_sort(Col.LASTPAYMENTDATE if paid_mode else Col.DUEDATE, self.store.sort_order)

        self.change_layout(apply_filters)

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

    def insert_event(self, data: list) -> int | None:
        event_id = self.db_handler.insert_event(data)
        if event_id is None:
            return None
        self.last_inserted_id = event_id
        self.change_layout(lambda: self.store.refresh_event(event_id))
        return event_id

    def edit_event(self, event_id: int, data: list) -> bool:
        if not self.db_handler.update_event(event_id, data):
            self.reload()
            return False
        self.change_layout(lambda: self.store.refresh_event(event_id))
        return True

    def delete_event(self, event_id: int) -> bool:
        if not self.db_handler.delete_event(event_id):
            return False
        self.change_layout(lambda: self.store.remove_event(event_id))
        return True

    def restore_event(self, event: tuple, payments: list[tuple]) -> bool:
        if not self.db_handler.restore_event(event, payments):
            return False
        event_id = event[EVENT_COLUMN_NAMES.index("id")]
        self.last_inserted_id = event_id
        self.change_layout(lambda: self.store.refresh_event(event_id))
        return True

    def document_title(self, document_id: int) -> DocumentTitle | None:
        if not self.document_titles:
            self.document_titles = self.db_handler.load_document_titles() or {}
        return self.document_titles.get(document_id)

    def document_tooltip(self, document_id: int) -> str:
        title = self.document_title(document_id)
        if title is None:
            return "Платеж привязан к договору (данные договора не найдены)"
        lines = [f"Договор № {title.contract_number} от {date_displstr(title.contract_date)}"]
        if title.contractor_name:
            lines.append(f"Контрагент: {title.contractor_name}")
        if title.document_name:
            lines.append(f"Документ: {title.document_name}")
        if title.monthly:
            lines.append("Ежемесячный платеж")
        return "\n".join(lines)

    def set_row_formatting(self, row_formatting: RowFormatting) -> bool:
        for var in astuple(row_formatting):
            if var is None:
                return False
        self.row_formatting = row_formatting
        self.style_cache.clear()
        return True

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
        if not index.isValid() or role != Qt.ItemDataRole.EditRole or index.column() in (*DERIVED_COLUMNS, Col.ID):
            return False
        event_id = self.rows[index.row()].event_id
        if not self.db_handler.update_event_field(event_id, EVENT_COLUMN_NAMES[STORED_INDEX[index.column()]], value):
            return False
        self.change_layout(lambda: self.store.refresh_event(event_id))
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
                if not document_id:
                    return self.empty_icon
                title = self.document_title(document_id)
                return self.monthly_icon if title is not None and title.monthly else self.contract_icon
            return self.document_tooltip(document_id) if document_id else None

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
            elif column == Col.LASTPAYMENTDATE:
                return date_displstr(str_date(self.db_value(row, column)))
            elif column == Col.RESPONSIBLE:
                try:
                    return self.personal_dict[self.qt_value(row, column)][0]
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
        row_formatting = self.row_formatting
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
