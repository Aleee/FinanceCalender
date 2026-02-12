from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel


def model_atlevel(relative_level: int, model_or_index: QAbstractTableModel | QSortFilterProxyModel | QModelIndex | None):
    model = model_or_index.model() if type(model_or_index) is QModelIndex else model_or_index
    if relative_level == 0:
        return model
    elif relative_level > 1:
        raise ValueError("Аргумент relative_level принимает только отрицательные значения")
    else:
        for i in range(abs(relative_level)):
            model = model.sourceModel()
        return model
