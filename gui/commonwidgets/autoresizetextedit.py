# Copyright © Kamil Śliwak
# https://github.com/cameel/
# Released under the MIT License

from PySide6.QtWidgets import QTextEdit, QSizePolicy
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import QSize, QMargins


class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(AutoResizingTextEdit, self).__init__(parent)

        size_policy: QSizePolicy = self.sizePolicy()
        size_policy.setHeightForWidth(True)
        size_policy.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        self.setSizePolicy(size_policy)

        self.textChanged.connect(lambda: self.updateGeometry())

    def setMinimumLines(self, num_lines):
        self.setMinimumSize(self.minimumSize().width(), self.lineCountToWidgetHeight(num_lines))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        margins: QMargins = self.contentsMargins()

        if width >= margins.left() + margins.right():
            document_width: int = width - margins.left() - margins.right()
        else:
            document_width: int = 0

        document = self.document().clone()
        document.setTextWidth(document_width)

        return margins.top() + document.size().height() + margins.bottom()

    def sizeHint(self):
        original_hint: QSize = super(AutoResizingTextEdit, self).sizeHint()
        return QSize(original_hint.width(), self.heightForWidth(original_hint.width()))

    def lineCountToWidgetHeight(self, num_lines):

        assert num_lines >= 0

        widget_margins: QMargins = self.contentsMargins()
        document_margin: float = self.document().documentMargin()
        font_metrics: QFontMetrics = QFontMetrics(self.document().defaultFont())

        return (
            widget_margins.top() +
            document_margin +
            max(num_lines, 1) * font_metrics.height() +
            self.document().documentMargin() +
            widget_margins.bottom()
        )
