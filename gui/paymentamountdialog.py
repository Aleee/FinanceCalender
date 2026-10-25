from datetime import date
from decimal import Decimal

from PySide6.QtWidgets import QDialog, QWidget

from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.payment import PaymentInfo
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.manualdialog import add_help_shortcut
from gui.ui.paymentamountdialog_ui import Ui_PaymentAmountDialog


def delete_payment_confirmed(dbh: DBHandler, info: PaymentInfo, parent: QWidget) -> bool:
    sign = -1 if info.total_amount < 0 else 1
    if sign * (info.total_amount - info.paid_before) < 0:
        ErrorInfoMessageBox("Нельзя удалить оплату: остальные оплаты по платежу превысят его общую сумму", parent=parent).exec()
        return False
    if sign * info.paid_before < 0:
        ErrorInfoMessageBox("Нельзя удалить оплату: сумма возвратов превысит сумму остальных оплат", parent=parent).exec()
        return False
    text = (f"Удалить оплату {info.payment_date:%d.%m.%Y} на сумму "
            f"{dec_strcommaspace(abs(info.payment_sum))}? Общая сумма платежа не изменится.")
    if YesNoMessagebox(text, parent, cancel_by_default=True).exec() != YesNoMessagebox.YES_RETURN_VALUE:
        return False
    if not dbh.delete_payment(info.payment_id):
        ErrorInfoMessageBox("Не удалось удалить оплату (подробности см. в логе)", parent=parent).exec()
        return False
    return True


class PaymentAmountDialog(QDialog):

    def __init__(self, db_handler: DBHandler, info: PaymentInfo, new_payment_sum: Decimal | None = None, parent=None):
        super().__init__(parent)
        self.ui = Ui_PaymentAmountDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "04-payment.html")

        self.dbh = db_handler
        self.info = info
        self.sign = -1 if info.total_amount < 0 else 1
        self.payment_sign = -1 if info.payment_sum < 0 else 1

        self.ui.lbl_receiver.setText(info.receiver)
        self.ui.lbl_name.setText(info.name)
        self.ui.lbl_duedate.setText(f"{info.due_date:%d.%m.%Y}" if info.due_date else "не указан")
        self.ui.lbl_paidbefore.setText(dec_strcommaspace(self.sign * info.paid_before))
        self.ui.de_paymentdate.setDate(info.payment_date)
        shown_sum = info.payment_sum if new_payment_sum is None else new_payment_sum
        self.ui.dsb_payment.setValue(float(abs(shown_sum)))

        self.ui.dsb_payment.valueChanged.connect(self.update_total)
        self.ui.chb_changetotal.toggled.connect(self.update_total)
        self.ui.dsb_total.valueChanged.connect(self.update_remain)
        self.ui.pb_deletepayment.clicked.connect(self.delete_payment)
        self.ui.pb_accept.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

        self.update_total()
        self.ui.dsb_payment.setFocus()
        self.ui.dsb_payment.selectAll()

    def payment_date(self) -> date:
        return self.ui.de_paymentdate.date().toPython()

    def payment_sum(self) -> Decimal:
        return self.payment_sign * Decimal(str(self.ui.dsb_payment.value()))

    def total_amount(self) -> Decimal:
        return self.sign * Decimal(str(self.ui.dsb_total.value()))

    def update_total(self) -> None:
        change_total = self.ui.chb_changetotal.isChecked()
        total = self.info.total_amount
        if change_total:
            total += self.payment_sum() - self.info.payment_sum
        self.ui.dsb_total.setValue(float(self.sign * total))
        self.ui.dsb_total.setEnabled(not change_total)
        self.update_remain()

    def update_remain(self) -> None:
        remain = self.total_amount() - self.info.paid_before - self.payment_sum()
        self.ui.lbl_remain.setText(dec_strcommaspace(self.sign * remain))

    def problem_text(self) -> str:
        if self.ui.dsb_payment.value() == 0:
            return "Сумма оплаты не может быть равна нулю"
        if self.ui.dsb_total.value() == 0:
            return "Общая сумма платежа не может быть равна нулю"
        if self.sign * (self.total_amount() - self.info.paid_before - self.payment_sum()) < 0:
            return "Общая сумма платежа не может быть меньше суммы всех оплат по нему"
        if self.sign * (self.info.paid_before + self.payment_sum()) < 0:
            return "Сумма возврата не может превышать сумму остальных оплат по платежу"
        return ""

    def accept(self) -> None:
        text = self.problem_text()
        if text:
            ErrorInfoMessageBox(text, parent=self).exec()
            return
        new_date = self.payment_date()
        if new_date > date.today() and new_date != self.info.payment_date:
            text = f"Выбранная дата ({new_date:%d.%m.%Y}) больше текущей даты. Уверены, что хотите продолжить?"
            if YesNoMessagebox(text, self).exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return
        if ((new_date, self.payment_sum(), self.total_amount()) !=
                (self.info.payment_date, self.info.payment_sum, self.info.total_amount)):
            if not self.dbh.update_payment(self.info.payment_id, new_date, self.payment_sum(), self.total_amount()):
                ErrorInfoMessageBox("Не удалось изменить оплату (подробности см. в логе)", parent=self).exec()
                return
        super().accept()

    def delete_payment(self) -> None:
        if delete_payment_confirmed(self.dbh, self.info, self):
            super().accept()
