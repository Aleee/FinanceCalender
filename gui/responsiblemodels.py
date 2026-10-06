import lovely_logger as log
from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, Qt


class ResponsibleModel(QStandardItemModel):
    def __init__(self, only_active_personal: bool = False, parent=None):
        super().__init__(parent)
        self.only_active_personal = only_active_personal

    def setup_model(self, input_dict: dict[int, tuple]):
        default_item: QStandardItem = QStandardItem("")
        default_item.setData(0, Qt.ItemDataRole.UserRole)
        self.appendRow(default_item)
        for key, tuple_val in input_dict.items():
            new_item: QStandardItem = QStandardItem(tuple_val[0])
            archived: bool = False
            try:
                if int(tuple_val[2]) == 1:
                    archived = True
            except (ValueError, IndexError, TypeError):
                log.w(f"Не удалось обработать статус архивности сотрудника {key}: {tuple_val}")
                continue
            try:
                new_item.setData(int(key), Qt.ItemDataRole.UserRole)
            except (ValueError, IndexError, TypeError):
                log.w(f"Не удалось обработать id сотрудника {key}: {tuple_val}")
                continue
            if self.only_active_personal and archived:
                continue
            self.appendRow(new_item)


class ResponsibleCategorySortModel(QSortFilterProxyModel):
    def __init__(self, freq_dict: dict[int, dict[int, int]]):
        super().__init__()
        self.freq_dict = freq_dict
        self.current_category: int | None = None

    def lessThan(self, source_left, source_right, /):
        if not self.current_category:
            return True
        if source_left.data(Qt.ItemDataRole.UserRole) == 0:
            return True
        if source_right.data(Qt.ItemDataRole.UserRole) == 0:
            return False
        category_freq = self.freq_dict.get(self.current_category, {})
        left_count = category_freq.get(source_left.data(Qt.ItemDataRole.UserRole), 0)
        right_count = category_freq.get(source_right.data(Qt.ItemDataRole.UserRole), 0)
        return left_count > right_count

    def resort(self, new_category: int):
        self.current_category = new_category
        self.invalidate()
