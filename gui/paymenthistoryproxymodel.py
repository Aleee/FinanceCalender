from PySide6.QtCore import QSortFilterProxyModel, Qt, QDate

from base.payment import PaymentField
from gui.common import model_atlevel
from gui.paymenthistorymodel import PaymentHistoryTableModel


class PaymentHistoryProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(PaymentHistoryProxyModel, self).__init__(parent)

        self.sort(2)
        self.setDynamicSortFilter(True)
        self.current_event_id: int = 0

    def filterAcceptsRow(self, source_row, source_parent, /):
        return model_atlevel(-1, self).index(source_row, PaymentField.EVENT, source_parent).data(PaymentHistoryTableModel.internalValueRole) == self.current_event_id

    def headerData(self, section, orientation, /, role=...):
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return section + 1
        return super().headerData(section, orientation, role)

    def reset_filter(self, event_id: int):
        self.current_event_id = event_id
        self.invalidate()

    def get_last_paymentdate(self, new_paymentdate: QDate | None) -> QDate:
        last_paymentdate: QDate = QDate()
        for row in range(self.rowCount()):
            date: QDate = self.index(row, PaymentField.PAYMENT_DATE).data(PaymentHistoryTableModel.internalValueRole)
            if date.isValid():
                if not last_paymentdate.isValid():
                    last_paymentdate = date
                else:
                    last_paymentdate = date if date > last_paymentdate else last_paymentdate
        if new_paymentdate:
            return last_paymentdate if last_paymentdate.isValid() and last_paymentdate > new_paymentdate else new_paymentdate
        else:
            return last_paymentdate
