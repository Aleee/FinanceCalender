from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QModelIndex, QItemSelectionModel, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QShortcut, QKeySequence

from gui.commonwidgets.eventfilter import TooltipFilter
from gui.commonwidgets.itemdelegate import EventItemDelegate
from gui.liabilitytablemodel import LiabilityTableModel
from base.edition import is_viewer
from base.liability import Col
from gui.booldelegate import BoolDelegate


class EventWidget(QTreeView):

    filter_conditions_changed = Signal()

    EMPTY_TABLE_TEXT = "Нет платежей, подходящих под условия фильтрации и поиска"
    EMPTY_TABLE_COLOR = "#666666"

    DEFAULT_COLUMN_WIDTH = {
        Col.RECEIVER: 140,
        Col.ID: 0,
        Col.TYPE: 0,
        Col.CONTRACTDOCUMENTID: 0,
        Col.CATEGORY: 0,
        Col.SUBCATEGORY: 0,
        Col.NAME: 400,
        Col.REMAINAMOUNT: 100,
        Col.TOTALAMOUNT: 122,
        Col.NDS: 0,
        Col.DUEDATE: 125,
        Col.INCURRENCEDATE: 125,
        Col.PAYMENTTYPE: 100,
        Col.DESCR: 300,
        Col.RESPONSIBLE: 175,
        Col.NOTES: 0,
        Col.TODAYSHARE: 135,
        Col.LASTPAYMENTDATE: 100,
        Col.FILTERFLAGS: 0,
        Col.FEATURED: 40,
        Col.HIDDEN: 40,
    }


    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.selected_row_id: int | None = None
        self.skip_restore_selection: bool = False
        self.paid_mode: bool = False
        self.user_hidden_columns: list[Col] = []

        self.setUniformRowHeights(True)
        self.setRootIsDecorated(False)
        self.setAllColumnsShowFocus(True)
        self.setSortingEnabled(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setItemsExpandable(False)
        self.setAutoScroll(True)
        self.setAcceptDrops(False)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.header().setFirstSectionMovable(False)
        self.header().setStretchLastSection(False)
        self.header().setTextElideMode(Qt.TextElideMode.ElideRight)

        self.tooltip_eventfilter = TooltipFilter(self)
        self.installEventFilter(self.tooltip_eventfilter)

        self.setItemDelegate(EventItemDelegate())

        star_delegate = BoolDelegate("★", "☆", "#ffcc00", "#857f67")
        self.setItemDelegateForColumn(Col.FEATURED, star_delegate)
        star_delegate.state_changed.connect(lambda: self.filter_conditions_changed.emit())

        hidden_delegate = BoolDelegate("🔒", "·", "", "#c8c8c8")
        self.setItemDelegateForColumn(Col.HIDDEN, hidden_delegate)
        hidden_delegate.state_changed.connect(lambda: self.filter_conditions_changed.emit())

        if not is_viewer():
            for key, column in (("Space", Col.FEATURED), ("Ctrl+H", Col.HIDDEN)):
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
                shortcut.activated.connect(lambda col=column: self.toggle_flag(col))

    def toggle_flag(self, column: Col) -> None:
        index = self.currentIndex().siblingAtColumn(column)
        if index.isValid():
            self.itemDelegateForColumn(column).toggle(self.model(), index)


    def paintEvent(self, event, /) -> None:
        super().paintEvent(event)
        if self.model() and self.model().stored_count == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(self.EMPTY_TABLE_COLOR))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.EMPTY_TABLE_TEXT)

    def setModel(self, model) -> None:
        super().setModel(model)
        header = self.header()
        header.moveSection(header.visualIndex(Col.LASTPAYMENTDATE), header.visualIndex(Col.REMAINAMOUNT))

    def set_paid_mode(self, paid_mode: bool) -> None:
        if paid_mode == self.paid_mode:
            return
        old_column, new_column = (Col.REMAINAMOUNT, Col.LASTPAYMENTDATE) if paid_mode else (Col.LASTPAYMENTDATE, Col.REMAINAMOUNT)
        width = self.columnWidth(old_column)
        self.paid_mode = paid_mode
        self.hide_columns()
        if width > 0:
            self.setColumnWidth(new_column, width)

    def hide_columns(self, to_hide: list[Col] | None = None) -> None:
        if to_hide is not None:
            self.user_hidden_columns = list(to_hide)
        columns_to_hide: list = [key for key, val in self.model().COLUMN_DATA.items() if not val[1]]
        if is_viewer():
            columns_to_hide.extend((Col.FEATURED, Col.HIDDEN))
        columns_to_hide.extend(self.user_hidden_columns)
        if self.paid_mode:
            columns_to_hide = [col for col in columns_to_hide if col != Col.LASTPAYMENTDATE]
            columns_to_hide.append(Col.REMAINAMOUNT)
        # Сперва все столбцы восстанавливаются (скрытые - с шириной по умолчанию)
        for col in range(self.model().columnCount()):
            self.setColumnHidden(col, False)
            if self.columnWidth(col) == 0:
                self.setColumnWidth(col, self.DEFAULT_COLUMN_WIDTH[col])
        # Затем скрываются по новому списку
        for col in columns_to_hide:
            self.setColumnHidden(col, True)

    def get_columnvisibility_list(self) -> list[bool]:
        return [not self.isColumnHidden(col) for col in range(self.model().columnCount())]

    def span_columns(self) -> None:
        for row in self.model().header_rows():
            self.setFirstColumnSpanned(row, QModelIndex(), True)

    def save_selection(self) -> None:
        selected = self.selectionModel().selectedRows()
        if selected:
            self.selected_row_id = self.model().data(self.model().index(selected[0].row(), Col.ID), LiabilityTableModel.dbValueRole)
        else:
            self.selected_row_id = None

    def restore_selection(self) -> None:
        if self.skip_restore_selection:
            self.skip_restore_selection = False
            return
        if self.selected_row_id is None:
            return
        selected_row_id = self.selected_row_id
        QTimer.singleShot(0, lambda: QTimer.singleShot(0, lambda: self._apply_selection(selected_row_id)))

    def _apply_selection(self, event_id: int) -> None:
        proxy_index = self.model().index_by_id(event_id)
        if not proxy_index.isValid():
            return
        sm = self.selectionModel()
        self.setCurrentIndex(proxy_index)
        sm.select(proxy_index, QItemSelectionModel.SelectionFlag.Rows | QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self.scrollTo(proxy_index)
