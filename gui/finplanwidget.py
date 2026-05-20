from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView, QStyledItemDelegate, QLineEdit, QHeaderView

from gui.commonwidgets.eventfilter import TooltipFilter
from gui.settings import SettingsHandler


class SimpleDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
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

    def adjust_columns(self, sh: SettingsHandler):
        for col in range(self.model().columnCount()):
            self.setColumnWidth(col, self.COLUMN_WIDTH[int(sh.settings.value("Appearance/fontsize"))] if col != 0 else 250)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(20)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            indexes = self.selectionModel().selectedIndexes()
            if indexes:
                model = self.model()
                for index in indexes:
                    model.setData(index,None, Qt.ItemDataRole.EditRole)
        super().keyPressEvent(event)
