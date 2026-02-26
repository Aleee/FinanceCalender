from PySide6 import QtGui
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPalette
from PySide6.QtCore import QModelIndex

from base.event import EventField, RowType, TermRoleFlags
from gui.eventmodel import EventTableModel, HeaderFooterSubtype, HeaderFooterField, RowFormatting
from gui.common import model_atlevel
from gui.filterwidget import TermCategory
from gui.fulfillmentmodel import FulfillmentModel


class EventItemDelegate(QStyledItemDelegate):

    VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    ALTERNATE_ROW_COLOR: QColor = QColor("#f7f7f7")
    FINALFOOTER_BACK_COLOR: QColor = QColor("#D2DABE")
    DARKER_RATIO: int = 110
    BORDER_WIDTH: int = 1

    def __init__(self, parent=None):
        super(EventItemDelegate, self).__init__(parent)

    def initStyleOption(self, option, index, /):
        super(EventItemDelegate, self).initStyleOption(option, index)

        row_formatting: RowFormatting = model_atlevel(-2, index).row_formatting
        if not row_formatting:
            return
        if index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.EVENT:
            option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Highlight, (QColor("#CDE8FF")))
            term_flags: TermRoleFlags = index.siblingAtColumn(EventField.TERMFLAGS).data(EventTableModel.internalValueRole)
            if TermRoleFlags.DUE in term_flags and model_atlevel(-1, index).term_filter != TermCategory.DUE:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.due_forecolor))
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText,
                                        QColor(row_formatting.due_forecolor))
            elif TermRoleFlags.TODAY in term_flags and model_atlevel(-1, index).term_filter != TermCategory.TODAY:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.today_forecolor))
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText,
                                        QColor(row_formatting.today_forecolor))
            else:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText, (QColor("black")))
        elif index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.HEADER:
            subtype: HeaderFooterSubtype = index.siblingAtColumn(HeaderFooterField.SUBTYPE).data(EventTableModel.internalValueRole)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.header_section_forecolor))
            if subtype == HeaderFooterSubtype.NEXTLEVEL:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.header_subsection_forecolor))
        elif index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.FOOTER:
            row_formatting: RowFormatting = model_atlevel(-2, index).row_formatting
            subtype: HeaderFooterSubtype = index.siblingAtColumn(HeaderFooterField.SUBTYPE).data(EventTableModel.internalValueRole)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.footer_section_forecolor))
            if subtype == HeaderFooterSubtype.NEXTLEVEL:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.footer_subsection_forecolor))


    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        self.initStyleOption(option, index)
        row_formatting: RowFormatting = model_atlevel(-2, index).row_formatting

        row_type: RowType = index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole)
        if row_type == RowType.EVENT:
            term_flags: TermRoleFlags = index.siblingAtColumn(EventField.TERMFLAGS).data(EventTableModel.internalValueRole)
            due_backcolor_setting: QColor = QColor(row_formatting.due_backcolor)
            today_backcolor_setting: QColor = QColor(row_formatting.today_backcolor)
            vertical_grid_color: QColor = self.VERTICAL_GRID_COLOR
            if due_backcolor_setting != QtGui.QColorConstants.White and TermRoleFlags.DUE in term_flags and model_atlevel(-1, index).term_filter != TermCategory.DUE:
                option.backgroundBrush = QBrush(QColor(row_formatting.due_backcolor))
                vertical_grid_color = QColor(row_formatting.due_backcolor).darker(self.DARKER_RATIO)
            elif today_backcolor_setting != QtGui.QColorConstants.White and TermRoleFlags.TODAY in term_flags and model_atlevel(-1, index).term_filter != TermCategory.TODAY:
                option.backgroundBrush = QBrush(QColor(row_formatting.today_backcolor))
                vertical_grid_color: QColor = QColor(row_formatting.today_backcolor).darker(self.DARKER_RATIO)
            else:
                if row_formatting.zebra_style and index.row() % 2 == 0:
                    option.backgroundBrush = QBrush(self.ALTERNATE_ROW_COLOR)
                else:
                    option.backgroundBrush = QBrush(QColor("#FFFFFF"))

        elif row_type == RowType.HEADER:
            subtype: HeaderFooterSubtype = index.siblingAtColumn(HeaderFooterField.SUBTYPE).data(EventTableModel.internalValueRole)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                option.backgroundBrush = QBrush(QColor(row_formatting.header_section_backcolor))
            if subtype == HeaderFooterSubtype.NEXTLEVEL:
                option.backgroundBrush = QBrush(QColor(row_formatting.header_subsection_backcolor))

        elif row_type == RowType.FOOTER:
            row_formatting = model_atlevel(-2, index).row_formatting
            subtype: HeaderFooterSubtype = index.siblingAtColumn(HeaderFooterField.SUBTYPE).data(EventTableModel.internalValueRole)
            if subtype in (HeaderFooterSubtype.TOPLEVELNOEVENTS, HeaderFooterSubtype.TOPLEVELWITHEVENTS):
                option.backgroundBrush = QBrush(QColor(row_formatting.footer_section_backcolor))
            if subtype == HeaderFooterSubtype.NEXTLEVEL:
                option.backgroundBrush = QBrush(QColor(row_formatting.footer_subsection_backcolor))

        elif row_type == RowType.FINALFOOTER:
            option.backgroundBrush = QBrush(self.FINALFOOTER_BACK_COLOR)

        option.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)

        # Отрисовка границ ПОСЛЕ отрисовки стандартного делегата
        painter.save()
        painter.setClipRect(option.rect)
        row_type: RowType = index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole)
        if row_formatting.vertical_grid and row_type == RowType.EVENT:
            pen: QPen = QPen(vertical_grid_color, self.BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawLine(option.rect.topLeft(), option.rect.bottomLeft())
            painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        elif row_type in (RowType.HEADER, RowType.FOOTER):
            pen: QPen = QPen(QColor("grey"), self.BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomRight(), option.rect.bottomLeft())
            if row_type == RowType.FOOTER and index.siblingAtColumn(EventField.CATEGORY).data(EventTableModel.internalValueRole) % 1000 != 0:
                pen.setWidth(self.BORDER_WIDTH)
                painter.setPen(pen)
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
        super(FulfillmentItemDelegate, self).initStyleOption(option, index)
        super().paint(painter, option, index)

        painter.save()
        painter.setClipRect(option.rect)
        pen: QPen = QPen(QColor("#b0b5e8"), 1)
        painter.setPen(pen)
        if (index.siblingAtColumn(0).data(FulfillmentModel.spanRole) and not index.sibling(index.row() + 1, 0).data(FulfillmentModel.spanRole)
                or not index.siblingAtColumn(0).data(FulfillmentModel.spanRole)):
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        painter.restore()
