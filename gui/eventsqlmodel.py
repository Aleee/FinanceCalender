import decimal
from dataclasses import dataclass, astuple
from decimal import Decimal
from enum import IntEnum
from typing import Any

import lovely_logger as log

from PySide6.QtCore import Qt, QModelIndex, Signal, QDate, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSql import QSqlTableModel

from base.contract import DocumentTitle
from base.date import date_displstr, str_date
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, FilterFlags, RowType, HeaderFooterSubtype, TermCategory, LiabilityRow,
                             PAYMENTTYPE_NAMES, calculate_filterflags, paid_threshold, matches_term, matches_category,
                             matches_details)


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


class Col(IntEnum):
    RECEIVER = 0
    ID = 1
    TYPE = 2
    CONTRACTDOCUMENTID = 3
    CATEGORY = 4
    SUBCATEGORY = 5
    NAME = 6
    REMAINAMOUNT = 7
    TOTALAMOUNT = 8
    NDS = 9
    DUEDATE = 10
    INCURRENCEDATE = 11
    PAYMENTTYPE = 12
    DESCR = 13
    RESPONSIBLE = 14
    NOTES = 15
    TODAYSHARE = 16
    LASTPAYMENTDATE = 17
    FILTERFLAGS = 18
    FEATURED = 19
    HIDDEN = 20
    RECEIVERNOCASE = 21


