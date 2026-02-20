from PySide6.QtWidgets import QDialog

from gui.fulfillmentmodel import FulfillmentModel
from gui.ui.fulfillmentdialog_ui import Ui_FulfillmentDialog


class FulfillmentDialog(QDialog):
    def __init__(self, parent=None):
        super(FulfillmentDialog, self).__init__(parent)
        self.ui = Ui_FulfillmentDialog()
        self.ui.setupUi(self)

        self.model = FulfillmentModel(self)
        self.model.setup_model()
        self.ui.tv_fulfillment.setModel(self.model)
        self.ui.tv_fulfillment.setup_rows()
