from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, Qt, QDate

from base.event import EventField, RowType
from base.payment import PaymentField
from gui.eventtablemodel import EventTableModel
from gui.paymenthistorymodel import PaymentHistoryTableModel


class PaymentHistoryProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(PaymentHistoryProxyModel, self).__init__(parent)

        self.sort(2)
        self.setDynamicSortFilter(True)

        self.current_event_id: int = 0

    def filterAcceptsRow(self, source_row, source_parent, /):
        return self.sourceModel().index(source_row, PaymentField.EVENT, source_parent).data(PaymentHistoryTableModel.internalValueRole) == self.current_event_id

    def headerData(self, section, orientation, /, role = ...):
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return section + 1
        return super().headerData(section, orientation, role)

    def reset_filter(self, event_id: int):
        self.current_event_id = event_id
        self.invalidate()
