from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView, QAbstractItemView

from gui.commonwidgets.nohighlightdelegate import NoHighlightItemDelegate
from gui.fulfillmentmodel import FulfillmentModel


class FulfillmentWidget(QTreeView):

    COL_WIDTH = [500, 100, 100, 80, 80]

    def __init__(self, parent=None):
        super(FulfillmentWidget, self).__init__(parent)

        self.header().setStretchLastSection(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        no_highlight_delegate = NoHighlightItemDelegate()
        self.setItemDelegate(no_highlight_delegate)
        self.setStyleSheet("QTreeView {show-decoration-selected: 0}")


    def setup_rows(self):
        self.expandAll()

        model: FulfillmentModel = self.model()
        for category in model.rootItem.childItems:
            parent_index: QModelIndex = model.index(category.row(), 0, QModelIndex())
            for entry in category.childItems:
                self.setFirstColumnSpanned(entry.row(), parent_index, True)

        self.collapseAll()

    def setup_columns(self):
        for col in range(self.model().rootItem.columnCount()):
            self.setColumnWidth(col, self.COL_WIDTH[col])
