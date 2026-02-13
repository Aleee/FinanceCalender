# Copyright © VRonin
# https://forum.qt.io/

from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QHeaderView, QStyleOptionHeader, QStyle
from PySide6.QtCore import QSize


class PersistentHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super(PersistentHeader, self).__init__(orientation, parent)

    def sizeHint(self):
        original_size = QHeaderView.sizeHint(self)
        if original_size.width() > 0 or original_size.height() > 0:
            return original_size
        self.ensurePolished()
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.section = 0
        font = QFont()
        font.setBold(True)
        opt.fontMetrics = QFontMetrics(font)
        opt.text = "0"
        if self.isSortIndicatorShown():
            opt.sortIndicator = QStyleOptionHeader().SortIndicator.SortDown
        return self.style().sizeFromContents(QStyle.ContentsType.CT_HeaderSection, opt, QSize(), self)
