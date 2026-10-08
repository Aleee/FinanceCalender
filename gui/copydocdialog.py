import math
import os
import re
from decimal import Decimal
from html import escape

import lovely_logger as log

from PySide6.QtCore import QDate, QModelIndex, Qt, QTimer
from PySide6.QtWidgets import QDialog, QPlainTextEdit

from base.contract import DocumentTitle, PaymentDueType
from base.date import date_str, date_displstr, MONTHS_RU
from base.dbhandler import DBHandler
from base.liability import RowType, PaymentType
from base.paymentdate import calculate_payment_date
from base.workcalendar import WEEKDAY_ABBR
from gui.common import model_atlevel
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from gui.settings import SettingsHandler
from gui.ui.copydocdialog_ui import Ui_CopyDocDialog


def common_description_prefix(descriptions: list[str]) -> str:
    texts = [text.strip() for text in descriptions if text and text.strip()]
    if not texts:
        return ""
    prefix = os.path.commonprefix(texts)
    if " от " in prefix:
        prefix = prefix[:prefix.index(" от ")]
    if len(texts) == 1:
        match = re.match(r".*?№ ?", prefix)
        if match:
            prefix = match.group()
    return prefix


class CopyDocDialog(QDialog):

    def __init__(self, final_proxy_model, db_handler: DBHandler, settings_handler: SettingsHandler,
                 current_index: QModelIndex, title: DocumentTitle, parent=None):
        super(CopyDocDialog, self).__init__(parent)
        self.ui = Ui_CopyDocDialog()
        self.ui.setupUi(self)

        self.model = final_proxy_model
        self.dbh = db_handler
        self.sh = settings_handler
        self.index: QModelIndex = current_index
        self.document_id: int = title.document_id
        self.terms = self.dbh.load_document_data(self.document_id)
        self.descriptions: list[str] = self.dbh.load_document_descriptions(self.document_id) or []
        self.calculated_due_date: QDate | None = None
        self.due_date_manual: bool = False
        self.period_manual: bool = False

        contract_line = f"Договор № {escape(title.contract_number)} от {date_displstr(title.contract_date)}"
        if title.document_name:
            contract_line += f" ({escape(title.document_name)})"
        self.ui.la_document.setText(f"<b>{escape(title.contractor_name)}</b><br>{contract_line}")
        self.ui.te_paytermsdescr.setPlainText(self.terms.description if self.terms and self.terms.description else "Условия оплаты не заданы")

        for month_num, month_name in enumerate(MONTHS_RU, start=1):
            self.ui.cmb_month.addItem(month_name, month_num)
        today = QDate.currentDate()
        self.ui.dsb_amount.setValue(float(self.source_value(Col.TOTALAMOUNT)))
        self.ui.de_incurrencedate.setDate(today)
        self.ui.de_duedate.setDate(today)
        self.set_period(today)
        self.ui.formLayout.setRowVisible(self.ui.wdg_period, self.needs_period())
        for text_edit in (self.ui.te_name, self.ui.te_descr):
            text_edit.ensurePolished()
            text_edit.setFixedHeight(self.two_lines_height(text_edit))
            text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.te_name.setPlainText(self.source_value(Col.NAME))
        self.ui.te_descr.setPlainText(common_description_prefix(self.descriptions))

        self.ui.de_incurrencedate.dateChanged.connect(self.on_incurrencedate_changed)
        self.ui.cmb_month.activated.connect(self.on_period_edited)
        self.ui.spb_year.valueChanged.connect(self.on_period_edited)
        self.ui.de_duedate.dateChanged.connect(self.on_duedate_edited)
        self.ui.la_duedatehint.linkActivated.connect(self.apply_due_date)
        self.ui.pb_accept.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

        self.recalc_due_date()
        self.ui.dsb_amount.setFocus()
        QTimer.singleShot(0, self.ui.dsb_amount.selectAll)

    @staticmethod
    def two_lines_height(text_edit: QPlainTextEdit) -> int:
        margins = 2 * (text_edit.frameWidth() + text_edit.document().documentMargin())
        return math.ceil(2 * text_edit.fontMetrics().lineSpacing() + margins) + 6

    def source_value(self, column: Col):
        return self.index.siblingAtColumn(column).data(LiabilitySqlTableModel.qtValueRole)

    def needs_period(self) -> bool:
        if self.terms is None:
            return False
        if self.terms.payment_type == PaymentDueType.FIXED:
            return True
        return self.terms.payment_type == PaymentDueType.RELATIVE and bool(self.terms.has_calendar_condition)

    def set_period(self, date: QDate) -> None:
        self.ui.cmb_month.blockSignals(True)
        self.ui.spb_year.blockSignals(True)
        self.ui.cmb_month.setCurrentIndex(date.month() - 1)
        self.ui.spb_year.setValue(date.year())
        self.ui.cmb_month.blockSignals(False)
        self.ui.spb_year.blockSignals(False)

    def set_due_date(self, date: QDate) -> None:
        self.ui.de_duedate.blockSignals(True)
        self.ui.de_duedate.setDate(date)
        self.ui.de_duedate.blockSignals(False)
        self.update_due_date_info()

    def update_due_date_info(self) -> None:
        due_date: QDate = self.ui.de_duedate.date()
        self.ui.la_weekday.setText(WEEKDAY_ABBR[due_date.dayOfWeek()])
        self.ui.la_weekday.setStyleSheet("color: #c0392b;" if due_date.dayOfWeek() >= 6 else "")
        if self.terms is None:
            hint = "Укажите вручную"
        elif self.calculated_due_date is None:
            hint = "Укажите вручную"
        elif self.due_date_manual:
            hint = (f"Расчетная: {self.calculated_due_date.toString('dd.MM.yyyy')} "
                    f"({WEEKDAY_ABBR[self.calculated_due_date.dayOfWeek()]}) · <a href=\"#reset\">вернуть</a>")
        else:
            hint = "Рассчитана автоматически"
        self.ui.la_duedatehint.setText(hint)

    def on_incurrencedate_changed(self, new_date: QDate) -> None:
        if not self.period_manual:
            self.set_period(new_date)
        self.recalc_due_date()

    def on_period_edited(self, *_) -> None:
        self.period_manual = True
        self.recalc_due_date()

    def on_duedate_edited(self, new_date: QDate) -> None:
        self.due_date_manual = new_date != self.calculated_due_date
        self.update_due_date_info()

    def recalc_due_date(self) -> None:
        result = None
        if self.terms is not None:
            result = calculate_payment_date(self.dbh, self.terms, self.ui.de_incurrencedate.date(),
                                            self.ui.spb_year.value(), self.ui.cmb_month.currentData())
        self.calculated_due_date = result if result is not None and result.isValid() else None
        if self.due_date_manual and self.ui.de_duedate.date() == self.calculated_due_date:
            self.due_date_manual = False
        if self.calculated_due_date is not None and not self.due_date_manual:
            self.set_due_date(self.calculated_due_date)
        self.update_due_date_info()

    def apply_due_date(self, *_) -> None:
        if self.calculated_due_date is None:
            return
        self.due_date_manual = False
        self.set_due_date(self.calculated_due_date)

    def check_integrity(self) -> bool:
        text = ""
        focus_widget = None
        if self.ui.dsb_amount.value() == 0.0:
            text, focus_widget = "Сумма платежа не может быть равна нулю", self.ui.dsb_amount
        elif self.ui.te_name.toPlainText().strip() == "":
            text, focus_widget = "Наименование не может быть пустым", self.ui.te_name
        elif self.ui.de_incurrencedate.date() > self.ui.de_duedate.date():
            text, focus_widget = "Дата возникновения платежа не может быть больше даты оплаты", self.ui.de_incurrencedate
        if text:
            ErrorInfoMessageBox(text, parent=self).exec()
            focus_widget.setFocus()
            return False

        descr = self.ui.te_descr.toPlainText().strip()
        if self.ui.de_duedate.date() < QDate.currentDate():
            text += "Дата платежа меньше текущей даты. "
        if descr == "":
            text += "Основание платежа не указано. "
        elif descr.casefold() in {existing.strip().casefold() for existing in self.descriptions}:
            text += "Платеж с таким основанием по этому документу уже есть. "
        if text:
            msg = YesNoMessagebox(f"{text}Вы уверены, что хотите продолжить?")
            if msg.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        return True

    def accept(self, /):
        if not self.check_integrity():
            return
        amount = Decimal(str(self.ui.dsb_amount.value()))
        due_date: QDate = self.ui.de_duedate.date()
        receiver: str = self.source_value(Col.RECEIVER)
        original_model: LiabilitySqlTableModel = model_atlevel(-2, self.model)

        data: list = [
            receiver,
            0,
            int(RowType.LIABILITY),
            self.document_id,
            self.source_value(Col.CATEGORY),
            self.source_value(Col.SUBCATEGORY),
            " ".join(self.ui.te_name.toPlainText().split()),
            str(amount),
            self.source_value(Col.NDS),
            date_str(due_date),
            date_str(self.ui.de_incurrencedate.date()),
            self.source_value(Col.PAYMENTTYPE) or int(PaymentType.NORMAL),
            self.ui.te_descr.toPlainText().strip(),
            self.source_value(Col.RESPONSIBLE),
            self.source_value(Col.NOTES),
            0,
            int(bool(self.source_value(Col.HIDDEN))),
            receiver.lower(),
        ]

        if original_model.insert_row(data) is None:
            log.e(f"Не удалось вставить новую строку в таблицу event со следующими данными: {data}")
            return
        QDialog.accept(self)
