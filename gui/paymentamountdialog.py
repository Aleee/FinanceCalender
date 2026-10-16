from decimal import Decimal

from PySide6.QtWidgets import QDialog

from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.payment import PaymentInfo
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.manualdialog import add_help_shortcut
from gui.ui.paymentamountdialog_ui import Ui_PaymentAmountDialog


class PaymentAmountDialog(QDialog):

    def __init__(self, db_handler: DBHandler, info: PaymentInfo, new_payment_sum: Decimal | None = None, parent=None):
        super().__init__(parent)
        self.ui = Ui_PaymentAmountDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "08-statement-matching.html")

        self.dbh = db_handler
        self.info = info
        self.sign = -1 if info.total_amount < 0 else 1

        self.ui.lbl_receiver.setText(info.receiver)
        self.ui.lbl_name.setText(info.name)
        self.ui.lbl_duedate.setText(f"{info.due_date:%d.%m.%Y}" if info.due_date else "не указан")
        self.ui.lbl_paidbefore.setText(dec_strcommaspace(self.sign * info.paid_before))
        self.ui.lbl_payment.setText(f"Оплата {info.payment_date:%d.%m.%Y}:")
        shown_sum = info.payment_sum if new_payment_sum is None else self.sign * abs(new_payment_sum)
        self.ui.dsb_payment.setValue(float(self.sign * shown_sum))

        self.ui.dsb_payment.valueChanged.connect(self.update_total)
        self.ui.chb_changetotal.toggled.connect(self.update_total)
        self.ui.dsb_total.valueChanged.connect(self.update_remain)
        self.ui.pb_accept.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

        self.update_total()
        self.ui.dsb_payment.setFocus()
        self.ui.dsb_payment.selectAll()

    def payment_sum(self) -> Decimal:
        return self.sign * Decimal(str(self.ui.dsb_payment.value()))

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
        return ""

    def accept(self) -> None:
        text = self.problem_text()
        if text:
            ErrorInfoMessageBox(text, parent=self).exec()
            return
        if (self.payment_sum(), self.total_amount()) != (self.info.payment_sum, self.info.total_amount):
            if not self.dbh.change_payment_amounts(self.info.payment_id, self.payment_sum(), self.total_amount()):
                ErrorInfoMessageBox("Не удалось изменить суммы (подробности см. в логе)", parent=self).exec()
                return
        super().accept()
