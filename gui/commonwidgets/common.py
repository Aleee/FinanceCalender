from PySide6.QtCore import QSortFilterProxyModel, QModelIndex
from PySide6.QtWidgets import QTreeView, QTableView


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
