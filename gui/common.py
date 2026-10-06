import lovely_logger as log

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QAbstractItemModel


def model_atlevel(relative_level: int, model_or_index: QAbstractItemModel | QModelIndex) -> QAbstractItemModel:
    model = model_or_index.model() if isinstance(model_or_index, QModelIndex) else model_or_index
    if relative_level == 0:
        return model
    elif relative_level > 0:
        message = "Аргумент relative_level принимает только отрицательные значения"
        log.x(message)
        raise ValueError(message)
    else:
        for i in range(abs(relative_level)):
            try:
                model = model.sourceModel()
            except AttributeError:
                message = f"На уровне -{i+1} модель отсутствует"
                log.x(message)
                raise ValueError(message)
        return model


def map_to_source(relative_level: int, index: QModelIndex) -> QModelIndex:
    if relative_level == 0:
        return index
    elif relative_level > 0:
        message = "Аргумент relative_level принимает только отрицательные значения"
        log.x(message)
        raise ValueError(message)
    else:
        current_model: QAbstractItemModel = index.model()
        for i in range(abs(relative_level)):
            # mapToSource — единственный вызов, которому нужна защита: именно он падает,
            # если уровней прокси меньше, чем запрошено в relative_level
            try:
                index = current_model.mapToSource(index)
            except AttributeError:
                message = f"На уровне -{i+1} модель отсутствует"
                log.x(message)
                raise ValueError(message)
            current_model = current_model.sourceModel()
        return index
