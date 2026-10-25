from decimal import Decimal
from html import escape
from typing import Callable

from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPalette
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from base.contracthistory import ContractObligation, ContractPayment, payment_years, payments_for_year
from base.date import date_displstr
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.manualdialog import add_help_shortcut
from gui.ui.contracthistorydialog_ui import Ui_ContractHistoryDialog

ALL_YEARS = 0
SORT_ROLE = Qt.ItemDataRole.UserRole + 1
CONTRACT_COLUMN_WIDTH = 260
PAID_BACKCOLOR = QColor("#f0f8f0")
OVERDUE_BACKCOLOR = QColor("#fdf1f1")
ALTERNATE_BACKCOLOR = QColor("#f2f6fa")


def contract_label(number: str, date: QDate, document_name: str) -> str:
    label = f"№ {number} от {date_displstr(date)}"
    return f"{label} · {document_name}" if document_name else label


def document_scope(document_name: str, contract_number: str, contract_date: QDate,
                   contractor_name: str) -> tuple[str, str, str]:
    return f"{contract_number} от {date_displstr(contract_date)}", f"({document_name})", contractor_name


class SortableItem(QTableWidgetItem):

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return self.data(SORT_ROLE) < other.data(SORT_ROLE)


class ContractHistoryDialog(QDialog):

    OBLIGATION_HEADERS = ("Договор", "Платеж", "Срок", "Сумма", "Остаток")
    OBLIGATION_FIT_COLUMNS = (2, 3, 4)
    OBLIGATION_AMOUNT_COLUMNS = (3, 4)
    PAYMENT_HEADERS = ("Дата", "Платеж", "Договор", "Сумма")
    PAYMENT_FIT_COLUMNS = (0, 3)
    PAYMENT_AMOUNT_COLUMNS = (3,)

    def __init__(self, dbh: DBHandler, title: str, contractor_id: int, contract_id: int | None,
                 open_event: Callable[[int, QWidget], bool] | None, parent=None, document_id: int | None = None,
                 subtitle: str = "", title_note: str = ""):
        super().__init__(parent)
        self.ui = Ui_ContractHistoryDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "06-contractors.html")

        self.dbh = dbh
        self.contractor_id = contractor_id
        self.contract_id = contract_id
        self.document_id = document_id
        self.open_event = open_event
        self.obligations: list[ContractObligation] = []
        self.payments: list[ContractPayment] = []

        self.ui.la_scope.setText(f"<b>{escape(title)}</b> {escape(title_note)}" if title_note
                                  else f"<b>{escape(title)}</b>")
        self.ui.la_subtitle.setText(subtitle)
        self.ui.la_subtitle.setVisible(bool(subtitle))
        self.setWindowTitle(f"Платежи: {title}")
        self.setup_table(self.ui.tbl_obligations, self.ui.tbl_obligations_total, self.OBLIGATION_HEADERS,
                         0, 2, Qt.SortOrder.AscendingOrder, 2)
        self.setup_table(self.ui.tbl_payments, self.ui.tbl_payments_total, self.PAYMENT_HEADERS,
                         2, 0, Qt.SortOrder.DescendingOrder, 1)
        payments_palette = self.ui.tbl_payments.palette()
        payments_palette.setColor(QPalette.ColorRole.AlternateBase, ALTERNATE_BACKCOLOR)
        self.ui.tbl_payments.setPalette(payments_palette)
        if contract_id is not None:
            for table in (self.ui.tbl_obligations, self.ui.tbl_obligations_total):
                table.setColumnHidden(0, True)
            for table in (self.ui.tbl_payments, self.ui.tbl_payments_total):
                table.setColumnHidden(2, True)
        self.total_layouts = {
            self.ui.tbl_obligations.viewport(): (self.ui.tbl_obligations, self.ui.lay_obligations_total),
            self.ui.tbl_payments.viewport(): (self.ui.tbl_payments, self.ui.lay_payments_total),
        }
        for viewport in self.total_layouts:
            viewport.installEventFilter(self)

        self.load_history()
        self.ui.cmb_year.currentIndexChanged.connect(self.fill_payments)
        self.ui.chb_only_unpaid.toggled.connect(self.fill_obligations)
        self.ui.tbl_obligations.cellDoubleClicked.connect(lambda row, _: self.on_open_event(self.ui.tbl_obligations, row))
        self.ui.pb_close.clicked.connect(self.accept)

    @staticmethod
    def setup_table(table: QTableWidget, total_table: QTableWidget, headers: tuple[str, ...], contract_column: int,
                    sort_column: int, sort_order: Qt.SortOrder, total_rows: int) -> None:
        for widget in (table, total_table):
            widget.setColumnCount(len(headers))
            widget.setWordWrap(False)
            header = widget.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            widget.setColumnWidth(contract_column, CONTRACT_COLUMN_WIDTH)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSortIndicator(sort_column, sort_order)
        table.setSortingEnabled(True)
        total_table.setRowCount(total_rows)
        total_table.setFixedHeight(total_rows * total_table.rowHeight(0) + 2 * total_table.frameWidth())

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.Resize and watched in self.total_layouts:
            table, layout = self.total_layouts[watched]
            scrollbar_width = table.width() - watched.width() - 2 * table.frameWidth()
            layout.setContentsMargins(0, 0, max(scrollbar_width, 0), 0)
        return super().eventFilter(watched, event)

    def load_history(self) -> None:
        history = self.dbh.load_contract_history(self.contractor_id, self.contract_id, self.document_id)
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
    def make_item(text: str, event_id: int, right: bool = False, overdue: bool = False,
                  sort_key: object = None, background: QColor | None = None) -> QTableWidgetItem:
        item = SortableItem(text)
        item.setData(Qt.ItemDataRole.UserRole, event_id)
        item.setData(SORT_ROLE, text.casefold() if sort_key is None else sort_key)
        if right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setToolTip(text)
        if background is not None:
            item.setBackground(QBrush(background))
        if overdue:
            item.setForeground(QBrush(Qt.GlobalColor.red))
            item.setToolTip("Просрочено")
        return item

    @staticmethod
    def show_empty_row(table: QTableWidget, text: str) -> None:
        first_column = next(column for column in range(table.columnCount()) if not table.isColumnHidden(column))
        table.setRowCount(1)
        table.setSpan(0, first_column, 1, table.columnCount() - first_column)
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(0, first_column, item)

    @staticmethod
    def fill_total(total_table: QTableWidget, row: int, label: str, amounts: dict[int, Decimal],
                   bold: bool = True, red: bool = False) -> None:
        font = QFont(total_table.font())
        font.setBold(bold)
        background = QBrush(total_table.palette().color(QPalette.ColorRole.Window))
        for column in range(total_table.columnCount()):
            text = label if column == 1 else dec_strcommaspace(amounts[column]) if column in amounts else ""
            item = QTableWidgetItem(text)
            item.setFont(font)
            item.setBackground(background)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if red and column in amounts:
                item.setForeground(QBrush(Qt.GlobalColor.red))
            if column in amounts:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_table.setItem(row, column, item)

    @staticmethod
    def fit_columns(table: QTableWidget, total_table: QTableWidget, columns: tuple[int, ...]) -> None:
        header = table.horizontalHeader()
        for column in columns:
            width = max(table.sizeHintForColumn(column), total_table.sizeHintForColumn(column),
                        header.sectionSizeHint(column))
            table.setColumnWidth(column, width)
            total_table.setColumnWidth(column, width)

    def refresh(self) -> None:
        self.fill_obligations()
        self.fill_payments()

    def fill_obligations(self) -> None:
        today = QDate.currentDate()
        only_unpaid = self.ui.chb_only_unpaid.isChecked()
        obligations = [obligation for obligation in self.obligations if obligation.remain > 0 or not only_unpaid]
        table = self.ui.tbl_obligations
        table.setSortingEnabled(False)
        table.clearSpans()
        table.setRowCount(len(obligations))
        overdue_remain = Decimal(0)
        for row, obligation in enumerate(obligations):
            overdue = obligation.remain > 0 and obligation.due_date < today
            cells = (
                (contract_label(obligation.contract_number, obligation.contract_date, obligation.document_name),
                 False, None),
                (obligation.name, False, None),
                (date_displstr(obligation.due_date), False, obligation.due_date.toJulianDay()),
                (dec_strcommaspace(obligation.total), True, float(obligation.total)),
                (dec_strcommaspace(obligation.remain), True, float(obligation.remain)),
            )
            if overdue:
                overdue_remain += obligation.remain
            for column, (text, right, sort_key) in enumerate(cells):
                table.setItem(row, column, self.make_item(
                    text, obligation.event_id, right, overdue and column in (2, 4), sort_key,
                    PAID_BACKCOLOR if obligation.remain <= 0 else OVERDUE_BACKCOLOR if overdue else None))
        if not obligations:
            self.show_empty_row(table, "Нет неоплаченных обязательств" if only_unpaid else "Нет обязательств")
        table.setSortingEnabled(True)
        self.fill_total(self.ui.tbl_obligations_total, 0, "Итого", {
            3: sum((obligation.total for obligation in obligations), Decimal(0)),
            4: sum((obligation.remain for obligation in obligations), Decimal(0)),
        })
        self.fill_total(self.ui.tbl_obligations_total, 1, "из них просрочено:", {4: overdue_remain},
                        bold=False, red=overdue_remain > 0)
        self.fit_columns(table, self.ui.tbl_obligations_total, self.OBLIGATION_FIT_COLUMNS)
        self.ui.tw_history.setTabText(self.ui.tw_history.indexOf(self.ui.tab_obligations),
                                      f"Обязательства ({len(obligations)})")

    def fill_payments(self) -> None:
        year = self.selected_year()
        payments = payments_for_year(self.payments, year)
        table = self.ui.tbl_payments
        table.setSortingEnabled(False)
        table.clearSpans()
        table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            cells = (
                (date_displstr(payment.payment_date), False, payment.payment_date.toJulianDay()),
                (payment.event_name, False, None),
                (contract_label(payment.contract_number, payment.contract_date, payment.document_name), False, None),
                (dec_strcommaspace(payment.amount), True, float(payment.amount)),
            )
            for column, (text, right, sort_key) in enumerate(cells):
                table.setItem(row, column, self.make_item(text, payment.event_id, right, sort_key=sort_key))
        if not payments:
            self.show_empty_row(table, f"Нет оплат за {year} год" if year else "Нет оплат")
        table.setSortingEnabled(True)
        self.fill_total(self.ui.tbl_payments_total, 0, f"Итого за {year} год" if year else "Итого за все годы", {
            3: sum((payment.amount for payment in payments), Decimal(0)),
        })
        self.fit_columns(table, self.ui.tbl_payments_total, self.PAYMENT_FIT_COLUMNS)
        self.ui.tw_history.setTabText(self.ui.tw_history.indexOf(self.ui.tab_payments), f"Оплаты ({len(payments)})")

    def on_open_event(self, table: QTableWidget, row: int) -> None:
        item = table.item(row, 0)
        event_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if self.open_event is None or event_id is None:
            return
        if self.open_event(event_id, self):
            self.load_history()
