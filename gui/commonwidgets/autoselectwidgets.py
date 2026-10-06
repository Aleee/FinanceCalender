from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QTimer


class AutoSelectMixin:
    def focusInEvent(self, event: QtGui.QFocusEvent) -> None:
        super().focusInEvent(event)
        # Qt сбрасывает выделение сразу после focusInEvent, поэтому
        # selectAll() вызываем отложенно, в следующем цикле событий.
        QTimer.singleShot(0, self.selectAll)


class AutoSelectSpinbox(AutoSelectMixin, QtWidgets.QSpinBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
