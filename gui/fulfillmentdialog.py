from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog

from base.dbhandler import DBHandler
from base.xlswriter import FulfilmentXlsWriter, ExportFormat
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.exportsuccessdialog import ExportSuccessDialog
from gui.fulfilmentmodel import FulfilmentModel
from gui.settings import SettingsHandler
from gui.ui.fulfillmentdialog_ui import Ui_FulfillmentDialog


class FulfillmentDialog(QDialog):
    def __init__(self, fulfillment_type: bool, db_handler: DBHandler, sh: SettingsHandler, begin_date: QDate, end_date: QDate, inflow_values: list, plan_values: dict, parent=None):
        super(FulfillmentDialog, self).__init__(parent)
        self.ui = Ui_FulfillmentDialog()
        self.ui.setupUi(self)

        self.is_fulfillment_toshow: bool = fulfillment_type
        self.db_handler: DBHandler = db_handler
        self.sh: SettingsHandler = sh
        self.begin_date: QDate = begin_date
        self.end_date: QDate = end_date
        self.inflow_values: list = inflow_values
        self.plan_values: dict = plan_values

        values = self.db_handler.load_fulfillmentpayments_from_db(self.begin_date, self.end_date)
        if values is None:
            msg_box = ErrorInfoMessageBox("Не удалось загрузить данные о платежах из базы данных (подробнее см. лог)")
            msg_box.exec()
            self.reject()
            return

        self.model: FulfilmentModel = FulfilmentModel(self)
        self.model.setup_model(self.is_fulfillment_toshow, values, inflow_values, plan_values)
        self.ui.tv_fulfillment.setModel(self.model)
        self.ui.tv_fulfillment.setup_rows()
        self.ui.tv_fulfillment.setup_columns()

        self.ui.pb_exportxls.clicked.connect(lambda: self.export(ExportFormat.XLSX))
        self.ui.pb_exportpdf.clicked.connect(lambda: self.export(ExportFormat.PDF))
        self.ui.pb_close.clicked.connect(self.accept)

    def export(self, export_format: ExportFormat = ExportFormat.XLSX):
        writer = FulfilmentXlsWriter(self.model, self.ui.tv_fulfillment, self.sh)
        if writer.write(self.is_fulfillment_toshow, self.begin_date, self.end_date, export_format=export_format):
            success_dialog: ExportSuccessDialog = ExportSuccessDialog(writer.last_path, self)
            success_dialog.exec()


