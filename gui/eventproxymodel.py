import re
from decimal import Decimal
from enum import IntEnum, auto
from typing import Any

from PySide6.QtCore import QSortFilterProxyModel, QDate, Qt, QModelIndex
from PySide6.QtGui import QFont

from base.formatting import dec_strcommaspace
from base.liability import CATEGORY_NAMES, LiabilityCategory
from gui.common import model_atlevel
from gui.eventsqlmodel import Col, LiabilitySqlTableModel, FilterFlags, RowFormatting, HeaderFooterSubtype
from gui.filterwidget import TermCategory
from gui.eventsqlmodel import RowType


class Filter(IntEnum):
    TERM = auto()
    CATEGORY = auto()
    HEADER = auto()
    FOOTER = auto()
    PAYTODAY = auto()


class LiabilitySortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(LiabilitySortFilterProxyModel, self).__init__(parent)

        self.sort(0)
        self.setDynamicSortFilter(True)

        self.sortfilter_enabled: bool = True

        self.term_filter: int = 0
        self.category_filter: int = 0
        self.header_filter: bool = False
        self.footer_filter: bool = False
        self.paytoday_filter: bool = False

    def enable_sortfilter(self, enable: bool) -> None:
        self.sortfilter_enabled = enable

    def set_filter(self, filter_type: int, condition: str | int | bool) -> None:
        if filter_type == Filter.TERM:
            self.term_filter = condition
        elif filter_type == Filter.CATEGORY:
            if condition == 0:
                self.category_filter = 0
            else:
                self.category_filter = list(CATEGORY_NAMES.keys())[condition]
        elif filter_type == Filter.HEADER:
            self.header_filter = condition
        elif filter_type == Filter.FOOTER:
            self.footer_filter = condition
        elif filter_type == Filter.PAYTODAY:
            self.paytoday_filter = condition
        if self.sortfilter_enabled:
            self.invalidate()

    def data(self, index, /, role=...):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()

            row_formatting: RowFormatting = model_atlevel(-1, self).row_formatting
            if not row_formatting:
                return QSortFilterProxyModel.data(self, index, role)

            row_type = index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole)

            if row_type == RowType.LIABILITY:
                filter_flags = FilterFlags(index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.dbValueRole))
                if FilterFlags.DUE in filter_flags and self.term_filter != TermCategory.DUE and not self.paytoday_filter:
                    font.setBold(self.sourceModel().row_formatting.due_textbold)
                    return font
                if FilterFlags.TODAY in filter_flags and self.term_filter != TermCategory.TODAY and not self.paytoday_filter:
                    font.setBold(self.sourceModel().row_formatting.today_textbold)
                    return font
            elif row_type == RowType.HEADER:
                font.setBold(self.sourceModel().row_formatting.header_textbold)
                return font
            elif row_type == RowType.FOOTER:
                font.setBold(self.sourceModel().row_formatting.footer_textbold)
                return font
            elif row_type == RowType.FINALFOOTER:
                font.setBold(True)
                return font

        return QSortFilterProxyModel.data(self, index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.sortfilter_enabled:
            return True

        def data_from_row(row: int, role=LiabilitySqlTableModel.dbValueRole) -> Any:
            return model_atlevel(-1, self).index(source_row, row, source_parent).data(role)

        row_type: RowType = data_from_row(Col.TYPE)

        ### Фильтрация заголовков и футеров
        if row_type != RowType.LIABILITY:
            # Не показывать, если отключены через тулбар
            if row_type == RowType.HEADER and not self.header_filter:
                return False
            if (row_type == RowType.FOOTER or row_type == RowType.FINALFOOTER) and not self.footer_filter:
                return False

            # Не показывать заголовки при наличии фильтра по категориям
            if self.category_filter:
                if row_type == RowType.HEADER:
                    return False
                elif row_type == RowType.FOOTER:
                    subtype: HeaderFooterSubtype = data_from_row(Col.SUBCATEGORY)
                    if subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                        return False
                elif row_type == RowType.FINALFOOTER:
                    return False
        return True

    def lessThan(self, source_left, source_right, /):
        if not self.sortfilter_enabled:
            return True

        left_category: int = model_atlevel(-1, self).index(source_left.row(), Col.CATEGORY, source_left.parent()).data(LiabilitySqlTableModel.qtValueRole)
        right_category: int = model_atlevel(-1, self).index(source_right.row(), Col.CATEGORY, source_right.parent()).data(LiabilitySqlTableModel.qtValueRole)
        left_type: RowType = model_atlevel(-1, self).index(source_left.row(), Col.TYPE, source_left.parent()).data(LiabilitySqlTableModel.qtValueRole)
        right_type: RowType = model_atlevel(-1, self).index(source_right.row(), Col.TYPE, source_right.parent()).data(LiabilitySqlTableModel.qtValueRole)
        left_subtype: HeaderFooterSubtype = (model_atlevel(-1, self).index(source_left.row(), Col.SUBCATEGORY, source_left.parent())
                                             .data(LiabilitySqlTableModel.qtValueRole))
        right_subtype: HeaderFooterSubtype = (model_atlevel(-1, self).index(source_right.row(), Col.SUBCATEGORY, source_right.parent())
                                              .data(LiabilitySqlTableModel.qtValueRole))

        # Последний футер сразу внизу
        if left_type == RowType.FINALFOOTER or right_type == RowType.FINALFOOTER:
            return right_type == RowType.FINALFOOTER
        if left_category != right_category:
            # Уточнение расположения footerа раздела (имеет категорию X000 и тип 3)
            # Если строки находятся в одном разделе
            if left_category and right_category:
                if left_category // 1000 == right_category // 1000:
                    if left_type == RowType.FOOTER and left_subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                        return False
                    if right_type == RowType.FOOTER and right_subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                        return True
                return left_category < right_category
            else:
                return False
        else:
            if left_type != right_type:
                return right_type > left_type
            else:
                left_duedate: QDate = model_atlevel(-1, self).index(source_left.row(), Col.DUEDATE,  source_left.parent()).data(LiabilitySqlTableModel.qtValueRole)
                right_duedate: QDate = model_atlevel(-1, self).index(source_right.row(), Col.DUEDATE, source_right.parent()).data(LiabilitySqlTableModel.qtValueRole)
                return left_duedate < right_duedate


class LiabilityTotalsProxyModel(QSortFilterProxyModel):

    TOTAL_CATEGORY = 9999

    decimalValueRole: int = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent=None):
        super(LiabilityTotalsProxyModel, self).__init__(parent)

        self.setDynamicSortFilter(True)

        self.stored_total = dict()
        self.stored_remain = dict()
        self.stored_today = dict()

    def recalculate_totals(self) -> None:
        for stored_dict in self.stored_total, self.stored_remain, self.stored_today:
            for category in LiabilityCategory:
                stored_dict[category] = 0
            stored_dict[self.TOTAL_CATEGORY] = 0

        for row in range(self.rowCount()):
            if self.index(row, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.LIABILITY:
                category: int = self.index(row, Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole)
                totalamount: Decimal = self.index(row, Col.TOTALAMOUNT, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                self.stored_total[category] += totalamount
                remainamount: Decimal = self.index(row, Col.REMAINAMOUNT, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                self.stored_remain[category] += remainamount
                todayshare: Decimal = self.index(row, Col.TODAYSHARE, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
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
        if model_atlevel(-1, self).index(source_row, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FINALFOOTER:
            return True
        category: int = self.sourceModel().index(source_row, Col.CATEGORY, source_parent).data(LiabilitySqlTableModel.dbValueRole)
        # костыль
        if category:
            return self.iterate_source_model(category, category == LiabilityCategory.TOP_CURRENT)
        else:
            return False

    def data(self, index, /, role=...):
        if role == Qt.ItemDataRole.FontRole:
            if index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) in (RowType.FOOTER, RowType.FINALFOOTER):
                if index.column() in (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE):
                    font: QFont = QFont()
                    font.setBold(True)
                    return font
        elif role == Qt.ItemDataRole.DisplayRole:
            if index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FOOTER:
                category: int = index.siblingAtColumn(Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole)
                if index.column() == Col.TOTALAMOUNT:
                    value = self.stored_total[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == Col.REMAINAMOUNT:
                    value = self.stored_remain[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == Col.TODAYSHARE:
                    value = self.stored_today[category]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
            elif index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FINALFOOTER:
                if index.column() == Col.TOTALAMOUNT:
                    value = self.stored_total[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == Col.REMAINAMOUNT:
                    value = self.stored_remain[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
                if index.column() == Col.TODAYSHARE:
                    value = self.stored_today[self.TOTAL_CATEGORY]
                    return "" if value == Decimal(0) else dec_strcommaspace(value)
        elif role == self.decimalValueRole:
            if index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FOOTER:
                category: int = index.siblingAtColumn(Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole)
                if index.column() == Col.TOTALAMOUNT:
                    return self.stored_total[category]
                if index.column() == Col.REMAINAMOUNT:
                    return self.stored_remain[category]
                if index.column() == Col.TODAYSHARE:
                    return self.stored_today[category]
            elif index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FINALFOOTER:
                if index.column() == Col.TOTALAMOUNT:
                    return self.stored_total[self.TOTAL_CATEGORY]
                if index.column() == Col.REMAINAMOUNT:
                    return self.stored_remain[self.TOTAL_CATEGORY]
                if index.column() == Col.TODAYSHARE:
                    return self.stored_today[self.TOTAL_CATEGORY]

        return QSortFilterProxyModel.data(self, index, role)

    def iterate_source_model(self, category: int, subcategories: bool = False):
        source_model = model_atlevel(-1, self)
        row_count: int = source_model.rowCount()
        subcategory_prefix: int = category // 1000
        for i in range(row_count):
            if source_model.index(i, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.LIABILITY:
                if subcategories:
                    if source_model.index(i, Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole) // 1000 == subcategory_prefix:
                        return True
                else:
                    if source_model.index(i, Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole) == category:
                        return True
            else:
                continue
        return False
