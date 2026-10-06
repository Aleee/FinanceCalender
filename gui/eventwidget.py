from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QModelIndex, QItemSelectionModel, QTimer, Signal
from PySide6.QtGui import QPainter, QColor

from gui.common import model_atlevel
from gui.commonwidgets.eventfilter import TooltipFilter
from gui.commonwidgets.itemdelegate import EventItemDelegate
from gui.eventsqlmodel import Col, LiabilitySqlTableModel
from base.liability import RowType
from gui.booldelegate import BoolDelegate


class EventWidget(QTreeView):

    filter_conditions_changed = Signal()

    EMPTY_TABLE_TEXT = "Нет платежей, подходящих под условия фильтрации и поиска"
    EMPTY_TABLE_COLOR = "#808080"

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
        Col.LASTPAYMENTDATE: 0,
        Col.FILTERFLAGS: 0,
        Col.FEATURED: 40,
        Col.HIDDEN: 40,
        Col.RECEIVERNOCASE: 0,
    }


    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.selected_row_id: int | None = None
        self.skip_restore_selection: bool = False

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

        hidden_delegate = BoolDelegate("🔒", "⚪")
        self.setItemDelegateForColumn(Col.HIDDEN, hidden_delegate)
        hidden_delegate.state_changed.connect(lambda: self.filter_conditions_changed.emit())


    def paintEvent(self, event, /) -> None:
        super().paintEvent(event)
        if self.model() and self.model().stored_count == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(self.EMPTY_TABLE_COLOR))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.EMPTY_TABLE_TEXT)

    def hide_columns(self, to_hide: list[Col] | None = None) -> None:
        columns_to_hide: list = [key for key, val in model_atlevel(-2, self.model()).COLUMN_DATA.items() if not val[1]]
        if to_hide:
            columns_to_hide.extend(to_hide)
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
        # Каждое применение setFirstColumnSpanned() вызывает фильтрацию, поэтому на время она отключается
        model_atlevel(-1, self.model()).enable_sortfilter(False)
        try:
            for row in range(self.model().rowCount()):
                if self.model().index(row, Col.TYPE, QModelIndex()).data(LiabilitySqlTableModel.dbValueRole) == RowType.HEADER:
                    self.setFirstColumnSpanned(row, QModelIndex(), True)
        finally:
            model_atlevel(-1, self.model()).enable_sortfilter(True)

    def save_selection(self) -> None:
        selected = self.selectionModel().selectedRows()
        if selected:
            self.selected_row_id = self.model().data(self.model().index(selected[0].row(), Col.ID), LiabilitySqlTableModel.dbValueRole)
        else:
            self.selected_row_id = None

    def restore_selection(self) -> None:
        if self.skip_restore_selection:
            self.skip_restore_selection = False
            return
        if self.selected_row_id is None:
            return
        source_model = model_atlevel(-2, self.model())
        for row in range(source_model.rowCount()):
            liability_index = source_model.index(row, Col.ID)
            liability_id = liability_index.data(LiabilitySqlTableModel.dbValueRole)
            if liability_id == self.selected_row_id:
                QTimer.singleShot(0, lambda: QTimer.singleShot(0, lambda: self._apply_selection(liability_index, source_model)))
                break

    def _apply_selection(self, idx: QModelIndex, source_model: LiabilitySqlTableModel) -> None:
        if not idx.isValid():
            return
        proxy_index = self.model().mapFromSource(model_atlevel(-1, self.model()).mapFromSource(idx))
        sm = self.selectionModel()
        self.setCurrentIndex(proxy_index)
        sm.select(proxy_index, QItemSelectionModel.SelectionFlag.Rows | QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self.scrollTo(proxy_index)
