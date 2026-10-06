from PySide6.QtWidgets import QDialog, QButtonGroup, QCheckBox

from base.xlswriter import LiabilityXlsWriter, ExportFormat, HiddenDisplayMode, get_pdf_converter
from gui.eventsqlmodel import Col
from gui.exportsuccessdialog import ExportSuccessDialog
from gui.ui.exportdialog_ui import Ui_ExportDialog


class ExportDialog(QDialog):

    FORMAT_SETTINGS_KEY = "Export/lastformat"

    def __init__(self, xls_writer: LiabilityXlsWriter, column_visibility: list[bool], parent=None):
        super(ExportDialog, self).__init__(parent)
        self.ui = Ui_ExportDialog()
        self.ui.setupUi(self)

        self.xls_writer: LiabilityXlsWriter = xls_writer
        self.column_visibility: list[bool] = list(column_visibility)
        self.column_visibility[Col.RECEIVER] = True

        self.rbg_exporttype: QButtonGroup = QButtonGroup(self)
        self.rbg_exporttype.addButton(self.ui.rb_xlsx, ExportFormat.XLSX)
        self.rbg_exporttype.addButton(self.ui.rb_pdf, ExportFormat.PDF)
        self.setup_format()

        self.rbg_hidden: QButtonGroup = QButtonGroup(self)
        self.rbg_hidden.addButton(self.ui.rb_hidden_none, HiddenDisplayMode.NONE)
        self.rbg_hidden.addButton(self.ui.rb_hidden_full, HiddenDisplayMode.FULL)
        self.rbg_hidden.addButton(self.ui.rb_hidden_sumonly, HiddenDisplayMode.SUMONLY)

        self.column_checkboxes: dict[Col, QCheckBox] = {
            Col.NAME: self.ui.chb_name,
            Col.REMAINAMOUNT: self.ui.chb_remainsum,
            Col.TOTALAMOUNT: self.ui.chb_totalsum,
            Col.DUEDATE: self.ui.chb_duedate,
            Col.PAYMENTTYPE: self.ui.chb_paymenttype,
            Col.DESCR: self.ui.chb_desc,
            Col.RESPONSIBLE: self.ui.chb_responsible,
            Col.TODAYSHARE: self.ui.chb_todayshare,
        }
        for col, checkbox in self.column_checkboxes.items():
            checkbox.setChecked(self.column_visibility[col])

        self.ui.pb_export.clicked.connect(self.export)
        self.ui.pb_cancel.clicked.connect(self.reject)

    def setup_format(self) -> None:
        if get_pdf_converter() is None:
            self.ui.rb_pdf.setEnabled(False)
            self.ui.rb_pdf.setToolTip("Для экспорта в PDF требуется установленный Microsoft Excel")
            return
        settings = self.xls_writer.settings_handler.settings
        if str(settings.value(self.FORMAT_SETTINGS_KEY)) == str(int(ExportFormat.PDF)):
            self.ui.rb_pdf.setChecked(True)

    def columns_to_export(self) -> list[bool]:
        for col, checkbox in self.column_checkboxes.items():
            self.column_visibility[col] = checkbox.isChecked()
        return self.column_visibility

    def export(self) -> None:
        fileformat: ExportFormat = ExportFormat(self.rbg_exporttype.checkedId())
        columns: list[bool] = self.columns_to_export()
        hidden_display_mode: HiddenDisplayMode = HiddenDisplayMode(self.rbg_hidden.checkedId())
        if self.xls_writer.write(fileformat, columns, hidden_display_mode):
            self.xls_writer.settings_handler.settings.setValue(self.FORMAT_SETTINGS_KEY, int(fileformat))
            self.accept()
            dlg = ExportSuccessDialog(self.xls_writer.last_path, self.parent())
            dlg.exec()
