from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QTableView, QStyledItemDelegate, QLineEdit, QHeaderView, QWidget, QStyleOptionViewItem,
)

from base.casting import str_int
from gui.commonwidgets.eventfilter import TooltipFilter
from gui.settings import SettingsHandler


class SimpleDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QLineEdit:
        return QLineEdit(parent)


class FinPlanTableView(QTableView):

    COLUMN_WIDTH = {
        0: 75,
        1: 85,
        2: 95,
    }

    def __init__(self, parent=None):
        super(FinPlanTableView, self).__init__(parent)

        self.tooltip_eventfilter: TooltipFilter = TooltipFilter(self)
        self.installEventFilter(self.tooltip_eventfilter)
        self.setItemDelegate(SimpleDelegate(self))

    def adjust_columns(self, sh: SettingsHandler) -> None:
        fontsize_index = str_int(sh.settings.value("Appearance/fontsize"), 0)
        column_width = self.COLUMN_WIDTH.get(fontsize_index, self.COLUMN_WIDTH[0])
        for col in range(self.model().columnCount()):
            self.setColumnWidth(col, 250 if col == 0 else column_width)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            indexes = self.selectionModel().selectedIndexes()
            if indexes:
                self.model().clear_values(indexes)
        super().keyPressEvent(event)
