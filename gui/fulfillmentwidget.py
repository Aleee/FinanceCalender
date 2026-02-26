from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView, QAbstractItemView, QStyledItemDelegate

from gui.commonwidgets.itemdelegate import FulfillmentItemDelegate
from gui.fulfillmentmodel import FulfillmentModel


class FulfillmentWidget(QTreeView):

    COL_WIDTH = [80, 450, 110, 110, 110, 100]

    def __init__(self, parent=None):
        super(FulfillmentWidget, self).__init__(parent)

        self.header().setStretchLastSection(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.setStyleSheet("QTreeView {show-decoration-selected: 0}")
        item_delegate: QStyledItemDelegate = FulfillmentItemDelegate()
        self.setItemDelegate(item_delegate)

        self.clicked.connect(self.on_item_click)

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

    def on_item_click(self, index):
        if index.isValid():
            if self.isExpanded(index.siblingAtColumn(0)):
                self.collapse(index.siblingAtColumn(0))
            else:
                self.expand(index.siblingAtColumn(0))
