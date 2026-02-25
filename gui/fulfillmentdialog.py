from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog

from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.fulfillmentmodel import FulfillmentModel
from gui.ui.fulfillmentdialog_ui import Ui_FulfillmentDialog


class FulfillmentDialog(QDialog):
    def __init__(self, db_handler: DBHandler, begin_date: QDate, end_date: QDate, inflow_values: list, parent=None):
        super(FulfillmentDialog, self).__init__(parent)
        self.ui = Ui_FulfillmentDialog()
        self.ui.setupUi(self)

        self.db_handler: DBHandler = db_handler
        self.begin_date: QDate = begin_date
        self.end_date: QDate = end_date
        self.inflow_values: list = inflow_values

        values = self.db_handler.load_fulfillmentpayments_from_db(self.begin_date, self.end_date)
        if not values:
            msg_box = ErrorInfoMessageBox("Не удалось загрузить данные о платежах из базы данных (подробнее см. лог)")
            msg_box.exec()
            self.reject()
            return

        self.model: FulfillmentModel = FulfillmentModel(self)
        self.model.setup_model(values, inflow_values)
        self.ui.tv_fulfillment.setModel(self.model)
        self.ui.tv_fulfillment.setup_rows()
        self.ui.tv_fulfillment.setup_columns()
