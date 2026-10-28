from PySide6.QtCore import QTimer
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import QSplitter


class BottomFirstSplitter(QSplitter):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wanted_top: int | None = None
        self.wanted_bottom: int | None = None
        self.splitterMoved.connect(self.remember_sizes)

    def remember_sizes(self) -> None:
        self.wanted_top, self.wanted_bottom = self.sizes()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self.wanted_bottom is None:
            QTimer.singleShot(0, self.remember_sizes)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.wanted_bottom is None or not self.isVisible():
            return
        total: int = sum(self.sizes())
        bottom_minimum: int = self.widget(1).minimumSizeHint().height()
        bottom: int = min(self.wanted_bottom, max(bottom_minimum, total - self.wanted_top))
        self.setSizes([total - bottom, bottom])
