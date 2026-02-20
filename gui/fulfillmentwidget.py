from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView

from gui.fulfillmentmodel import FulfillmentModel


class FulfillmentWidget(QTreeView):
    def __init__(self, parent=None):
        super(FulfillmentWidget, self).__init__(parent)


    def setup_rows(self):
        self.expandAll()

        model: FulfillmentModel = self.model()
        for category in model.rootItem.childItems:
            parent_index: QModelIndex = model.index(category.row(), 0, QModelIndex())
            for entry in category.childItems:
                self.setFirstColumnSpanned(entry.row(), parent_index, True)

        self.collapseAll()
