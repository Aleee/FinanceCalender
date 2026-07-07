import re
from decimal import Decimal
from enum import IntEnum, auto
from typing import Any

from PySide6 import QtGui
from PySide6.QtCore import QSortFilterProxyModel, QDate, Qt, QModelIndex, SIGNAL, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QApplication

from base.formatting import dec_strcommaspace
from base.liability import CATEGORY_NAMES, LiabilityCategory, FilterFlags, RowType, HeaderFooterSubtype
from gui.common import model_atlevel
from gui.commonwidgets.common import RowStyle
from gui.eventsqlmodel import Col, LiabilitySqlTableModel, RowFormatting
from gui.filterwidget import TermCategory


class Filter(IntEnum):
    TERM = auto()
    CATEGORY = auto()
    HEADER = auto()
    FOOTER = auto()
    PAYTODAY = auto()


class LiabilitySortFilterProxyModel(QSortFilterProxyModel):

    modelInvalidated = Signal()
    styleRole = Qt.ItemDataRole.UserRole + 20

    VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    DARKER_RATIO: int = 110
    BORDER_WIDTH: int = 1

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

        self.cache: dict = {}
        self.modelReset.connect(self.cache_data)
        self.dataChanged.connect(self.cache_data)

        self.style_cache = {}

    def invalidate_style_cache(self):
        self.style_cache.clear()

    def style_data(self, row):
        entry_id = self.index(row, Col.ID).data(LiabilitySqlTableModel.qtValueRole)
        key = self.style_cache.get(entry_id)
        if key is None:
            key = self.compute_style_for_source(self.mapToSource(self.index(row, Col.ID)), row)
            self.style_cache[entry_id] = key
        return self.style_cache[entry_id]

    def compute_style_for_source(self, source_index, proxy_row) -> RowStyle:
        base_model = self.sourceModel()

        row_formatting = base_model.row_formatting
        role = LiabilitySqlTableModel.qtValueRole
        db_role = LiabilitySqlTableModel.dbValueRole

        row_type: RowType = base_model.index(source_index.row(), Col.TYPE).data(db_role)
        style = RowStyle(vertical_grid_color=self.VERTICAL_GRID_COLOR)

        if row_type == RowType.LIABILITY:
            style.highlight_color = QColor("#CDE8FF")
            filter_flags: FilterFlags = base_model.index(source_index.row(), Col.FILTERFLAGS).data(role)
            due_fore = QColor(row_formatting.due_forecolor)
            today_fore = QColor(row_formatting.today_forecolor)
            due_back = QColor(row_formatting.due_backcolor)
            today_back = QColor(row_formatting.today_backcolor)
            due_condition = (
                    FilterFlags.DUE in filter_flags
                    and self.term_filter != TermCategory.DUE
                    and not self.paytoday_filter)
            today_condition = (
                    FilterFlags.TODAY in filter_flags
                    and self.term_filter != TermCategory.TODAY
                    and not self.paytoday_filter)
            if due_condition:
                style.text_color = due_fore
                style.highlighted_text_color = due_fore
                style.background_brush = QBrush(due_back)
                style.vertical_grid_color = due_back.darker(self.DARKER_RATIO)
            elif today_condition:
                style.text_color = today_fore
                style.highlighted_text_color = today_fore
                style.background_brush = QBrush(today_back)
                style.vertical_grid_color = today_back.darker(self.DARKER_RATIO)
            else:
                style.highlighted_text_color = QColor("black")
                style.background_brush = QBrush(QColor("#FFFFFF"))

        elif row_type == RowType.HEADER:
            subtype: HeaderFooterSubtype = base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.header_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_section_backcolor))
            elif subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.header_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_subsection_backcolor))

        elif row_type == RowType.FOOTER:
            subtype: HeaderFooterSubtype = (base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role))
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.footer_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_section_backcolor))
            elif subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.footer_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_subsection_backcolor))

        elif row_type == RowType.FINALFOOTER:
            style.background_brush = QBrush(self.FINALFOOTER_BACK_COLOR)

        return style

    def cache_data(self):
        self.cache = {}

        source = self.sourceModel()
        role = LiabilitySqlTableModel.dbValueRole

        for row in range(source.rowCount()):
            idx_type = source.index(row, Col.TYPE)
            if idx_type.data(role) != RowType.LIABILITY:
                continue

            category = source.index(row, Col.CATEGORY).data(role)

            group = category // 1000

            self.cache[category] = self.cache.get(category, 0) + 1
            self.cache[group] = self.cache.get(group, 0) + 1

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
            self.modelInvalidated.emit()

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

        elif role == self.styleRole:
            return self.style_data(index.row())

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
        model = self.sourceModel()
        left_key = model.data(source_left, model.sortRole)
        right_key = model.data(source_right, model.sortRole)
        return left_key < right_key