class LiabilitySqlTableModel(QSqlTableModel):

    beforeSelect = Signal()
    afterSelect = Signal()
    filterwidget_labels_changed = Signal(object, object)

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
        Col.DUEDATE: ("Дата платежа", True),
        Col.INCURRENCEDATE: ("Дата появления", True),
        Col.PAYMENTTYPE: ("Вид платежа", True),
        Col.DESCR: ("Основание платежа", True),
        Col.RESPONSIBLE: ("Ответственное лицо", True),
        Col.NOTES: ("", False),
        Col.TODAYSHARE: ("Оплата сегодня", True),
        Col.LASTPAYMENTDATE: ("", False),
        Col.FILTERFLAGS: ("", False),
        Col.FEATURED: ("", True),
        Col.HIDDEN: ("", True),
        Col.RECEIVERNOCASE: ("", False),
    }

    DECIMAL_COLUMNS = [
        Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE
    ]

    DERIVED_COLUMNS = (Col.REMAINAMOUNT, Col.TODAYSHARE, Col.LASTPAYMENTDATE, Col.FILTERFLAGS)
    NON_LIABILITY_VALUES = {Col.TODAYSHARE: "0.0", Col.LASTPAYMENTDATE: "", Col.FILTERFLAGS: int(FilterFlags.NONE)}
    NO_PAYMENTS = (Decimal(0), Decimal(0), "")

    ICON_SIZE = 16

    dbValueRole = Qt.ItemDataRole.UserRole + 1
    qtValueRole = Qt.ItemDataRole.UserRole + 2
    sortRole = Qt.ItemDataRole.UserRole + 10

    afterRowRemoval = Signal()
    cacheUpdateNeeded = Signal()


    def __init__(self, db_handler: DBHandler, parent=None):
        super(LiabilitySqlTableModel, self).__init__(parent)

        self.db_handler = db_handler
        self.table_columns: dict[int, int] = {column: column - sum(1 for derived in self.DERIVED_COLUMNS if derived < column)
                                              for column in Col}
        self.current_date: QDate = QDate().currentDate()
        self.paid_load_months: int | None = None
        self.payment_totals: dict[int, tuple[Decimal, Decimal, str]] = {}
        self.liability_cache: dict[int, LiabilityRow] | None = None
        self.event_cache: dict[int, tuple] | None = None
        self.header_cache: list[int] | None = None
        self.personal_dict: dict = {}
        self.document_titles: dict[int, DocumentTitle] = {}
        self.contract_icon = QIcon(":/icon-table/designer/icons/attachment.svg")
        empty_pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        empty_pixmap.fill(Qt.GlobalColor.transparent)
        self.empty_icon = QIcon(empty_pixmap)
        # temp
        self.row_formatting = RowFormatting()

        for key, val in self.COLUMN_DATA.items():
            self.setHeaderData(key, Qt.Orientation.Horizontal, val)

        self.sort_cache = {}
        self.row_sort_keys: dict[int, tuple] = {}

        self.modelReset.connect(self.invalidate_liability_cache)
        self.dataChanged.connect(self.invalidate_liability_cache)
        self.rowsInserted.connect(self.extend_liability_cache)
        self.rowsRemoved.connect(self.invalidate_liability_cache)

    def sort_key(self, row):
        key = self.row_sort_keys.get(row)
        if key is None:
            entry_id = self.raw_value(row, Col.ID)
            key = self.sort_cache.get(entry_id)
            if key is None:
                key = self.compute_sort_key(row)
                self.sort_cache[entry_id] = key
            self.row_sort_keys[row] = key
        return key

    def invalidate_sort_cache(self):
        self.sort_cache.clear()
        self.row_sort_keys.clear()

    def compute_sort_key(self, row: int):
        idx = self.index(row, Col.TYPE)
        if not idx.isValid():
            return (99, 0, 0, 0, 0)
        row_type: RowType = self.data(idx, self.qtValueRole)

        if row_type == RowType.FINALFOOTER:
            return (98, 0, 0, 0, 0)

        category: int = self.data(self.index(row, Col.CATEGORY), self.qtValueRole)
        subtype: HeaderFooterSubtype = self.data(self.index(row, Col.SUBCATEGORY), self.qtValueRole)
        due_date: QDate = self.data(self.index(row, Col.DUEDATE), self.qtValueRole)

        if category is None:
            return (99, 0, 0, 0, 0)

        # 1) раздел
        division = category // 1000
        # 2) является ли футером раздела
        division_footer = 1 if row_type == RowType.FOOTER and subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS else 0
        # 3) категория
        category_group = category if category else 0
        # 4) тип в категории
        type_order = int(row_type)
        # 5) дата
        if due_date:
            date_key = due_date.toJulianDay()
        else:
            date_key = 0

        return (division,
                division_footer,
                category_group,
                type_order,
                date_key)

    def data(self, idx, /, role=...):
        if not idx.isValid() and not role == self.sortRole:
            return None

        if role == self.dbValueRole:
            if idx.column() in self.DERIVED_COLUMNS:
                return self.derived_db_value(idx)
            return self.stored_data(idx, Qt.ItemDataRole.DisplayRole)

        elif role == self.qtValueRole:
            try:
                if idx.column() in (Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE):
                    try:
                        return Decimal(self.data(idx, self.dbValueRole))
                    except (decimal.InvalidOperation, TypeError):
                        return Decimal(0)
                elif idx.column() in (Col.ID, Col.TYPE, Col.CONTRACTDOCUMENTID, Col.CATEGORY, Col.SUBCATEGORY, Col.PAYMENTTYPE, Col.NDS, Col.FEATURED, Col.RESPONSIBLE):
                    return int(self.data(idx, self.dbValueRole))
                elif idx.column() in (Col.DUEDATE, Col.INCURRENCEDATE):
                    return str_date(self.data(idx, self.dbValueRole))
                elif idx.column() == Col.FILTERFLAGS:
                    return FilterFlags(self.data(idx, self.dbValueRole))
                else:
                    return self.data(idx, self.dbValueRole)
            except (ValueError, TypeError):
                return None

        elif role == Qt.ItemDataRole.DisplayRole:
            # Итоговые строки
            if idx.siblingAtColumn(Col.TYPE).data(self.dbValueRole) == RowType.FOOTER:
                if idx.column() == Col.RECEIVER:
                    return f"Всего по {CATEGORY_NAMES[idx.siblingAtColumn(Col.CATEGORY).data(self.dbValueRole)][:5]}"
                else:
                    return ""
            elif idx.siblingAtColumn(Col.TYPE).data(self.dbValueRole) in (RowType.HEADER, RowType.FINALFOOTER) and idx.column() != Col.RECEIVER:
                return ""

            # Все строки
            if idx.column() == Col.PAYMENTTYPE:
                return PAYMENTTYPE_NAMES[idx.data(self.dbValueRole)]
            elif idx.column() in (Col.REMAINAMOUNT, Col.TOTALAMOUNT):
                return dec_strcommaspace(self.data(idx, self.qtValueRole))
            elif idx.column() in (Col.DUEDATE, Col.INCURRENCEDATE):
                return date_displstr(self.data(idx, self.qtValueRole))
            elif idx.column() == Col.TODAYSHARE:
                return dec_strcommaspace(idx.data(self.qtValueRole))
            elif idx.column() == Col.RESPONSIBLE:
                try:
                    return self.personal_dict[idx.data(self.qtValueRole)][0]
                except KeyError:
                    return "Н/Д"

        elif role in (Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.ToolTipRole) and idx.column() == Col.DESCR:
            if idx.siblingAtColumn(Col.TYPE).data(self.dbValueRole) != RowType.LIABILITY:
                return None
            document_id: int = idx.siblingAtColumn(Col.CONTRACTDOCUMENTID).data(self.qtValueRole)
            if role == Qt.ItemDataRole.DecorationRole:
                # прозрачная заглушка выравнивает текст непривязанных строк с привязанными
                return self.contract_icon if document_id else self.empty_icon
            return self.document_tooltip(document_id) if document_id else None

        elif role == self.sortRole:
            if not idx.isValid():
                return (99, 0, 0, 0, 0)
            if idx.row() >= self.rowCount():
                return (99, 0, 0, 0, 0)
            return self.sort_key(idx.row())

        return self.stored_data(idx, role)

    def table_column(self, column: int) -> int:
        return self.table_columns[column]

    def stored_columns(self) -> list[Col]:
        return [column for column in Col if column not in self.DERIVED_COLUMNS]

    def stored_data(self, idx, role) -> Any:
        if idx.column() in self.DERIVED_COLUMNS:
            return None
        return QSqlTableModel.data(self, self.index(idx.row(), self.table_columns[idx.column()]), role)

    def raw_value(self, row: int, column: int) -> Any:
        if column in self.DERIVED_COLUMNS:
            return None
        return QSqlTableModel.data(self, self.index(row, self.table_columns[column]), Qt.ItemDataRole.DisplayRole)

    def derived_db_value(self, idx) -> Any:
        if self.raw_value(idx.row(), Col.TYPE) != RowType.LIABILITY:
            return self.NON_LIABILITY_VALUES.get(idx.column())
        liability = self.liability_rows().get(self.raw_value(idx.row(), Col.ID))
        if liability is None:
            return None
        if idx.column() == Col.REMAINAMOUNT:
            return str(liability.remain)
        if idx.column() == Col.TODAYSHARE:
            return str(liability.today_share)
        if idx.column() == Col.LASTPAYMENTDATE:
            return liability.last_payment_date
        return int(liability.filter_flags)

    def liability_rows(self) -> dict[int, LiabilityRow]:
        if self.liability_cache is None:
            self.liability_cache = self.build_liability_rows()
        return self.liability_cache

    def invalidate_liability_cache(self, *_) -> None:
        self.liability_cache = None
        self.event_cache = None
        self.header_cache = None
        self.row_sort_keys.clear()

    def header_rows(self) -> list[int]:
        if self.header_cache is None:
            self.header_cache = [row for row in range(self.rowCount()) if self.raw_value(row, Col.TYPE) == RowType.HEADER]
        return self.header_cache

    def extend_liability_cache(self, _parent, first: int, last: int) -> None:
        self.header_cache = None
        self.row_sort_keys.clear()
        if self.event_cache is None:
            return
        new_events = self.build_event_cache(range(first, last + 1))
        self.event_cache.update(new_events)
        if self.liability_cache is not None:
            self.liability_cache.update(self.build_liability_rows(new_events))

    def event_columns(self) -> dict[int, tuple]:
        if self.event_cache is None:
            self.event_cache = self.build_event_cache()
        return self.event_cache

    def build_event_cache(self, rows: range | None = None) -> dict[int, tuple]:
        event_cache: dict[int, tuple] = {}
        for row in rows if rows is not None else range(self.rowCount()):
            if self.raw_value(row, Col.TYPE) != RowType.LIABILITY:
                continue
            event_id = self.raw_value(row, Col.ID)
            if event_id is None:
                continue
            event_cache[event_id] = (self.raw_value(row, Col.CATEGORY) or 0,
                                     self.raw_value(row, Col.RECEIVERNOCASE) or "",
                                     self.to_int(self.raw_value(row, Col.RESPONSIBLE)),
                                     bool(self.raw_value(row, Col.FEATURED)),
                                     bool(self.raw_value(row, Col.HIDDEN)),
                                     self.raw_value(row, Col.TOTALAMOUNT),
                                     str_date(self.raw_value(row, Col.DUEDATE)))
        return event_cache

    def build_liability_rows(self, event_cache: dict[int, tuple] | None = None) -> dict[int, LiabilityRow]:
        liability_rows: dict[int, LiabilityRow] = {}
        if event_cache is None:
            event_cache = self.event_columns()
        for event_id, (category, receiver, responsible, featured, hidden, total, due_date) in event_cache.items():
            paid, today_share, last_payment_date = self.payment_totals.get(event_id, self.NO_PAYMENTS)
            try:
                remain = Decimal(total) - paid
            except (decimal.InvalidOperation, TypeError):
                remain = -paid
            filter_flags = calculate_filterflags(remain, due_date, today_share != 0, self.current_date)
            liability_rows[event_id] = LiabilityRow(category=category, receiver=receiver, responsible=responsible,
                                                    featured=featured, hidden=hidden, remain=remain,
                                                    today_share=today_share, last_payment_date=last_payment_date,
                                                    filter_flags=filter_flags)
        return liability_rows

    @staticmethod
    def to_int(value: Any) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def load_payment_totals(self) -> None:
        self.payment_totals = self.db_handler.load_payment_totals(self.current_date) or {}
        self.liability_cache = None

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
        return "\n".join(lines)

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.COLUMN_DATA[section][0]
            elif role == Qt.ItemDataRole.ToolTipRole:
                return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignHCenter
        return super(LiabilitySqlTableModel, self).headerData(section, orientation, role)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return QSqlTableModel.columnCount(self, parent) + len(self.DERIVED_COLUMNS)

    def setData(self, index, value, /, role=Qt.ItemDataRole.EditRole) -> bool:
        if index.column() in self.DERIVED_COLUMNS:
            return False
        if role == Qt.ItemDataRole.EditRole and isinstance(value, str):
            value = value.rstrip()
        return super(LiabilitySqlTableModel, self).setData(self.index(index.row(), self.table_column(index.column())), value, role)

    def stored_flags(self, index):
        return super(LiabilitySqlTableModel, self).flags(self.index(index.row(), 0))

    def flags(self, index, /):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if self.raw_value(index.row(), Col.TYPE) != RowType.LIABILITY:
            return self.stored_flags(index) & ~Qt.ItemFlag.ItemIsSelectable
        else:
            return self.stored_flags(index)

    def set_paid_load_months(self, months: int) -> None:
        if months == self.paid_load_months:
            return
        self.paid_load_months = months
        self.setFilter(self.db_handler.paid_load_filter(paid_threshold(QDate.currentDate(), months)))

    def select(self):
        self.beforeSelect.emit()
        self.document_titles.clear()
        self.current_date = QDate.currentDate()
        self.load_payment_totals()
        result = super(LiabilitySqlTableModel, self).select()
        while self.canFetchMore():
            self.fetchMore()
        QTimer.singleShot(0, self.afterSelect.emit)
        return result

    def insert_row(self, data: list) -> int | None:
        new_row_position: int = self.rowCount()
        self.insertRow(new_row_position)
        if len(data) != len(self.stored_columns()):
            raise IndexError("В новую строку передано неверное количество данных")
        result = self.insert_data_in_row(new_row_position, data)
        self.cacheUpdateNeeded.emit()
        return result

    def edit_row(self, row: int, data: list) -> int | None:
        result = self.insert_data_in_row(row, data)
        self.cacheUpdateNeeded.emit()
        return result

    def insert_data_in_row(self, row: int, data: list) -> int | None:
        for column, value in zip(self.stored_columns(), data):
            if column == Col.ID:
                continue
            if not self.setData(self.index(row, column), value):
                return None
        return row

    # Функция возвращает ID удаленной строки (0 в случае неудачи)
    def delete_row(self, row: int) -> int:
        deleted_id: int = self.index(row, Col.ID).data(self.qtValueRole)
        result = deleted_id if self.removeRow(row) else 0
        return result

    def removeRow(self, row, parent=QModelIndex()):
        result = super(LiabilitySqlTableModel, self).removeRow(row, parent)
        if not result:
            log.e(f"Не удалось удалить строку {row} из таблицы event: {self.lastError().text()}")
        self.cacheUpdateNeeded.emit()
        return result

    def submitAll(self) -> bool:
        result = super().submitAll()
        if not result:
            log.e(f"Не удалось записать изменения в таблицу event: {self.lastError().text()}")
        return result

    def send_filterwidget_labeldata(self, term: TermCategory, category: int, receiver: str, responsible: int, paid_today: bool, paid_months_toshow: int, featured: bool) -> None:
        threshold = paid_threshold(self.current_date, paid_months_toshow)
        receiver = receiver.lower()
        term_labels_dict = dict.fromkeys(TermCategory, 0)
        category_counts: dict[int, int] = {}
        total_by_term = 0
        for liability in self.liability_rows().values():
            if not matches_details(liability, receiver, responsible, paid_today, featured):
                continue
            if matches_category(category, liability):
                for term_category in TermCategory:
                    if matches_term(term_category, liability, threshold):
                        term_labels_dict[term_category] += 1
            if matches_term(term, liability, threshold):
                total_by_term += 1
                category_counts[liability.category] = category_counts.get(liability.category, 0) + 1

        category_labels_dict = {}
        for category_key in CATEGORY_NAMES.keys():
            category_labels_dict[category_key] = total_by_term if category_key % 1000 == 0 else category_counts.get(category_key, 0)

        self.filterwidget_labels_changed.emit(term_labels_dict, category_labels_dict)

    def set_row_formatting(self, row_formatting: RowFormatting) -> bool:
        for var in astuple(row_formatting):
            if var is None:
                return False
        self.row_formatting = row_formatting
        return True
