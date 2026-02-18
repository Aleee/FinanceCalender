from PySide6.QtCore import QObject, QEvent, Qt, Signal, QPoint, QModelIndex, QRect
from PySide6.QtWidgets import QApplication, QAbstractItemView, QToolTip


class RightClickFilter(QObject):

    rightmousebutton_clicked = Signal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                self.rightmousebutton_clicked.emit()
        return super().eventFilter(obj, event)


class TooltipFilter(QObject):

    def __init__(self, view: QAbstractItemView):
        super().__init__()
        self.view = view

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ToolTip:
            position: QPoint = self.view.viewport().mapFromGlobal(event.globalPos())
            index: QModelIndex = self.view.indexAt(position)
            if not index.isValid():
                return False
            value = index.data(Qt.ItemDataRole.DisplayRole)
            value_width: int = self.view.fontMetrics().boundingRect(value).width()
            rect: QRect = self.view.visualRect(index)
            rect_width: int = rect.width()
            if value_width > rect_width - 10:
                QToolTip.showText(event.globalPos(), value, self.view, rect)
            else:
                QToolTip.hideText()
        return False
