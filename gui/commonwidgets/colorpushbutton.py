from PySide6 import QtWidgets, QtGui


class ColorPushButton(QtWidgets.QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.color: str | None = None
        self.clicked.connect(self.pick_color)

    def set_color(self, color: str) -> None:
        if color != self.color:
            self.color = color
        if self.color:
            self.setStyleSheet(f"background-color: {self.color}")
        else:
            self.setStyleSheet("")

    def get_color(self) -> str | None:
        return self.color

    def pick_color(self) -> None:
        dlg: QtWidgets.QColorDialog = QtWidgets.QColorDialog(self)
        dlg.setCurrentColor(QtGui.QColor(self.color))
        self.setStyleSheet("")
        if dlg.exec_():
            self.set_color(dlg.currentColor().name())
        else:
            self.set_color(self.color)
