from PySide6.QtWidgets import QDialog, QButtonGroup

from base.event import EventField
from gui.ui.exportdialog_ui import Ui_ExportDialog
from base.xlswriter import XlsWriter, ExportFormat


class ExportDialog(QDialog):

    def __init__(self, xls_writer: XlsWriter, column_visibility: list[bool], parent=None):
        super(ExportDialog, self).__init__(parent)
        self.ui = Ui_ExportDialog()
        self.ui.setupUi(self)

        self.xls_writer: XlsWriter = xls_writer
        self.column_visibility: list[bool] = column_visibility

        self.rbg_exporttype: QButtonGroup = QButtonGroup(self)
        self.rbg_exporttype.addButton(self.ui.rb_xlsx, ExportFormat.XLSX)
        self.rbg_exporttype.addButton(self.ui.rb_pdf, ExportFormat.PDF)

        self.rbg_receiver: QButtonGroup = QButtonGroup(self)
        self.rbg_receiver.addButton(self.ui.rb_receiver_on, 1)
        self.rbg_receiver.addButton(self.ui.rb_receiver_off, 0)
        self.rbg_receiver.button(int(self.column_visibility[EventField.RECEIVER])).setChecked(True)

        self.rbg_name: QButtonGroup = QButtonGroup(self)
        self.rbg_name.addButton(self.ui.rb_name_on, 1)
        self.rbg_name.addButton(self.ui.rb_name_off, 0)
        self.rbg_name.button(int(self.column_visibility[EventField.NAME])).setChecked(True)

        self.rbg_remainsum: QButtonGroup = QButtonGroup(self)
        self.rbg_remainsum.addButton(self.ui.rb_remainsum_on, 1)
        self.rbg_remainsum.addButton(self.ui.rb_remainsum_off, 0)
        self.rbg_remainsum.button(int(self.column_visibility[EventField.REMAINAMOUNT])).setChecked(True)

        self.rbg_totalsum: QButtonGroup = QButtonGroup(self)
        self.rbg_totalsum.addButton(self.ui.rb_totalsum_on, 1)
        self.rbg_totalsum.addButton(self.ui.rb_totalsum_off, 0)
        self.rbg_totalsum.button(int(self.column_visibility[EventField.TOTALAMOUNT])).setChecked(True)

        self.rbg_duedate: QButtonGroup = QButtonGroup(self)
        self.rbg_duedate.addButton(self.ui.rb_duedate_on, 1)
        self.rbg_duedate.addButton(self.ui.rb_duedate_off, 0)
        self.rbg_duedate.button(int(self.column_visibility[EventField.DUEDATE])).setChecked(True)

        self.rbg_paymenttype: QButtonGroup = QButtonGroup(self)
        self.rbg_paymenttype.addButton(self.ui.rb_paymenttype_on, 1)
        self.rbg_paymenttype.addButton(self.ui.rb_paymenttype_off, 0)
        self.rbg_paymenttype.button(int(self.column_visibility[EventField.PAYMENTTYPE])).setChecked(True)

        self.rbg_desc: QButtonGroup = QButtonGroup(self)
        self.rbg_desc.addButton(self.ui.rb_desc_on, 1)
        self.rbg_desc.addButton(self.ui.rb_desc_off, 0)
        self.rbg_desc.button(int(self.column_visibility[EventField.DESCR])).setChecked(True)

        self.rbg_responsible: QButtonGroup = QButtonGroup(self)
        self.rbg_responsible.addButton(self.ui.rb_responsible_on, 1)
        self.rbg_responsible.addButton(self.ui.rb_responsible_off, 0)
        self.rbg_responsible.button(int(self.column_visibility[EventField.RESPONSIBLE])).setChecked(True)

        self.rbg_todayshare: QButtonGroup = QButtonGroup(self)
        self.rbg_todayshare.addButton(self.ui.rb_todayshare_on, 1)
        self.rbg_todayshare.addButton(self.ui.rb_todayshare_off, 0)
        self.rbg_todayshare.button(int(self.column_visibility[EventField.TODAYSHARE])).setChecked(True)

        self.ui.pb_export.clicked.connect(self.export)

    def columns_to_export(self) -> list[bool]:
        column_visibility_edited = self.column_visibility
        column_visibility_edited[EventField.RECEIVER] = bool(self.rbg_receiver.checkedId())
        column_visibility_edited[EventField.NAME] = bool(self.rbg_name.checkedId())
        column_visibility_edited[EventField.REMAINAMOUNT] = bool(self.rbg_remainsum.checkedId())
        column_visibility_edited[EventField.TOTALAMOUNT] = bool(self.rbg_totalsum.checkedId())
        column_visibility_edited[EventField.DUEDATE] = bool(self.rbg_duedate.checkedId())
        column_visibility_edited[EventField.PAYMENTTYPE] = bool(self.rbg_paymenttype.checkedId())
        column_visibility_edited[EventField.DESCR] = bool(self.rbg_desc.checkedId())
        column_visibility_edited[EventField.RESPONSIBLE] = bool(self.rbg_responsible.checkedId())
        column_visibility_edited[EventField.TODAYSHARE] = bool(self.rbg_todayshare.checkedId())
        return column_visibility_edited

    def export(self):
        fileformat = ExportFormat(self.rbg_exporttype.checkedId())
        columns = self.columns_to_export()
        self.xls_writer.write(fileformat, columns)
        self.accept()
