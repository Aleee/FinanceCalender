from PySide6 import QtWidgets
from PySide6.QtCore import QTimer


class AutoSelectMixin:
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)


class AutoSelectSpinbox(AutoSelectMixin, QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
