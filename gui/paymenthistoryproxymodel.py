from PySide6.QtCore import QSortFilterProxyModel, Qt


class PaymentHistoryProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(PaymentHistoryProxyModel, self).__init__(parent)

        self.sort(2)
        self.setDynamicSortFilter(True)
        self.current_event_id: int = 0


    def headerData(self, section, orientation, /, role=...):
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return section + 1
        return super().headerData(section, orientation, role)
