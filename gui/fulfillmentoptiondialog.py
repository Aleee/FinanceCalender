from PySide6 import QtWidgets
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog, QButtonGroup

from base.date import first_date_of_month, last_date_of_month
from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.fulfillmentdialog import FulfillmentDialog
from gui.ui.fulfillmentoptiondialog_ui import Ui_FulfillmentOptionDialog


class FulfillmentOptionDialog(QDialog):

    MONTHS = ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь")
    QUARTALS = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]

    def __init__(self, db_handler: DBHandler, parent=None):
        super(FulfillmentOptionDialog, self).__init__(parent)
        self.ui = Ui_FulfillmentOptionDialog()
        self.ui.setupUi(self)

        self.db_handler = db_handler

        self.rb_group: QButtonGroup = QButtonGroup(self)
        self.rb_group.addButton(self.ui.rb_onemonth, 1)
        self.rb_group.addButton(self.ui.rb_severalmonths, 2)
        self.rb_group.addButton(self.ui.rb_customperiod, 3)
        self.rb_group.buttonClicked.connect(lambda: self.change_enablestate(self.rb_group.checkedId()))

        self.rb_group_type: QButtonGroup = QButtonGroup(self)
        self.rb_group_type.addButton(self.ui.rb_planfulfillment, 1)
        self.rb_group_type.addButton(self.ui.rb_ndsfreepayments, 2)

        self.ui.pb_cancel.clicked.connect(self.reject)
        self.ui.pb_continue.clicked.connect(self.continue_clicked)

        self.widgets_by_group = {
            1: (self.ui.cmb_onemonth, self.ui.spb_onemonth_year),
            2: (self.ui.cmb_severalmonths_end, self.ui.cmb_severalmonths_begin, self.ui.spb_severalmonths_year_end),
            3: (self.ui.label, self.ui.label_2, self.ui.de_customperiod_end, self.ui.de_customperiod_begin),
        }

        # Заполнение комбобоксов и значения по умолчанию
        for cmb in (self.ui.cmb_onemonth, self.ui.cmb_severalmonths_begin, self.ui.cmb_severalmonths_end):
            for index, name in enumerate(self.MONTHS):
                cmb.addItem(name, index + 1)
        current_date: QDate = QDate.currentDate()
        self.ui.cmb_onemonth.setCurrentText(self.MONTHS[current_date.month() - 1])
        for spb in (self.ui.spb_onemonth_year, self.ui.spb_severalmonths_year_end):
            spb.setValue(current_date.year())
        for quart in self.QUARTALS:
            if current_date.month() in quart:
                self.ui.cmb_severalmonths_end.setCurrentText(self.MONTHS[quart[0] - 1])
                self.ui.cmb_severalmonths_end.setCurrentText(self.MONTHS[quart[2] - 1])
        self.ui.de_customperiod_begin.setDate(first_date_of_month(current_date))
        self.ui.de_customperiod_end.setDate(current_date)


        # Косметика
        self.layout().setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
        self.ui.rb_onemonth.click()


    def change_enablestate(self, checked_id: int):
        for group_id, widgets in self.widgets_by_group.items():
            for widget in widgets:
                widget.setEnabled(checked_id == group_id)

    def continue_clicked(self) -> None:
        begin_date, end_date = self.get_period_data()
        if self.ui.stackedWidget.currentIndex() == 0:
            if begin_date > end_date:
                msg_box = ErrorInfoMessageBox("Дата начала превышает дату окончания периода")
                msg_box.exec()
                return
            if begin_date.year() != end_date.year():
                msg_box = ErrorInfoMessageBox("Начало и конец периода должны быть в пределах одного года")
                msg_box.exec()
                return
            self.load_inflow(begin_date, end_date)
            if self.ui.rb_planfulfillment.isChecked():
                self.ui.stackedWidget.setCurrentIndex(1)
            else:
                dlg: FulfillmentDialog = FulfillmentDialog(False, self.db_handler, begin_date, end_date, self.get_inflow_data(), self.load_plan(begin_date, end_date), self)
                dlg.exec()
                self.accept()
        else:
            self.save_inflow(begin_date, end_date)
            dlg: FulfillmentDialog = FulfillmentDialog(True, self.db_handler, begin_date, end_date, self.get_inflow_data(), self.load_plan(begin_date, end_date), self)
            dlg.exec()
            self.accept()

    def load_inflow(self, begin_date: QDate, end_date: QDate):
        inflow_data = self.db_handler.load_fulfillmentdata_from_db(begin_date, end_date)
        if inflow_data:
            for index, wdg in enumerate([self.ui.spb_10000, self.ui.spb_21000, self.ui.spb_22000, self.ui.spb_23100, self.ui.spb_23200]):
                wdg.setValue(inflow_data[index])

    def save_inflow(self, begin_date: QDate, end_date: QDate):
        values = [spb.value() for spb in (self.ui.spb_10000, self.ui.spb_21000, self.ui.spb_22000, self.ui.spb_23100, self.ui.spb_23200)]
        if any(value != 0 for value in values):
            self.db_handler.save_fulfillmentdata_to_db(begin_date, end_date, values)

    def get_inflow_data(self) -> list[int]:
        inflow_data = []
        for wdg in (self.ui.spb_10000, self.ui.spb_21000, self.ui.spb_22000, self.ui.spb_23100, self.ui.spb_23200):
            inflow_data.append(wdg.value())
        return inflow_data

    def get_period_data(self) -> tuple[QDate, QDate]:
        if self.rb_group.checkedId() == 1:
            begin_date: QDate = QDate(self.ui.spb_onemonth_year.value(), self.ui.cmb_onemonth.currentData(), 1)
            end_date: QDate = QDate(begin_date.year(), begin_date.month(), begin_date.daysInMonth())
        elif self.rb_group.checkedId() == 2:
            begin_date: QDate = QDate(self.ui.spb_severalmonths_year_end.value(), self.ui.cmb_severalmonths_begin.currentData(), 1)
            end_temp_date: QDate = QDate(self.ui.spb_severalmonths_year_end.value(), self.ui.cmb_severalmonths_end.currentData(), 1)
            end_date: QDate = last_date_of_month(end_temp_date)
        elif self.rb_group.checkedId() == 3:
            begin_date, end_date = self.ui.de_customperiod_begin.date(), self.ui.de_customperiod_end.date()
        else:
            raise IndexError
        return begin_date, end_date

    def load_plan(self, begin_date: QDate, end_date: QDate):
        return self.db_handler.load_fulfillmentplanvalues_from_db(begin_date.year(), begin_date.month(), end_date.month())
