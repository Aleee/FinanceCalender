from typing import Optional

from PySide6.QtWidgets import QDialog, QButtonGroup, QLayout

from base.dbhandler import DBHandler
from base.contract import PaymentDueType, DaysType, MonthType, ContractDocumentData, ContractInfo
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.ui.contractdialog_ui import Ui_ContractDialog


class ContractDocumentDialog(QDialog):

    def __init__(self, dbh: DBHandler, document_id: int, contract: ContractInfo, parent=None):
        super().__init__(parent)
        self.ui = Ui_ContractDialog()
        self.ui.setupUi(self)
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.dbh = dbh
        self.document_id = document_id
        self.contract = contract
        self._loaded: Optional[ContractDocumentData] = None

        self.rbg_termgroup = QButtonGroup(self)
        for btn in (self.ui.rb_termsunknown, self.ui.rb_fixed, self.ui.rb_relative):
            self.rbg_termgroup.addButton(btn)
        self.rbg_relative = QButtonGroup(self)
        for btn in (self.ui.rb_rel_banking, self.ui.rb_rel_working, self.ui.rb_rel_calendar):
            self.rbg_relative.addButton(btn)
        self.rbg_rel_add = QButtonGroup(self)
        for btn in (self.ui.rb_rel_period_curr, self.ui.rb_rel_period_next, self.ui.rb_rel_period_prev):
            self.rbg_rel_add.addButton(btn)
        self.rbg_fixed = QButtonGroup(self)
        for btn in (self.ui.rb_fixed_period_curr, self.ui.rb_fixed_period_next, self.ui.rb_fixed_period_prev):
            self.rbg_fixed.addButton(btn)

        self._rb_payment = {
            PaymentDueType.PREPAYMENT: self.ui.rb_termsunknown,
            PaymentDueType.RELATIVE: self.ui.rb_relative,
            PaymentDueType.FIXED: self.ui.rb_fixed,
        }
        self._rb_days_type = {
            DaysType.CALENDAR: self.ui.rb_rel_calendar,
            DaysType.BANKING: self.ui.rb_rel_banking,
            DaysType.WORKING: self.ui.rb_rel_working,
        }
        self._rb_rel_month = {
            MonthType.CURRENT: self.ui.rb_rel_period_curr,
            MonthType.NEXT: self.ui.rb_rel_period_next,
            MonthType.PREVIOUS: self.ui.rb_rel_period_prev,
        }
        self._rb_fixed_month = {
            MonthType.CURRENT: self.ui.rb_fixed_period_curr,
            MonthType.NEXT: self.ui.rb_fixed_period_next,
            MonthType.PREVIOUS: self.ui.rb_fixed_period_prev,
        }

        self.ui.le_contractname.setReadOnly(True)
        self.ui.de_contractdate.setReadOnly(True)

        self.rbg_termgroup.buttonToggled.connect(self.change_frame_visibility)
        self.ui.chb_rel_additional.toggled.connect(self.ui.widget_2.setEnabled)
        self.ui.pushButton.clicked.connect(self.on_save)
        self.ui.pushButton_2.clicked.connect(self.reject)

        doctypes = self.dbh.load_documenttypes()
        positions = self.dbh.load_positions()
        if doctypes is None or positions is None:
            ErrorInfoMessageBox("Не удалось загрузить данные из базы данных (см. подробнее лог)").exec()
            self.reject()
            return
        for doctype_id, name in doctypes:
            self.ui.cmb_documenttype.addItem(name, doctype_id)      # было cmb_responsible
        for position_id, _, name in positions:
            self.ui.cmb_responsible.addItem(name, position_id)

        self._set_defaults()
        if document_id != 0:
            self.load_data()
        else:
            self.init_new_document()
        self.change_frame_visibility()

    # ---------- значения по умолчанию ----------

    def _set_defaults(self):
        self.ui.rb_termsunknown.setChecked(True)
        self.ui.rb_rel_calendar.setChecked(True)
        self.ui.rb_rel_period_curr.setChecked(True)
        self.ui.rb_fixed_period_curr.setChecked(True)
        self.ui.spb_rel_days.setValue(0)
        self.ui.spb_rel_dayofmonth.setValue(1)
        self.ui.spb_fixed_dayofmonth.setValue(1)
        self.ui.chb_rel_additional.setChecked(False)
        self.ui.widget_2.setEnabled(False)

    # ---------- БД -> виджеты ----------

    def load_data(self):
        data = self.dbh.load_document_data(self.document_id)
        if data is None:
            ErrorInfoMessageBox("Не удалось загрузить данные из базы данных (см. подробнее лог)").exec()
            self.reject()
            return
        self._loaded = data
        self.fill_widgets(data)

    @staticmethod
    def _select_combo_data(combo, value):
        combo.setCurrentIndex(combo.findData(value))   # -1 (пусто), если не найдено

    def fill_widgets(self, data: ContractDocumentData):
        self.ui.le_contractor.setText(data.contractor_name)
        self.ui.le_contractname.setText(data.contract_number)
        if data.contract_date.isValid():
            self.ui.de_contractdate.setDate(data.contract_date)
        self.ui.le_documentname.setText(data.document_name)
        self.ui.te_description.setPlainText(data.description)
        self._select_combo_data(self.ui.cmb_documenttype, data.document_type)
        self._select_combo_data(self.ui.cmb_responsible, data.position_id)

        self._set_defaults()

        if data.payment_type == PaymentDueType.RELATIVE:
            self.ui.spb_rel_days.setValue(data.days_count or 0)
            if data.days_type is not None:
                self._rb_days_type[data.days_type].setChecked(True)
            self.ui.chb_rel_additional.setChecked(data.has_calendar_condition)
            if data.month_day is not None:
                self.ui.spb_rel_dayofmonth.setValue(data.month_day)
            if data.month_type is not None:
                self._rb_rel_month[data.month_type].setChecked(True)

        elif data.payment_type == PaymentDueType.FIXED:
            if data.month_day is not None:
                self.ui.spb_fixed_dayofmonth.setValue(data.month_day)
            if data.month_type is not None:
                self._rb_fixed_month[data.month_type].setChecked(True)

        self._rb_payment[data.payment_type].setChecked(True)

    # ---------- виджеты -> данные ----------

    @staticmethod
    def _checked_key(mapping: dict):
        for key, button in mapping.items():
            if button.isChecked():
                return key
        return None

    def collect_data(self) -> ContractDocumentData:
        base = self._loaded

        payment_type = self._checked_key(self._rb_payment) or PaymentDueType.PREPAYMENT
        days_count = 0
        days_type: Optional[DaysType] = None
        has_calendar_condition = False
        month_day: Optional[int] = None
        month_type: Optional[MonthType] = None

        if payment_type == PaymentDueType.RELATIVE:
            days_count = self.ui.spb_rel_days.value()
            days_type = self._checked_key(self._rb_days_type)
            has_calendar_condition = self.ui.chb_rel_additional.isChecked()
            if has_calendar_condition:
                month_day = self.ui.spb_rel_dayofmonth.value()
                month_type = self._checked_key(self._rb_rel_month)

        elif payment_type == PaymentDueType.FIXED:
            month_day = self.ui.spb_fixed_dayofmonth.value()
            month_type = self._checked_key(self._rb_fixed_month)

        return ContractDocumentData(
            document_id=self.document_id,
            contractor_id=base.contractor_id,
            contractor_name=self.ui.le_contractor.text(),
            contract_id=base.contract_id,
            contract_number=self.ui.le_contractname.text().strip(),
            contract_date=self.ui.de_contractdate.date(),
            document_type=self.ui.cmb_documenttype.currentData() or 0,
            position_id=self.ui.cmb_responsible.currentData() or 0,
            document_name=self.ui.le_documentname.text().strip(),
            description=self.ui.te_description.toPlainText().strip(),
            payment_type=payment_type,
            days_count=days_count,
            days_type=days_type,
            has_calendar_condition=has_calendar_condition,
            month_day=month_day,
            month_type=month_type,
        )

    def on_save(self):
        data = self.collect_data()
        if not data.document_name:
            ErrorInfoMessageBox("Укажите название документа").exec()
            return
        if not data.document_type:
            ErrorInfoMessageBox("Тип документа обязательно должен быть выбран").exec()
            return
        new_id = self.dbh.save_document_data(data)
        if new_id is None:
            return
        self.document_id = new_id
        self.accept()

    def change_frame_visibility(self, *_):
        self.ui.fr_relative.setVisible(self.ui.rb_relative.isChecked())
        self.ui.fr_fixed.setVisible(self.ui.rb_fixed.isChecked())

    def init_new_document(self):
        c = self.contract
        self._loaded = ContractDocumentData(
            document_id=0,
            contractor_id=c.contractor_id,
            contractor_name=c.contractor_name,
            contract_id=c.contract_id,
            contract_number=c.contract_number,
            contract_date=c.contract_date,
            document_type=0,
            position_id=0,
            document_name="",
            description="",
            payment_type=PaymentDueType.PREPAYMENT,
        )
        self.fill_widgets(self._loaded)