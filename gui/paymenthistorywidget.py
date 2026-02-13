from PySide6 import QtWidgets
from PySide6.QtWidgets import QAbstractItemView

from base.payment import PaymentField


class PaymentHistoryTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(PaymentHistoryTableView, self).__init__(parent)

        self.setSortingEnabled(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAutoScroll(True)
        self.setAcceptDrops(False)
        self.setMouseTracking(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)

    def set_columns_visibility(self) -> None:
        for col in (PaymentField.ID, PaymentField.EVENT, PaymentField.CREATE_DATE):
            self.setColumnHidden(col, True)

    def update_column_width(self, fontsize_setting) -> None:
        column_width = (70, 80, 95)[fontsize_setting]
        self.setColumnWidth(PaymentField.PAYMENT_DATE, column_width)
