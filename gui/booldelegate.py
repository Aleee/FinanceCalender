from typing import Any

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor

from gui.commonwidgets.itemdelegate import EventItemDelegate
from gui.eventsqlmodel import Col, LiabilitySqlTableModel
from base.liability import RowType


class BoolDelegate(EventItemDelegate):

    state_changed = Signal()

    def __init__(self, check_symbol: str, uncheck_symbol: str = "", check_color: str = "", uncheck_color: str = "", parent=None):
        super().__init__(parent)
        self.check_symbol = check_symbol
        self.uncheck_symbol = uncheck_symbol
        self.check_color = check_color
        self.uncheck_color = uncheck_color

    def draw_content(self, painter, option, index):
        if index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.qtValueRole) == RowType.LIABILITY:
            value: Any = index.data(Qt.ItemDataRole.EditRole)
            checked = bool(value)
            if checked:
                symbol: str = self.check_symbol
                if self.check_color:
                    painter.setPen(QColor(self.check_color))
            else:
                symbol: str = self.uncheck_symbol if self.uncheck_symbol else self.check_symbol
                if self.uncheck_color:
                    painter.setPen(QColor(self.uncheck_color))
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, symbol)
        else:
            super().draw_content(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonPress and index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.qtValueRole) == RowType.LIABILITY:
            current: bool = bool(index.data(Qt.ItemDataRole.EditRole))
            new_value: int = 0 if current else 1
            model.setData(index, new_value, Qt.ItemDataRole.EditRole)
            self.state_changed.emit()
            return True
        return super().editorEvent(event, model, option, index)
