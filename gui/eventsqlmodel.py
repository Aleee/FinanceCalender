import decimal
from dataclasses import dataclass, astuple
from decimal import Decimal
from enum import IntEnum
from typing import Any

import lovely_logger as log

from PySide6.QtCore import Qt, QModelIndex, Signal, QDate, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSql import QSqlTableModel, QSqlQuery

from base.contract import DocumentTitle
from base.date import date_displstr, str_date, date_str
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, FilterFlags, RowType, HeaderFooterSubtype, TermCategory,
                             PAYMENTTYPE_NAMES, calculate_filterflags, build_filter_clause)


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

    ICON_SIZE = 16

    dbValueRole = Qt.ItemDataRole.UserRole + 1
    qtValueRole = Qt.ItemDataRole.UserRole + 2
    sortRole = Qt.ItemDataRole.UserRole + 10

    afterRowRemoval = Signal()
    cacheUpdateNeeded = Signal()


    def __init__(self, db_handler: DBHandler, parent=None):
        super(LiabilitySqlTableModel, self).__init__(parent)

        self.db_handler = db_handler
        self.current_date: QDate = QDate().currentDate()
        self.paid_minimum_date: QDate = QDate()
        self.next_select_norecalc: bool = False
        self.filter_to_restore: str = ""
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

    def sort_key(self, row):
        entry_id = self.data(self.index(row, Col.ID), self.qtValueRole)
        key = self.sort_cache.get(entry_id)
        if key is None:
            key = self.compute_sort_key(row)
            self.sort_cache[entry_id] = key
        return key

    def invalidate_sort_cache(self):
        self.sort_cache.clear()

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
            return super(LiabilitySqlTableModel, self).data(idx, Qt.ItemDataRole.DisplayRole)

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

        return super(LiabilitySqlTableModel, self).data(idx, role)

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

    def flags(self, index, /):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if index.siblingAtColumn(Col.TYPE).data(self.qtValueRole) != RowType.LIABILITY:
            return super(LiabilitySqlTableModel, self).flags(index) & ~Qt.ItemFlag.ItemIsSelectable
        else:
            return super(LiabilitySqlTableModel, self).flags(index)

    def select(self, recalculate_manual_data: bool = True):
        self.beforeSelect.emit()
        self.document_titles.clear()
        if not self.next_select_norecalc and recalculate_manual_data:
            self.calculate_manual_data()
            self.insert_filterflags()
        result = super(LiabilitySqlTableModel, self).select()
        while self.canFetchMore():
            self.fetchMore()
        self.next_select_norecalc = False
        QTimer.singleShot(0, self.afterSelect.emit)
        return result

    def insert_row(self, data: list) -> int | None:
        new_row_position: int = self.rowCount()
        self.insertRow(new_row_position)
        if len(data) != self.columnCount():
            raise IndexError("В новую строку передано неверное количество данных")
        result = self.insert_data_in_row(new_row_position, data)
        self.cacheUpdateNeeded.emit()
        return result

    def edit_row(self, row: int, data: list) -> int | None:
        result = self.insert_data_in_row(row, data)
        self.cacheUpdateNeeded.emit()
        return result

    def insert_data_in_row(self, row: int, data: list) -> int | None:
        for column, value in enumerate(data):
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

    def set_filters(self, term: TermCategory, category: int, receiver: str, responsible: str, paid_today: bool, paid_months_toshow: int, featured: bool) -> None:
        filt = build_filter_clause(term, category, receiver, responsible, paid_today, paid_months_toshow, featured, self.current_date)
        filt += f" OR filterflags = {int(FilterFlags.NONE)})"

        self.send_filterwidget_labeldata(term, category, receiver, responsible, paid_today, paid_months_toshow, featured)
        self.next_select_norecalc = True
        self.setFilter(filt)

    def modify_filter(self, new_clause: str):
        self.next_select_norecalc = True
        self.filter_to_restore = self.filter()
        self.setFilter(self.filter() + " " + new_clause)

    def restore_modified_filter(self):
        self.next_select_norecalc = True
        self.setFilter(self.filter_to_restore)
        self.filter_to_restore = ""

    def update_labels(self, term, category, receiver, responsible, paid_today, paid_months_toshow, featured):
        self.send_filterwidget_labeldata(term, category, receiver, responsible, paid_today, paid_months_toshow, featured)

    def send_filterwidget_labeldata(self, term: TermCategory, category: int, receiver: str, responsible: str, paid_today: bool, paid_months_toshow: int, featured: bool) -> None:
        term_subqueries = []
        for term_category in TermCategory:
            clause = build_filter_clause(term_category, category, receiver, responsible, paid_today, paid_months_toshow, featured, self.current_date)
            term_subqueries.append(f"(SELECT COUNT(id) FROM event WHERE {clause}))")
        query = QSqlQuery(f"SELECT {', '.join(term_subqueries)}")
        if not query.isActive():
            log.w(f"Не удалось получить статистику по срокам для боковой панели. Ошибка: {query.lastError().text()}")
        query.next()
        term_labels_dict = {}
        for i, term_category in enumerate(TermCategory):
            term_labels_dict[term_category] = query.value(i)

        category_subqueries = []
        for category in list(CATEGORY_NAMES.keys()):
            clause = build_filter_clause(term, category, receiver, responsible, paid_today, paid_months_toshow, featured, self.current_date)
            category_subqueries.append(f"(SELECT COUNT(id) FROM event WHERE {clause}))")
        query = QSqlQuery(f"SELECT {', '.join(category_subqueries)}")
        if not query.isActive():
            log.w(f"Не удалось получить статистику по категориям для боковой панели. Ошибка: {query.lastError().text()}")
        query.next()
        category_labels_dict = {}
        for i, category in enumerate(CATEGORY_NAMES.keys()):
            category_labels_dict[category] = query.value(i)

        self.filterwidget_labels_changed.emit(term_labels_dict, category_labels_dict)

    def calculate_manual_data(self):
        self.db_handler.insert_manualcalculated_data()

    def insert_filterflags(self):
        self.db_handler.insert_filterflags()

    def recalculate_values_on_newpayment(self, index: QModelIndex, amount: Decimal, date: QDate, last_payment_date: QDate):

        old_remain: Decimal = index.siblingAtColumn(Col.REMAINAMOUNT).data(self.qtValueRole)
        new_remain: Decimal = old_remain - amount if old_remain - amount > 0.001 else Decimal(0)
        self.setData(index.siblingAtColumn(Col.REMAINAMOUNT), str(new_remain))

        old_today_amount: Decimal = index.siblingAtColumn(Col.TODAYSHARE).data(self.qtValueRole)
        if date == QDate.currentDate():
            today_share: Decimal = old_today_amount + amount
        else:
            today_share: Decimal = old_today_amount
        self.setData(index.siblingAtColumn(Col.TODAYSHARE), str(today_share))

        self.setData(index.siblingAtColumn(Col.LASTPAYMENTDATE), date_str(last_payment_date))

        new_filter_flags: FilterFlags = calculate_filterflags(new_remain, index.siblingAtColumn(Col.DUEDATE).data(self.qtValueRole), bool(today_share), self.current_date)
        self.setData(index.siblingAtColumn(Col.FILTERFLAGS), int(new_filter_flags))

    def recalculate_values_on_paymentdelete(self, index: QModelIndex, amount: Decimal, date: QDate, last_payment_date: QDate):

        old_remain: Decimal = index.siblingAtColumn(Col.REMAINAMOUNT).data(self.qtValueRole)
        new_remain: Decimal = old_remain + amount
        total_amount: Decimal = index.siblingAtColumn(Col.TOTALAMOUNT).data(self.qtValueRole)
        if new_remain > total_amount:
            new_remain = total_amount
        self.setData(index.siblingAtColumn(Col.REMAINAMOUNT), str(new_remain))

        old_today_amount: Decimal = index.siblingAtColumn(Col.TODAYSHARE).data(self.qtValueRole)
        if date == QDate.currentDate():
            today_share: Decimal = old_today_amount - amount
            self.setData(index.siblingAtColumn(Col.TODAYSHARE), str(today_share))
        else:
            today_share: Decimal = old_today_amount

        self.setData(index.siblingAtColumn(Col.LASTPAYMENTDATE), date_str(last_payment_date))

        new_filter_flags: FilterFlags = calculate_filterflags(new_remain, index.siblingAtColumn(Col.DUEDATE).data(self.qtValueRole), bool(today_share), self.current_date)
        self.setData(index.siblingAtColumn(Col.FILTERFLAGS), int(new_filter_flags))

    def set_row_formatting(self, row_formatting: RowFormatting) -> bool:
        for var in astuple(row_formatting):
            if var is None:
                return False
        self.row_formatting = row_formatting
        return True
