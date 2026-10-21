from typing import Callable

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QBrush
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from base.contracthistory import (ContractObligation, ContractPayment, HistorySummary, payment_years,
                                  payments_for_year, summarize_history)
from base.date import date_displstr
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.manualdialog import add_help_shortcut
from gui.ui.contracthistorydialog_ui import Ui_ContractHistoryDialog

ALL_YEARS = 0


def contract_label(number: str, date: QDate, document_name: str) -> str:
    label = f"№ {number} от {date_displstr(date)}"
    return f"{label} · {document_name}" if document_name else label


def history_summary_text(summary: HistorySummary, year: int | None) -> str:
    period = f"за {year} год" if year else "за все годы"
    return (f"Обязательств: {summary.count} на {dec_strcommaspace(summary.total, add_rub=True)} · "
            f"оплачено {dec_strcommaspace(summary.paid, add_rub=True)} · "
            f"не оплачено {dec_strcommaspace(summary.unpaid_sum, add_rub=True)} ({summary.unpaid_count}) · "
            f"оплачено {period}: {dec_strcommaspace(summary.paid_in_year, add_rub=True)}")


class ContractHistoryDialog(QDialog):

    OBLIGATION_HEADERS = ("Договор", "Платеж", "Срок", "Сумма", "Оплачено", "Остаток")
    PAYMENT_HEADERS = ("Дата", "Платеж", "Договор", "Сумма")

    def __init__(self, dbh: DBHandler, title: str, contractor_id: int, contract_id: int | None,
                 open_event: Callable[[int, QWidget], bool] | None, parent=None):
        super().__init__(parent)
        self.ui = Ui_ContractHistoryDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "06-contractors.html")

        self.dbh = dbh
        self.contractor_id = contractor_id
        self.contract_id = contract_id
        self.open_event = open_event
        self.obligations: list[ContractObligation] = []
        self.payments: list[ContractPayment] = []

        self.ui.lbl_scope.setText(title)
        self.setWindowTitle(f"Платежи: {title}")
        self.setup_table(self.ui.tbl_obligations, self.OBLIGATION_HEADERS)
        self.setup_table(self.ui.tbl_payments, self.PAYMENT_HEADERS)
        if contract_id is not None:
            self.ui.tbl_obligations.setColumnHidden(0, True)
            self.ui.tbl_payments.setColumnHidden(2, True)

        self.load_history()
        self.ui.cmb_year.currentIndexChanged.connect(self.refresh)
        self.ui.chb_only_unpaid.toggled.connect(self.refresh)
        self.ui.tbl_obligations.cellDoubleClicked.connect(lambda row, _: self.on_open_event(self.ui.tbl_obligations, row))
        self.ui.tbl_payments.cellDoubleClicked.connect(lambda row, _: self.on_open_event(self.ui.tbl_payments, row))
        self.ui.pb_close.clicked.connect(self.accept)
        if open_event is None:
            self.ui.lbl_hint.hide()

    @staticmethod
    def setup_table(table: QTableWidget, headers: tuple[str, ...]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def load_history(self) -> None:
        history = self.dbh.load_contract_history(self.contractor_id, self.contract_id)
        if history is None:
            ErrorInfoMessageBox("Не удалось загрузить историю платежей (см. подробнее лог)", False, self).exec()
            history = ([], [])
        self.obligations, self.payments = history
        selected_year = self.selected_year()
        years = payment_years(self.payments)
        current_year = QDate.currentDate().year()
        if selected_year is None and self.ui.cmb_year.count() == 0:
            selected_year = current_year if current_year in years else (years[0] if years else None)
        self.ui.cmb_year.blockSignals(True)
        self.ui.cmb_year.clear()
        self.ui.cmb_year.addItem("Все годы", ALL_YEARS)
        for year in years:
            self.ui.cmb_year.addItem(str(year), year)
        self.ui.cmb_year.setCurrentIndex(max(self.ui.cmb_year.findData(selected_year or ALL_YEARS), 0))
        self.ui.cmb_year.blockSignals(False)
        self.refresh()

    def selected_year(self) -> int | None:
        return self.ui.cmb_year.currentData() or None

    @staticmethod
    def make_item(text: str, event_id: int, right: bool = False, overdue: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, event_id)
        if right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if overdue:
            item.setForeground(QBrush(Qt.GlobalColor.red))
        return item

    def refresh(self) -> None:
        year = self.selected_year()
        self.fill_obligations()
        self.fill_payments(payments_for_year(self.payments, year))
        self.ui.lbl_summary.setText(history_summary_text(summarize_history(self.obligations, self.payments, year), year))

    def fill_obligations(self) -> None:
        today = QDate.currentDate()
        obligations = [obligation for obligation in self.obligations
                       if obligation.remain > 0 or not self.ui.chb_only_unpaid.isChecked()]
        table = self.ui.tbl_obligations
        table.setRowCount(len(obligations))
        for row, obligation in enumerate(obligations):
            overdue = obligation.remain > 0 and obligation.due_date < today
            cells = (
                (contract_label(obligation.contract_number, obligation.contract_date, obligation.document_name), False),
                (obligation.name, False),
                (date_displstr(obligation.due_date), False),
                (dec_strcommaspace(obligation.total), True),
                (dec_strcommaspace(obligation.paid), True),
                (dec_strcommaspace(obligation.remain), True),
            )
            for column, (text, right) in enumerate(cells):
                table.setItem(row, column, self.make_item(
                    text, obligation.event_id, right, overdue and column in (2, 5)))

    def fill_payments(self, payments: list[ContractPayment]) -> None:
        table = self.ui.tbl_payments
        table.setRowCount(len(payments))
        for row, payment in enumerate(reversed(payments)):
            cells = (
                (date_displstr(payment.payment_date), False),
                (payment.event_name, False),
                (contract_label(payment.contract_number, payment.contract_date, payment.document_name), False),
                (dec_strcommaspace(payment.amount), True),
            )
            for column, (text, right) in enumerate(cells):
                table.setItem(row, column, self.make_item(text, payment.event_id, right))

    def on_open_event(self, table: QTableWidget, row: int) -> None:
        item = table.item(row, 0)
        if self.open_event is None or item is None:
            return
        if self.open_event(item.data(Qt.ItemDataRole.UserRole), self):
            self.load_history()
