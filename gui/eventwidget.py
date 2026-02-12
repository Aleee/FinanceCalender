from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QModelIndex

from base.event import EventField
from gui.eventtablemodel import EventTableModel
from gui.eventproxymodel import EventListProxyModel
from gui.itemdelegate import CustomDelegate


class EventWidget(QTreeView):

    DEFAULT_COLUMN_WIDTH = {
        EventField.RECEIVER: 140,
        EventField.TYPE: 0,
        EventField.ID: 0,
        EventField.CATEGORY: 0,
        EventField.NAME: 400,
        EventField.REMAINAMOUNT: 100,
        EventField.TOTALAMOUNT: 122,
        EventField.PERCENTAGE: 105,
        EventField.DUEDATE: 125,
        EventField.PAYMENTTYPE: 100,
        EventField.CREATEDATE: 125,
        EventField.DESCR: 300,
        EventField.RESPONSIBLE: 175,
        EventField.TODAYSHARE: 135,
        EventField.TERMFLAGS: 0,
        EventField.NOTES: 0,
        EventField.LASTPAYMENTDATE: 0,
    }

    COLUMNS_HIDDEN_BYDEFAULT = [EventField.TYPE, EventField.ID, EventField.CATEGORY, EventField.TERMFLAGS,
                                EventField.PERCENTAGE, EventField.CREATEDATE, EventField.NOTES, EventField.LASTPAYMENTDATE]

    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.header().setFirstSectionMovable(False)
        self.header().setStretchLastSection(False)
        self.header().setTextElideMode(Qt.TextElideMode.ElideRight)

        self.setItemDelegate(CustomDelegate())

    def set_columns_visibility(self, to_hide: list) -> None:
        columns_to_hide: list = self.COLUMNS_HIDDEN_BYDEFAULT.copy()
        if to_hide:
            columns_to_hide.extend(to_hide)
        # Сперва все столбцы восстанавливаются (скрытые - с шириной по умолчанию)
        for col in range(self.model().sourceModel().sourceModel().columnCount()):
            self.setColumnHidden(col, False)
            if self.columnWidth(col) == 0:
                self.setColumnWidth(col, self.DEFAULT_COLUMN_WIDTH[col])
        # Затем скрываются по новому списку
        for col in columns_to_hide:
            self.setColumnHidden(col, True)

    def get_columnvisibility_list(self) -> list[bool]:
        return [not self.isColumnHidden(col) for col in range(self.model().sourceModel().sourceModel().columnCount())]

    def set_eventlistmodel(self, model: EventListProxyModel) -> bool:
        if model:
            self.setModel(model)
            if len(self.DEFAULT_COLUMN_WIDTH) != self.model().sourceModel().sourceModel().column_count:
                raise ValueError("Количество столбцов в модели и в отображении не совпадает")
            return True
        else:
            return False

    def regain_state_after_model_changes(self):
        # Каждое применение setFirstColumnSpanned() вызывает фильтрацию, поэтому на время она отключается
        self.model().sourceModel().enable_sortfilter(False)
        for row in range(self.model().rowCount()):
            if self.model().index(row, 0, QModelIndex()).data(EventTableModel.customSpanRole):
                self.setFirstColumnSpanned(row, QModelIndex(), True)
        self.model().sourceModel().enable_sortfilter(True)
