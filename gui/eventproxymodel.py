import re
from decimal import Decimal
from enum import IntEnum, auto
from typing import Any

from PySide6.QtCore import QSortFilterProxyModel, QDate, Qt, QModelIndex
from PySide6.QtGui import QFont

from base.event import EventField, RowType, EventCategory, Event
from base.formatting import dec_strcommaspace
from gui.common import model_atlevel
from gui.eventmodel import EventTableModel, TermRoleFlags, HeaderFooterSubtype, HeaderFooterField, EventHeader, EventFooter, FinalFooter, RowFormatting
from gui.filterwidget import TermCategory


class Filter(IntEnum):
    TERM = auto()
    CATEGORY = auto()
    RECEIVER = auto()
    RESPONSIBLE = auto()
    HEADER = auto()
    FOOTER = auto()
    PAYTODAY = auto()


class EventListProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(EventListProxyModel, self).__init__(parent)

        self.sort(0)
        self.setDynamicSortFilter(True)

        self.sortfilter_enabled: bool = True

        self.term_filter: int = 0
        self.category_filter: int = 0
        self.receiver_filter: str = ""
        self.responsible_filter: str = ""
        self.header_filter: bool = False
        self.footer_filter: bool = False
        self.paytoday_filter: bool = False

        self.stats: dict | None = None

    def enable_sortfilter(self, enable: bool) -> None:
        self.sortfilter_enabled = enable

    def store_stats(self, stats: dict) -> None:
        self.stats = stats
        self.invalidate()

    def set_filter(self, filter_type: int, condition: str | int | bool) -> None:
        if filter_type == Filter.TERM:
            self.term_filter = condition
        elif filter_type == Filter.CATEGORY:
            if condition == 0:
                self.category_filter = 0
            else:
                self.category_filter = list(self.sourceModel().CATEGORY_NAMES.keys())[condition]
        elif filter_type == Filter.RECEIVER:
            self.receiver_filter = condition
        elif filter_type == Filter.RESPONSIBLE:
            self.responsible_filter = condition
        elif filter_type == Filter.HEADER:
            self.header_filter = condition
        elif filter_type == Filter.FOOTER:
            self.footer_filter = condition
        elif filter_type == Filter.PAYTODAY:
            self.paytoday_filter = condition
        if self.sortfilter_enabled:
            self.invalidate()

    def filters_active(self) -> bool:
        return self.term_filter != 0 or self.category_filter != 0 or self.receiver_filter != "" or self.responsible_filter != "" or self.paytoday_filter

    def data(self, index, /, role=...):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.FontRole:
            try:
                entry = self.sourceModel().event_list[self.mapToSource(index).row()]
            except IndexError:
                return QSortFilterProxyModel.data(self, index, role)
            font = QFont()
            row_formatting: RowFormatting = self.sourceModel().row_formatting
            if not row_formatting:
                return QSortFilterProxyModel.data(self, index, role)
            if isinstance(entry, Event):
                term_flags = index.siblingAtColumn(EventField.TERMFLAGS).data(EventTableModel.internalValueRole)
                if TermRoleFlags.DUE in term_flags and self.term_filter != TermCategory.DUE:
                    font.setBold(self.sourceModel().row_formatting.due_textbold)
                    return font
                if TermRoleFlags.TODAY in term_flags and self.term_filter != TermCategory.TODAY:
                    font.setBold(self.sourceModel().row_formatting.today_textbold)
                    return font
            elif isinstance(entry, EventHeader):
                font.setBold(self.sourceModel().row_formatting.header_textbold)
                return font
            elif isinstance(entry, EventFooter):
                font.setBold(self.sourceModel().row_formatting.footer_textbold)
                return font
            elif isinstance(entry, FinalFooter):
                font.setBold(True)
                return font

        return QSortFilterProxyModel.data(self, index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.sortfilter_enabled:
            return True

        def data_from_row(row: int, role=EventTableModel.internalValueRole) -> Any:
            return self.sourceModel().index(source_row, row, source_parent).data(role)

        row_type: RowType = data_from_row(EventField.TYPE)

        ### Фильтрация строк с данными
        if row_type == RowType.EVENT:

            ## Фильтр по сроку
            term_flags: TermRoleFlags = data_from_row(EventField.TERMFLAGS, EventTableModel.internalValueRole)
            # Проверка на оплаченность
            is_paid: bool = TermRoleFlags.PAID in term_flags
            if (self.term_filter == TermCategory.PAID and not is_paid) or (self.term_filter != TermCategory.PAID and is_paid):
                return False
            # Проверка на давность оплаты
            if self.term_filter == TermCategory.PAID:
                last_payment_date: QDate = data_from_row(EventField.LASTPAYMENTDATE)
                if not last_payment_date.isValid() or last_payment_date < self.sourceModel().paid_minimum_date:
                    return False
            # Проверка по дате
            if self.term_filter == TermCategory.DUE:
                if TermRoleFlags.DUE not in term_flags:
                    return False
            elif self.term_filter == TermCategory.TODAY:
                if TermRoleFlags.TODAY not in term_flags:
                    return False
            elif self.term_filter == TermCategory.WEEK:
                if TermRoleFlags.WEEK not in term_flags:
                    return False
            elif self.term_filter == TermCategory.MONTH:
                if TermRoleFlags.MONTH not in term_flags:
                    return False

            ## Фильтр по категории
            if self.category_filter != TermCategory.UNPAID:
                if data_from_row(EventField.CATEGORY) != self.category_filter:
                    return False

            ## Фильтр по получателю
            if self.receiver_filter:
                match: re.Match = re.search(self.receiver_filter, data_from_row(EventField.RECEIVER), re.IGNORECASE)
                if not match:
                    return False

            ## Фильтр по ответственному
            if self.responsible_filter:
                match: re.Match = re.search(self.responsible_filter, data_from_row(EventField.RESPONSIBLE), re.IGNORECASE)
                if not match:
                    return False

            ## Фильтр по оплате сегодня
            if self.paytoday_filter:
                if data_from_row(EventField.TODAYSHARE) == 0:
                    return False

        ### Фильтрация заголовков и футеров
        else:
            # Не показывать, если отключены через тулбар
            if row_type == RowType.HEADER and not self.header_filter:
                return False
            if (row_type == RowType.FOOTER or row_type == RowType.FINALFOOTER) and not self.footer_filter:
                return False

            # Не показывать заголовки при наличии фильтра по категориям
            subtype: HeaderFooterSubtype = data_from_row(HeaderFooterField.SUBTYPE)
            if self.category_filter != 0:
                if row_type == RowType.HEADER:
                    return False
                elif row_type == RowType.FOOTER and subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                    return False
                elif row_type == RowType.FINALFOOTER:
                    return False

        return True


    def lessThan(self, source_left, source_right, /):
        if not self.sortfilter_enabled:
            return True

        left_category: int = self.sourceModel().index(source_left.row(), EventField.CATEGORY, source_left.parent()).data(EventTableModel.sortRole)
        right_category: int = self.sourceModel().index(source_right.row(), EventField.CATEGORY, source_right.parent()).data(EventTableModel.sortRole)
        left_type: RowType = self.sourceModel().index(source_left.row(), HeaderFooterField.TYPE, source_left.parent()).data(EventTableModel.internalValueRole)
        right_type: RowType = self.sourceModel().index(source_right.row(), HeaderFooterField.TYPE, source_right.parent()).data(EventTableModel.internalValueRole)
        left_subtype: HeaderFooterSubtype = (self.sourceModel().index(source_left.row(), HeaderFooterField.SUBTYPE, source_left.parent())
                                             .data(EventTableModel.internalValueRole))
        right_subtype: HeaderFooterSubtype = (self.sourceModel().index(source_right.row(), HeaderFooterField.SUBTYPE, source_right.parent())
                                              .data(EventTableModel.internalValueRole))

        # Последний футер сразу внизу
        if left_type == RowType.FINALFOOTER or right_type == RowType.FINALFOOTER:
            return right_type == RowType.FINALFOOTER
        if left_category != right_category:
            # Уточнение расположения footerа раздела (имеет категорию X000 и тип 3)
            # Если строки находятся в одном разделе
            if left_category // 1000 == right_category // 1000:
                if left_type == RowType.FOOTER and left_subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                    return False
                if right_type == RowType.FOOTER and right_subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                    return True
            return left_category < right_category
        else:
            if left_type != right_type:
                return right_type > left_type
            else:
                left_duedate: QDate = self.sourceModel().index(source_left.row(), EventField.DUEDATE,  source_left.parent()).data(EventTableModel.internalValueRole)
                right_duedate: QDate = self.sourceModel().index(source_right.row(), EventField.DUEDATE, source_right.parent()).data(EventTableModel.internalValueRole)
                return left_duedate < right_duedate


class EventListFinalFilterModel(QSortFilterProxyModel):

    TOTAL_CATEGORY = 9999
    TOTAL_DECIMALS_FONTFAMILY = "Roboto"

    decimalValueRole: int = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent=None):
        super(EventListFinalFilterModel, self).__init__(parent)

        self.setDynamicSortFilter(True)

        self.stored_total = dict()
        self.stored_remain = dict()
        self.stored_today = dict()

    def recalculate_totals(self) -> None:
        for stored_dict in self.stored_total, self.stored_remain, self.stored_today:
            for category in EventCategory:
                stored_dict[category] = 0
            stored_dict[self.TOTAL_CATEGORY] = 0

        for row in range(self.rowCount()):
            if self.index(row, EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.EVENT:
                category: int = self.index(row, EventField.CATEGORY).data(EventTableModel.internalValueRole)
                totalamount: Decimal = self.index(row, EventField.TOTALAMOUNT, QModelIndex()).data(EventTableModel.internalValueRole)
                self.stored_total[category] += totalamount
                remainamount: Decimal = self.index(row, EventField.REMAINAMOUNT, QModelIndex()).data(EventTableModel.internalValueRole)
                self.stored_remain[category] += remainamount
                todayshare: Decimal = self.index(row, EventField.TODAYSHARE, QModelIndex()).data(EventTableModel.internalValueRole)
                self.stored_today[category] += todayshare
        for stored_dict in self.stored_total, self.stored_remain, self.stored_today:
            total_total: Decimal = Decimal(0)
            for category in stored_dict.keys():
                if category % 100 == 0:
                    category_prefix: int = category // 1000
                    running_total: Decimal = Decimal(0)
                    for key, value in stored_dict.items():
                        if key // 1000 == category_prefix:
                            running_total += value
                    stored_dict[category] = running_total
                if category % 1000 != 0:
                    total_total += stored_dict[category]
            stored_dict[self.TOTAL_CATEGORY] = total_total
        self.layoutChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent, /):
        # Фильтрация заголовков пустых подразделов
        if self.sourceModel().index(source_row, HeaderFooterField.TYPE).data(EventTableModel.internalValueRole) == RowType.FINALFOOTER:
            return True
        category: int = self.sourceModel().index(source_row, HeaderFooterField.CATEGORY, source_parent).data(EventTableModel.internalValueRole)
        return self.iterate_source_model(category, category == EventCategory.TOP_CURRENT)

    def data(self, index, /, role=...):
        if role == Qt.ItemDataRole.FontRole:
            if index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) in (RowType.FOOTER, RowType.FINALFOOTER):
                if index.column() in (EventField.TOTALAMOUNT, EventField.REMAINAMOUNT, EventField.TODAYSHARE):
                    font: QFont = QFont()
                    font.setBold(True)
                    font.setFamily(self.TOTAL_DECIMALS_FONTFAMILY)
                    return font
        if role == Qt.ItemDataRole.DisplayRole:
            if index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.FOOTER:
                category: int = index.siblingAtColumn(EventField.CATEGORY).data(EventTableModel.internalValueRole)
                if index.column() == EventField.TOTALAMOUNT:
                    value = self.stored_total[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == EventField.REMAINAMOUNT:
                    value = self.stored_remain[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == EventField.TODAYSHARE:
                    value = self.stored_today[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
            elif index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.FINALFOOTER:
                if index.column() == EventField.TOTALAMOUNT:
                    value = self.stored_total[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == EventField.REMAINAMOUNT:
                    value = self.stored_remain[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == EventField.TODAYSHARE:
                    value = self.stored_today[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
        if role == self.decimalValueRole:
            if index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.FOOTER:
                category: int = index.siblingAtColumn(EventField.CATEGORY).data(EventTableModel.internalValueRole)
                if index.column() == EventField.TOTALAMOUNT:
                    return self.stored_total[category]
                if index.column() == EventField.REMAINAMOUNT:
                    return self.stored_remain[category]
                if index.column() == EventField.TODAYSHARE:
                    return self.stored_today[category]
            elif index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.FINALFOOTER:
                if index.column() == EventField.TOTALAMOUNT:
                    return self.stored_total[self.TOTAL_CATEGORY]
                if index.column() == EventField.REMAINAMOUNT:
                    return self.stored_remain[self.TOTAL_CATEGORY]
                if index.column() == EventField.TODAYSHARE:
                    return self.stored_today[self.TOTAL_CATEGORY]

        return QSortFilterProxyModel.data(self, index, role)

    def iterate_source_model(self, category: int, subcategories: bool = False):
        source_model = model_atlevel(-1, self)
        row_count: int = source_model.rowCount()
        subcategory_prefix: int = category // 1000
        for i in range(row_count):
            if source_model.index(i, EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.EVENT:
                if subcategories:
                    if source_model.index(i, EventField.CATEGORY).data(EventTableModel.internalValueRole) // 1000 == subcategory_prefix:
                        return True
                else:
                    if source_model.index(i, EventField.CATEGORY).data(EventTableModel.internalValueRole) == category:
                        return True
            else:
                continue
        return False
