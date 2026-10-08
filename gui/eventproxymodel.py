import re
from decimal import Decimal, InvalidOperation
from enum import IntEnum, auto
from typing import Any

from PySide6 import QtGui
from PySide6.QtCore import QSortFilterProxyModel, QDate, Qt, Signal
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QApplication

from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, LiabilityCategory, FilterFlags, RowType, HeaderFooterSubtype, TermCategory,
                             category_section, is_top_level_category, matches_filters, paid_threshold)
from gui.common import model_atlevel
from gui.commonwidgets.common import RowStyle
from gui.eventsqlmodel import Col, LiabilitySqlTableModel


class Filter(IntEnum):
    TERM = auto()
    CATEGORY = auto()
    HEADER = auto()
    FOOTER = auto()
    PAYTODAY = auto()
    SEARCH = auto()


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
        self.search_filter: str = ""
        self.receiver_filter: str = ""
        self.responsible_filter: int = 0
        self.featured_filter: bool = False
        self.paid_months_filter: int = 3
        self.exclude_hidden: bool = False

        self.accepted_ids: set[int] | None = None
        self.cache: dict | None = None

        self.style_cache = {}
        self.modelReset.connect(self.invalidate_style_cache)
        self.dataChanged.connect(self.invalidate_style_cache)

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

        elif row_type == RowType.HEADER:
            subtype: HeaderFooterSubtype = base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.header_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_section_backcolor))
            elif subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.header_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.header_subsection_backcolor))
            style.font_bold = row_formatting.header_textbold

        elif row_type == RowType.FOOTER:
            subtype: HeaderFooterSubtype = (base_model.index(source_index.row(), Col.SUBCATEGORY).data(db_role))
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                style.text_color = QColor(row_formatting.footer_section_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_section_backcolor))
            elif subtype == HeaderFooterSubtype.ORDINARY:
                style.text_color = QColor(row_formatting.footer_subsection_forecolor)
                style.background_brush = QBrush(QColor(row_formatting.footer_subsection_backcolor))
            style.font_bold = row_formatting.footer_textbold

        elif row_type == RowType.FINALFOOTER:
            style.background_brush = QBrush(self.FINALFOOTER_BACK_COLOR)
            style.font_bold = True

        return style

    def setSourceModel(self, source_model) -> None:
        source_model.modelAboutToBeReset.connect(self.invalidate_accepted)
        source_model.dataChanged.connect(self.invalidate_accepted)
        source_model.rowsInserted.connect(self.invalidate_accepted)
        source_model.rowsRemoved.connect(self.invalidate_accepted)
        super().setSourceModel(source_model)

    def invalidate_accepted(self, *_) -> None:
        self.accepted_ids = None
        self.cache = None

    def build_accepted(self) -> None:
        accepted_ids: set[int] = set()
        cache: dict = {}
        threshold = paid_threshold(self.sourceModel().current_date, self.paid_months_filter)
        for event_id, liability in self.sourceModel().liability_rows().items():
            if self.exclude_hidden and liability.hidden:
                continue
            if not matches_filters(liability, self.term_filter, self.category_filter, self.receiver_filter,
                                   self.responsible_filter, self.paytoday_filter, self.featured_filter, threshold):
                continue
            accepted_ids.add(event_id)
            group = category_section(liability.category)
            cache[liability.category] = cache.get(liability.category, 0) + 1
            cache[group] = cache.get(group, 0) + 1
        self.accepted_ids = accepted_ids
        self.cache = cache

    def category_count(self, category: int) -> int:
        if self.cache is None:
            self.build_accepted()
        return self.cache.get(category, 0)

    def set_filters(self, term: TermCategory, category: int, receiver: str, responsible: int, paid_today: bool,
                    paid_months_toshow: int, featured: bool) -> None:
        self.term_filter = term
        self.category_filter = category
        self.receiver_filter = receiver.lower()
        self.responsible_filter = responsible
        self.paytoday_filter = paid_today
        self.paid_months_filter = paid_months_toshow
        self.featured_filter = featured
        self.invalidate_accepted()
        self.invalidate_style_cache()
        if self.sortfilter_enabled:
            self.invalidate()
            self.modelInvalidated.emit()

    def set_hidden_filter(self, exclude_hidden: bool) -> None:
        self.exclude_hidden = exclude_hidden
        self.invalidate_accepted()
        self.invalidate()

    def enable_sortfilter(self, enable: bool) -> None:
        self.sortfilter_enabled = enable

    def set_filter(self, filter_type: int, condition: str | int | bool, invalidate: bool = True) -> None:
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
        elif filter_type == Filter.SEARCH:
            self.search_filter = str(condition).strip().lower()
        if filter_type in (Filter.TERM, Filter.CATEGORY, Filter.PAYTODAY):
            self.invalidate_accepted()
        if self.sortfilter_enabled and invalidate:
            self.invalidate()
            self.modelInvalidated.emit()

    def data(self, index, /, role=...):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.FontRole:
            font_bold = self.style_data(index.row()).font_bold
            if font_bold is not None:
                font = QFont()
                font.setBold(font_bold)
                return font

        elif role == self.styleRole:
            return self.style_data(index.row())

        return QSortFilterProxyModel.data(self, index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.sortfilter_enabled:
            return True

        source_model = self.sourceModel()

        def data_from_row(column: int, role=LiabilitySqlTableModel.dbValueRole) -> Any:
            return source_model.index(source_row, column, source_parent).data(role)

        row_type: RowType = source_model.raw_value(source_row, Col.TYPE)

        ### Быстрый поиск по наименованию и основанию платежа
        if self.search_filter:
            if row_type == RowType.LIABILITY:
                haystack: str = f"{data_from_row(Col.NAME)} {data_from_row(Col.DESCR)}".lower()
                if self.search_filter not in haystack:
                    return False
            elif row_type in (RowType.HEADER, RowType.FOOTER):
                return False

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

        if self.accepted_ids is None:
            self.build_accepted()
        return source_model.raw_value(source_row, Col.ID) in self.accepted_ids

    def lessThan(self, source_left, source_right, /):
        model = self.sourceModel()
        keys = model.row_sort_keys
        left_key = keys.get(source_left.row()) or model.sort_key(source_left.row())
        right_key = keys.get(source_right.row()) or model.sort_key(source_right.row())
        return left_key < right_key


class LiabilityTotalsProxyModel(QSortFilterProxyModel):

    TOTAL_CATEGORY = 9999
    TOTAL_COLUMNS = (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)

    decimalValueRole: int = Qt.ItemDataRole.UserRole + 4
    RowStyleRole: int = LiabilitySortFilterProxyModel.styleRole

    def __init__(self, parent=None):
        super(LiabilityTotalsProxyModel, self).__init__(parent)

        self.setDynamicSortFilter(True)

        self.stored_total = dict()
        self.stored_remain = dict()
        self.stored_today = dict()
        self.stored_count: int = 0

    def recalculate_totals(self) -> None:
        for stored_dict in self.stored_total, self.stored_remain, self.stored_today:
            for category in LiabilityCategory:
                stored_dict[category] = 0
            stored_dict[self.TOTAL_CATEGORY] = 0
        self.stored_count = 0

        base_model: LiabilitySqlTableModel = model_atlevel(-2, self)
        liability_rows = base_model.liability_rows()
        event_columns = base_model.event_columns()
        for row in range(self.rowCount()):
            event_id: int = self.index(row, Col.ID).data(LiabilitySqlTableModel.dbValueRole)
            liability = liability_rows.get(event_id)
            if liability is None:
                continue
            self.stored_count += 1
            category, _, _, _, _, total, _ = event_columns[event_id]
            try:
                totalamount: Decimal = Decimal(total)
            except (InvalidOperation, TypeError):
                totalamount = Decimal(0)
            self.stored_total[category] += totalamount
            self.stored_remain[category] += liability.remain
            self.stored_today[category] += liability.today_share
        for stored_dict in self.stored_total, self.stored_remain, self.stored_today:
            total_total: Decimal = Decimal(0)
            for category in stored_dict.keys():
                if is_top_level_category(category):
                    category_prefix: int = category_section(category)
                    running_total: Decimal = Decimal(0)
                    for key, value in stored_dict.items():
                        if category_section(key) == category_prefix:
                            running_total += value
                    stored_dict[category] = running_total
                if category != LiabilityCategory.TOP_CURRENT:
                    total_total += stored_dict[category]
            stored_dict[self.TOTAL_CATEGORY] = total_total
        self.layoutChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent, /):
        if model_atlevel(-1, self).index(source_row, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.FINALFOOTER:
            return self.has_visible_liabilities()
        category: int = self.sourceModel().index(source_row, Col.CATEGORY, source_parent).data(LiabilitySqlTableModel.dbValueRole)
        if category:
            return self.category_not_empty(category, category == LiabilityCategory.TOP_CURRENT)
        else:
            return False

    def has_visible_liabilities(self) -> bool:
        proxy = self.sourceModel()
        for row in range(proxy.rowCount()):
            if proxy.index(row, Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) == RowType.LIABILITY:
                return True
        return False

    def data(self, index, /, role=...):
        if index.column() not in self.TOTAL_COLUMNS:
            return QSortFilterProxyModel.data(self, index, role)
        if role == Qt.ItemDataRole.FontRole:
            if index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) in (RowType.FOOTER, RowType.FINALFOOTER):
                if index.column() in self.TOTAL_COLUMNS:
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
            subcategory_prefix: int = category_section(category)
            return model_atlevel(-1, self).category_count(subcategory_prefix) > 0
        else:
            return model_atlevel(-1, self).category_count(category) > 0