class LiabilityTotalsProxyModel(QSortFilterProxyModel):

    TOTAL_CATEGORY = 9999

    # VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    # ALTERNATE_ROW_COLOR: QColor = QColor("#f7f7f7")
    # FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    # DARKER_RATIO: int = 110
    # BORDER_WIDTH: int = 1

    decimalValueRole: int = Qt.ItemDataRole.UserRole + 4
    RowStyleRole: int = Qt.ItemDataRole.UserRole + 20

    def __init__(self, parent=None):
        super(LiabilityTotalsProxyModel, self).__init__(parent)

        self.setDynamicSortFilter(True)

        self.stored_total = dict()
        self.stored_remain = dict()
        self.stored_today = dict()

    #     self.style_cache: dict = {}
    #
    # def refresh_style_cache(self):
    #     QTimer.singleShot(0, self.refresh_style_cache_delayed)
    #     return

    # def refresh_style_cache_delayed(self):
    #     self.proxy_model = model_atlevel(-1, self)
    #     proxy_rows = self.rowCount()
    #     self.style_cache = {}
    #     # ids = {}
    #     for proxy_row in range(proxy_rows):
    #         proxy_index = self.index(proxy_row, 0)
    #         source_index = self.proxy_model.mapToSource(self.mapToSource(proxy_index))
    #         id_value = source_index.siblingAtColumn(Col.ID).data(LiabilitySqlTableModel.qtValueRole)
    #         self.style_cache[id_value] = self.compute_style_for_source(source_index, proxy_row)
    #     #     ids[id_value] = self.compute_style_for_source(source_index, proxy_row)
    #     # print(ids)

    # def row_style(self, id_value):
    #     try:
    #         return self.style_cache[id_value]
    #     except KeyError:
    #         return None

    # def compute_style_for_source(self, source_index, proxy_row) -> RowStyle:
    #     proxy_model = model_atlevel(-1, self)
    #     base_model = model_atlevel(-2, self)
    #
    #     row_formatting = base_model.row_formatting
    #     role = LiabilitySqlTableModel.qtValueRole
    #     db_role = LiabilitySqlTableModel.dbValueRole
    #
    #     row_type: RowType = base_model.index(source_index.row(), Col.TYPE).data(db_role)
    #
    #     style = RowStyle(vertical_grid_color=self.VERTICAL_GRID_COLOR)
    #
    #     if row_type == RowType.LIABILITY:
    #
    #         style.highlight_color = QColor("#CDE8FF")
    #
    #         filter_flags: FilterFlags = base_model.index(source_index.row(), Col.FILTERFLAGS).data(role)
    #
    #         due_fore = QColor(row_formatting.due_forecolor)
    #         today_fore = QColor(row_formatting.today_forecolor)
    #         due_back = QColor(row_formatting.due_backcolor)
    #         today_back = QColor(row_formatting.today_backcolor)
    #
    #         due_condition = (
    #                 FilterFlags.DUE in filter_flags
    #                 and proxy_model.term_filter != TermCategory.DUE
    #                 and not proxy_model.paytoday_filter)
    #
    #         today_condition = (
    #                 FilterFlags.TODAY in filter_flags
    #                 and proxy_model.term_filter != TermCategory.TODAY
    #                 and not proxy_model.paytoday_filter)
    #
    #         if due_condition:
    #             style.text_color = due_fore
    #             style.highlighted_text_color = due_fore
    #             style.background_brush = QBrush(due_back)
    #             style.vertical_grid_color = due_back.darker(self.DARKER_RATIO)
    #
    #         elif today_condition:
    #             style.text_color = today_fore
    #             style.highlighted_text_color = today_fore
    #             style.background_brush = QBrush(today_back)
    #             style.vertical_grid_color = today_back.darker(self.DARKER_RATIO)
    #
    #         else:
    #             style.highlighted_text_color = QColor("black")
    #             if row_formatting.zebra_style and proxy_row % 2 == 0:
    #                 style.background_brush = QBrush(self.ALTERNATE_ROW_COLOR)
    #             else:
    #                 style.background_brush = QBrush(QColor("#FFFFFF"))
    #
    #     elif row_type == RowType.HEADER:
    #
    #         subtype: HeaderFooterSubtype = base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role)
    #
    #         if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
    #             style.text_color = QColor(row_formatting.header_section_forecolor)
    #             style.background_brush = QBrush(QColor(row_formatting.header_section_backcolor))
    #
    #         elif subtype == HeaderFooterSubtype.ORDINARY:
    #             style.text_color = QColor(row_formatting.header_subsection_forecolor)
    #             style.background_brush = QBrush(QColor(row_formatting.header_subsection_backcolor))
    #
    #     elif row_type == RowType.FOOTER:
    #
    #         subtype: HeaderFooterSubtype = (base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role))
    #         if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
    #             style.text_color = QColor(row_formatting.footer_section_forecolor)
    #             style.background_brush = QBrush(QColor(row_formatting.footer_section_backcolor))
    #
    #         elif subtype == HeaderFooterSubtype.ORDINARY:
    #             style.text_color = QColor(row_formatting.footer_subsection_forecolor)
    #             style.background_brush = QBrush(QColor(row_formatting.footer_subsection_backcolor))
    #
    #     elif row_type == RowType.FINALFOOTER:
    #         style.background_brush = QBrush(self.FINALFOOTER_BACK_COLOR)
    #
    #     return style

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
        if model_atlevel(-1, self).index(source_row, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FINALFOOTER:
            return True
        category: int = self.sourceModel().index(source_row, Col.CATEGORY, source_parent).data(LiabilitySqlTableModel.dbValueRole)
        if category:
            return self.category_not_empty(category, category == LiabilityCategory.TOP_CURRENT)
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

    def category_not_empty(self, category: int, subcategories: bool = False):
        if subcategories:
            subcategory_prefix: int = category // 1000
            return model_atlevel(-1, self).cache.get(subcategory_prefix, 0) > 0
        else:
            return model_atlevel(-1, self).cache.get(category, 0) > 0




        # source_model = model_atlevel(-1, self)
        # row_count: int = source_model.rowCount()
        # subcategory_prefix: int = category // 1000
        # for i in range(row_count):
        #     if source_model.index(i, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.LIABILITY:
        #         if subcategories:
        #             if source_model.index(i, Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole) // 1000 == subcategory_prefix:
        #                 return True
        #         else:
        #             if source_model.index(i, Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole) == category:
        #                 return True
        #     else:
        #         continue
        # return False
