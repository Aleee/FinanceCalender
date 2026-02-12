from PySide6 import QtWidgets
from PySide6.QtWidgets import QAbstractItemView


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
        for col in (0, 1, 4):
            self.setColumnHidden(col, True)

    def update_column_width(self, fontsize_setting):
        column_width = (70, 80, 95)[fontsize_setting]
        self.setColumnWidth(2, column_width)
        #self.setColumnWidth(3, 75)

