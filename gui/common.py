import lovely_logger as log
from PySide6 import QtGui, QtWidgets, QtCore

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QAbstractItemModel


def model_atlevel(relative_level: int, model_or_index: QAbstractTableModel | QAbstractItemModel | QSortFilterProxyModel | QModelIndex) \
        -> (QAbstractTableModel | QAbstractItemModel | QSortFilterProxyModel):
    model = model_or_index.model() if type(model_or_index) is QModelIndex else model_or_index
    if relative_level == 0:
        return model
    elif relative_level > 0:
        log.x("Аргумент relative_level принимает только отрицательные значения")
        raise ValueError
    else:
        for i in range(abs(relative_level)):
            model = model.sourceModel()
        return model


def map_to_source(relative_level: int, index: QModelIndex) -> QModelIndex:
    if relative_level == 0:
        return index
    elif relative_level > 0:
        raise ValueError("Аргумент relative_level принимает только отрицательные значения")
    else:
        current_model: QAbstractTableModel | QSortFilterProxyModel = index.model()
        for i in range(abs(relative_level)):
            index = current_model.mapToSource(index)
            try:
                current_model: QAbstractItemModel = current_model.sourceModel()
            except AttributeError:
                if i != abs(relative_level) - 1:
                    log.x(f"На уровне -{i+1} модель отсутствует")
                    raise ValueError
        return index
