from dataclasses import dataclass

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QTreeView, QTableView, QFrame


@dataclass(slots=True)
class RowStyle:
    text_color: QColor | None = None
    highlighted_text_color: QColor | None = None
    highlight_color: QColor | None = None
    background_brush: QBrush | None = None
    vertical_grid_color: QColor | None = None
    font_bold: bool | None = None


class StatusBarSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)  # вертикальная линия
        self.setFrameShadow(QFrame.Shadow.Sunken)  # стиль тени
        self.setLineWidth(1)


def is_selection_filteredout(proxy_model: QSortFilterProxyModel, widget: QTreeView | QTableView, two_proxies: bool = False, current_instead: bool = False) -> bool:
    filteredout: bool = False
    if not current_instead:
        s_indexes: list = widget.selectionModel().selectedIndexes()
        try:
            s_index: QModelIndex = s_indexes[0]
        except IndexError:
            return True
    else:
        s_index: QModelIndex = widget.selectionModel().currentIndex()
    if not s_index:
        filteredout = True
    if two_proxies:
        middleproxy_index = proxy_model.mapToSource(s_index)
        origin_index = proxy_model.sourceModel().mapToSource(middleproxy_index)
        back_middleproxy_index = proxy_model.sourceModel().mapFromSource(origin_index)
        back_finalproxy_index = proxy_model.mapFromSource(back_middleproxy_index)
        if not back_finalproxy_index.isValid():
            filteredout = True
    else:
        origin_index = proxy_model.mapToSource(s_index)
        back_proxy_index = proxy_model.mapFromSource(origin_index)
        if not back_proxy_index.isValid():
            filteredout = True
    return filteredout
