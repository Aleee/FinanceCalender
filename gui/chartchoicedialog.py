from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog

from base.date import first_date_of_month
from gui.chartdialogs import DebtChartDialog
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.ui.chartchoice_ui import Ui_ChartChoiceDialog


class ChartChoiceDialog(QDialog):

    def __init__(self, parent=None):
        super(ChartChoiceDialog, self).__init__(parent)
        self.ui = Ui_ChartChoiceDialog()
        self.ui.setupUi(self)

        self.ui.de_start.setDate(first_date_of_month(QDate.currentDate().addMonths(-1)))
        self.ui.de_end.setDate(QDate.currentDate())

        self.ui.pb_cancel.clicked.connect(self.close)
        self.ui.pb_continue.clicked.connect(self.open_chart_dialog)

    def open_chart_dialog(self):
        start_date = self.ui.de_start.date()
        end_date = self.ui.de_end.date()
        if start_date > end_date:
            ErrorInfoMessageBox("Дата начала превышает дату окончания периода").exec()
            return

        if self.ui.rb_chart1.isChecked():
            self.debtchart_dialog = DebtChartDialog(start_date, end_date, self)
            self.debtchart_dialog.exec()
            self.accept()

