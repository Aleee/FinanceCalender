from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal


class ColorPushButton(QtWidgets.QPushButton):

    color_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.color: str | None = None
        self.clicked.connect(self.pick_color)

    def set_color(self, color: str | None) -> None:
        self.color = color
        if self.color:
            self.setStyleSheet(f"background-color: {self.color}")
            self.setToolTip(f"{self.color} — нажмите, чтобы изменить")
        else:
            self.setStyleSheet("")
            self.setToolTip("Нажмите, чтобы выбрать цвет")
        self.color_changed.emit()

    def get_color(self) -> str | None:
        return self.color

    def pick_color(self) -> None:
        dlg = QtWidgets.QColorDialog(self.window())
        dlg.setCurrentColor(QtGui.QColor(self.color))
        if dlg.exec():
            self.set_color(dlg.currentColor().name())
