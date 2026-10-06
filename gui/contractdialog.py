from typing import Optional

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import QDialog, QButtonGroup, QLayout, QDialogButtonBox

from base.dbhandler import DBHandler
from base.contract import PaymentDueType, DaysType, MonthType, ContractDocumentData, ContractInfo
from base.paymentdate import calculate_payment_date
from base.workcalendar import WEEKDAY_ABBR
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.ui.contractdialog_ui import Ui_ContractDialog


class ContractDocumentDialog(QDialog):

    DAYS_TYPE_ITEMS = (
        ("календарных", DaysType.CALENDAR),
        ("банковских", DaysType.BANKING),
        ("рабочих", DaysType.WORKING),
    )
    MONTH_TYPE_ITEMS = (
        ("предыдущего", MonthType.PREVIOUS),
        ("отчётного", MonthType.CURRENT),
        ("следующего", MonthType.NEXT),
    )

    def __init__(self, dbh: DBHandler, settings: QSettings, document_id: int, contract: ContractInfo, parent=None):
        super().__init__(parent)
        self.ui = Ui_ContractDialog()
        self.ui.setupUi(self)
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.dbh = dbh
        self.settings = settings
        self.document_id = document_id
        self.contract = contract
        self._loaded: Optional[ContractDocumentData] = None

        self.rbg_termgroup = QButtonGroup(self)
        for btn in (self.ui.rb_termsunknown, self.ui.rb_fixed, self.ui.rb_relative):
            self.rbg_termgroup.addButton(btn)

        self._rb_payment = {
            PaymentDueType.PREPAYMENT: self.ui.rb_termsunknown,
            PaymentDueType.RELATIVE: self.ui.rb_relative,
            PaymentDueType.FIXED: self.ui.rb_fixed,
        }
        for text, days_type in self.DAYS_TYPE_ITEMS:
            self.ui.cmb_rel_daystype.addItem(text, days_type.value)
        for combo in (self.ui.cmb_rel_month, self.ui.cmb_fixed_month):
            for text, month_type in self.MONTH_TYPE_ITEMS:
                combo.addItem(text, month_type.value)

        self.btn_save = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Save)
        self.btn_save.setText("Сохранить")
        self.btn_save.setDefault(True)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        self.ui.buttonBox.accepted.connect(self.on_save)
        self.ui.buttonBox.rejected.connect(self.reject)

        doctypes = self.dbh.load_documenttypes()
        positions = self.dbh.load_positions()
        if doctypes is None or positions is None:
            ErrorInfoMessageBox("Не удалось загрузить данные из базы данных (см. подробнее лог)", parent=self).exec()
            return
        for doctype_id, name in doctypes:
            self.ui.cmb_documenttype.addItem(name, doctype_id)
        for position_id, _, name in positions:
            self.ui.cmb_responsible.addItem(name, position_id)

        self._set_defaults()
        if document_id != 0:
            self.load_data()
        else:
            self.init_new_document()
        if self._loaded is None:
            return

        self.setWindowTitle(f"Документ: {self._loaded.document_name}" if document_id != 0 else "Новый документ")

        self.rbg_termgroup.buttonToggled.connect(self.update_terms_widgets)
        self.ui.chb_rel_additional.toggled.connect(self.update_terms_widgets)
        for spinbox in (self.ui.spb_rel_days, self.ui.spb_rel_dayofmonth, self.ui.spb_fixed_dayofmonth):
            spinbox.valueChanged.connect(self.update_terms_widgets)
        for combo in (self.ui.cmb_rel_daystype, self.ui.cmb_rel_month, self.ui.cmb_fixed_month):
            combo.currentIndexChanged.connect(self.update_terms_widgets)
        self.update_terms_widgets()
        self.ui.le_documentname.setFocus()

    def exec(self) -> int:
        if self._loaded is None:
            return QDialog.DialogCode.Rejected
        return super().exec()

    # ---------- значения по умолчанию ----------

    def _set_defaults(self) -> None:
        self.ui.rb_termsunknown.setChecked(True)
        self.ui.spb_rel_days.setValue(0)
        self._select_combo_data(self.ui.cmb_rel_daystype, DaysType.CALENDAR.value)
        self.ui.chb_rel_additional.setChecked(False)
        self.ui.spb_rel_dayofmonth.setValue(1)
        self._select_combo_data(self.ui.cmb_rel_month, MonthType.CURRENT.value)
        self.ui.spb_fixed_dayofmonth.setValue(1)
        self._select_combo_data(self.ui.cmb_fixed_month, MonthType.CURRENT.value)

    # ---------- БД -> виджеты ----------

    def load_data(self) -> None:
        data = self.dbh.load_document_data(self.document_id)
        if data is None:
            ErrorInfoMessageBox("Не удалось загрузить данные из базы данных (см. подробнее лог)", parent=self).exec()
            return
        self._loaded = data
        self.fill_widgets(data)

    @staticmethod
    def _select_combo_data(combo, value):
        combo.setCurrentIndex(combo.findData(value))   # -1 (пусто), если не найдено

    def fill_widgets(self, data: ContractDocumentData) -> None:
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
                self._select_combo_data(self.ui.cmb_rel_daystype, data.days_type.value)
            self.ui.chb_rel_additional.setChecked(data.has_calendar_condition)
            if data.month_day is not None:
                self.ui.spb_rel_dayofmonth.setValue(data.month_day)
            if data.month_type is not None:
                self._select_combo_data(self.ui.cmb_rel_month, data.month_type.value)

        elif data.payment_type == PaymentDueType.FIXED:
            if data.month_day is not None:
                self.ui.spb_fixed_dayofmonth.setValue(data.month_day)
            if data.month_type is not None:
                self._select_combo_data(self.ui.cmb_fixed_month, data.month_type.value)

        self._rb_payment[data.payment_type].setChecked(True)

    # ---------- виджеты -> данные ----------

    @staticmethod
    def _checked_key(mapping: dict):
        for key, button in mapping.items():
            if button.isChecked():
                return key
        return None

    def collect_data(self) -> ContractDocumentData:
        loaded = self._loaded

        payment_type = self._checked_key(self._rb_payment) or PaymentDueType.PREPAYMENT
        days_count = 0
        days_type: Optional[DaysType] = None
        has_calendar_condition = False
        month_day: Optional[int] = None
        month_type: Optional[MonthType] = None

        if payment_type == PaymentDueType.RELATIVE:
            days_count = self.ui.spb_rel_days.value()
            days_type = DaysType(self.ui.cmb_rel_daystype.currentData())
            has_calendar_condition = self.ui.chb_rel_additional.isChecked()
            if has_calendar_condition:
                month_day = self.ui.spb_rel_dayofmonth.value()
                month_type = MonthType(self.ui.cmb_rel_month.currentData())

        elif payment_type == PaymentDueType.FIXED:
            month_day = self.ui.spb_fixed_dayofmonth.value()
            month_type = MonthType(self.ui.cmb_fixed_month.currentData())

        return ContractDocumentData(
            document_id=self.document_id,
            contractor_id=loaded.contractor_id,
            contractor_name=self.ui.le_contractor.text(),
            contract_id=loaded.contract_id,
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

    def on_save(self) -> None:
        if self._loaded is None:
            return
        data = self.collect_data()
        if not data.document_name:
            ErrorInfoMessageBox("Укажите название документа", parent=self).exec()
            self.ui.le_documentname.setFocus()
            return
        if not data.document_type:
            ErrorInfoMessageBox("Выберите тип документа", parent=self).exec()
            self.ui.cmb_documenttype.setFocus()
            return
        new_id = self.dbh.save_document_data(data)
        if new_id is None:
            return
        self.document_id = new_id
        self.accept()

    def update_terms_widgets(self, *_) -> None:
        self.ui.fr_relative.setEnabled(self.ui.rb_relative.isChecked())
        self.ui.widget_2.setEnabled(self.ui.chb_rel_additional.isChecked())
        self.ui.fr_fixed.setEnabled(self.ui.rb_fixed.isChecked())

    def init_new_document(self) -> None:
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
