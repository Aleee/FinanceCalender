from PySide6 import QtGui
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPalette
from PySide6.QtCore import QModelIndex

from base.event import EventField, RowType, TermRoleFlags
from gui.eventmodel import EventTableModel, HeaderFooterSubtype, HeaderFooterField, RowFormatting
from gui.common import model_atlevel


class CustomDelegate(QStyledItemDelegate):

    VERTICAL_GRID_COLOR: QColor = QColor("#EEEEEE")
    ALTERNATE_ROW_COLOR: QColor = QColor("#f7f7f7")
    FINALFOOTER_BACK_COLOR: QColor = QColor("#fff9cd")
    DARKER_RATIO: int = 110
    BORDER_WIDTH: int = 1

    def __init__(self, parent=None):
        super(CustomDelegate, self).__init__(parent)

    def initStyleOption(self, option, index, /):
        super(CustomDelegate, self).initStyleOption(option, index)

        row_formatting: RowFormatting = model_atlevel(-2, index).row_formatting
        if index.siblingAtColumn(EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.EVENT:
            option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Highlight, (QColor("#CDE8FF")))
            term_flags: TermRoleFlags = index.siblingAtColumn(EventField.TERMFLAGS).data(EventTableModel.internalValueRole)
            if TermRoleFlags.DUE in term_flags:
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text,
                                        QColor(row_formatting.due_forecolor))
                option.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText,
                                        QColor(row_formatting.due_forecolor))
            elif TermRoleFlags.TODAY in term_flags:
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
            if due_backcolor_setting != QtGui.QColorConstants.White and TermRoleFlags.DUE in term_flags:
                option.backgroundBrush = QBrush(QColor(row_formatting.due_backcolor))
                vertical_grid_color = QColor(row_formatting.due_backcolor).darker(self.DARKER_RATIO)
            elif today_backcolor_setting != QtGui.QColorConstants.White and TermRoleFlags.TODAY in term_flags:
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
            if row_type == RowType.FOOTER:
                painter.drawLine(option.rect.topRight(), option.rect.topLeft())
        painter.restore()
