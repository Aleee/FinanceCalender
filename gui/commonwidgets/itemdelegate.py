from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtGui import QPainter, QColor, QPen, QPalette
from PySide6.QtCore import QModelIndex

from gui.commonwidgets.common import RowStyle
from gui.eventproxymodel import LiabilityTotalsProxyModel
from gui.eventsqlmodel import Col, RowFormatting, LiabilitySqlTableModel
from base.liability import RowType

from gui.common import model_atlevel
from gui.fulfilmentmodel import FulfilmentModel


class EventItemDelegate(QStyledItemDelegate):

    FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    BORDER_WIDTH: int = 1

    def __init__(self, parent=None):
        super(EventItemDelegate, self).__init__(parent)

    def initStyleOption(self, option, index, /):
        super(EventItemDelegate, self).initStyleOption(option, index)
        self.apply_style(option, index.data(LiabilityTotalsProxyModel.RowStyleRole))

    def apply_style(self, option, style: RowStyle):
        if not style:
            return
        if style.highlight_color:
            option.palette.setColor(
                QPalette.ColorGroup.All,
                QPalette.ColorRole.Highlight,
                style.highlight_color
            )
        if style.text_color:
            option.palette.setColor(
                QPalette.ColorGroup.All,
                QPalette.ColorRole.Text,
                style.text_color
            )
        if style.highlighted_text_color:
            option.palette.setColor(
                QPalette.ColorGroup.All,
                QPalette.ColorRole.HighlightedText,
                style.highlighted_text_color
            )
        if style.background_brush:
            option.backgroundBrush = style.background_brush

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        style: RowStyle = index.data(LiabilityTotalsProxyModel.RowStyleRole)
        super(EventItemDelegate, self).initStyleOption(option, index)
        self.apply_style(option, style)
        row_formatting: RowFormatting = model_atlevel(-2, index).row_formatting
        vertical_grid_color = self.draw_background(option, style)
        self.draw_content(painter, option, index)
        self.draw_borders(painter, option, index, row_formatting, vertical_grid_color)

    def draw_content(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)

    def draw_background(self, option, style: RowStyle):
        if not style:
            return None
        if style.background_brush:
            option.backgroundBrush = style.background_brush
        return style.vertical_grid_color

    def draw_borders(self, painter, option, index, row_formatting, vertical_grid_color):
        painter.save()
        painter.setClipRect(option.rect)
        row_type: RowType = index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole)
        if row_formatting.vertical_grid and row_type == RowType.LIABILITY:
            pen: QPen = QPen(vertical_grid_color, self.BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
            painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        elif row_type in (RowType.HEADER, RowType.FOOTER):
            pen: QPen = QPen(QColor("grey"), self.BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomRight(), option.rect.bottomLeft())
            if row_type == RowType.FOOTER and index.siblingAtColumn(Col.CATEGORY).data(LiabilitySqlTableModel.dbValueRole) % 1000 != 0:
                painter.drawLine(option.rect.topRight(), option.rect.topLeft())
        painter.restore()


class FulfillmentItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(FulfillmentItemDelegate, self).__init__(parent)

    def initStyleOption(self, option, index, /):
        super(FulfillmentItemDelegate, self).initStyleOption(option, index)

        if option.state & QStyle.StateFlag.State_Selected:
            option.state &= ~QStyle.StateFlag.State_Selected
        if option.state & QStyle.StateFlag.State_HasFocus:
            option.state &= ~QStyle.StateFlag.State_HasFocus

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        painter.save()
        painter.setClipRect(option.rect)
        pen: QPen = QPen(QColor("#b0b5e8"), 1)
        painter.setPen(pen)
        if (index.siblingAtColumn(0).data(FulfilmentModel.spanRole) and not index.sibling(index.row() + 1, 0).data(FulfilmentModel.spanRole)
                or not index.siblingAtColumn(0).data(FulfilmentModel.spanRole)):
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.restore()
