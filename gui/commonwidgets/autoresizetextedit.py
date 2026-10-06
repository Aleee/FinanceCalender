# Copyright © Kamil Śliwak
# https://github.com/cameel/
# Released under the MIT License

from PySide6.QtWidgets import QTextEdit, QSizePolicy
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import QSize, QMargins


class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        size_policy: QSizePolicy = self.sizePolicy()
        size_policy.setHeightForWidth(True)
        size_policy.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        self.setSizePolicy(size_policy)

        self.textChanged.connect(self.updateGeometry)

    def setMinimumLines(self, num_lines: int) -> None:
        self.setMinimumSize(self.minimumSize().width(), self.lineCountToWidgetHeight(num_lines))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        margins: QMargins = self.contentsMargins()

        document_width: int = 0
        if width >= margins.left() + margins.right():
            document_width = width - margins.left() - margins.right()

        document = self.document().clone()
        document.setTextWidth(document_width)

        return int(margins.top() + document.size().height() + margins.bottom())

    def sizeHint(self) -> QSize:
        original_hint: QSize = super().sizeHint()
        return QSize(original_hint.width(), self.heightForWidth(original_hint.width()))

    def lineCountToWidgetHeight(self, num_lines: int) -> int:
        if num_lines < 0:
            raise ValueError("num_lines must be >= 0")

        widget_margins: QMargins = self.contentsMargins()
        document_margin: float = self.document().documentMargin()
        font_metrics: QFontMetrics = QFontMetrics(self.document().defaultFont())

        return int(
            widget_margins.top() +
            document_margin +
            max(num_lines, 1) * font_metrics.height() +
            document_margin +
            widget_margins.bottom()
        )
