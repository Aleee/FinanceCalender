from datetime import date
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Callable

import lovely_logger as log

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QDialog, QFileDialog, QHeaderView, QPushButton, QTableWidgetItem

from base.dbhandler import DBHandler
from base.feeparser import CSVParseError
from base.formatting import dec_strcommaspace, COLOR_STATEMENT, COLOR_CALENDAR, COLOR_HEADER_BG, COLOR_PAIR_BG
from base.payment import PaymentEntry
from base.paymentmacther import reconcile_statement_with_calendar, ReconciliationResult, ProbablePair, RegroupedPayments
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.ui.matchingdialog_ui import Ui_matchingdialog


class MatchingDialog(QDialog):

    COLUMN_HEADERS = ("Дата", "В выписке", "Назначение платежа", "Разница", "В календаре", "Платёж в календаре", "", "")
    DESCR_COLUMNS = (2, 5)
    CONFIDENCE_COLUMN = 6
    BUTTON_COLUMN = 7
    DIFFERENCE_COLUMN = 3

    def __init__(self, settings_handler, db_handler, create_event: Callable[[Decimal, QDialog], bool],
                 create_fees: Callable[[str, dict, QDialog], None], parent=None):
        super(MatchingDialog, self).__init__(parent)
        self.ui = Ui_matchingdialog()
        self.ui.setupUi(self)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler
        self.create_event: Callable[[Decimal, QDialog], bool] = create_event
        self.create_fees: Callable[[str, dict, QDialog], None] = create_fees

        self.match_result: ReconciliationResult | None = None
        self.csv_path: str = ""
        self.confirmed_groups: set[tuple] = set()

        self.difference_font: QFont = QFont(self.font())
        self.difference_font.setBold(True)

        self.ui.tw_discrepancies.setColumnCount(len(self.COLUMN_HEADERS))
        self.ui.tw_discrepancies.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.ui.tw_discrepancies.horizontalHeaderItem(self.CONFIDENCE_COLUMN).setToolTip("Вероятность совпадения")
        self.ui.tw_discrepancies.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header = self.ui.tw_discrepancies.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column in self.DESCR_COLUMNS:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.BUTTON_COLUMN, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.BUTTON_COLUMN, 90)

        self.ui.pb_close.clicked.connect(self.close)
        self.ui.pb_opencsv.clicked.connect(self.open_csv)

    def open_csv(self):
        last_path = self.sh.settings.value("CSVparser/lastloadpath")
        file_path: str = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выберите выписку",
            dir=last_path if last_path and Path(last_path).is_dir() else "",
            filter="Файл выписки в формате CSV (*.csv)", )[0]
        if not file_path:
            return

        self.sh.settings.setValue("CSVparser/lastloadpath", str(Path(file_path).parent))
        self.csv_path = file_path
        self.reconcile()

    def reconcile(self):
        try:
            self.match_result = reconcile_statement_with_calendar(self.csv_path, self.dbh, frozenset(self.confirmed_groups))
        except CSVParseError as exc:
            log.w(f"Не удалось прочитать CSV-файл выписки: {exc}")
            ErrorInfoMessageBox(f"Не удалось прочитать CSV-файл: {exc}").exec()
            self.match_result = None
            return
        except Exception as exc:
            log.x(f"Не удалось обработать CSV-файл: {exc}")
            ErrorInfoMessageBox(f"Не удалось обработать CSV-файл: {exc}").exec()
            self.match_result = None
            return
        if self.match_result is None:
            ErrorInfoMessageBox("В процессе обработки CSV-файла произошла ошибка (см. лог)").exec()
            self.match_result = None
            return

        self.print_report()

    def print_report(self):
        table = self.ui.tw_discrepancies
        scroll_position = table.verticalScrollBar().value()
        table.setRowCount(0)
        if self.match_result is None:
            self.ui.lb_summary.clear()
            return
        self.ui.lb_summary.setText(self.match_result.format_summary())

        for d in self.match_result.discrepancies:
            for pair in d.probable_pairs:
                self.add_row(d.fee_date, pair.statement, pair.calendar, pair)
            for group in d.groups:
                self.add_group(group)
            for entry in d.only_in_statement:
                self.add_row(d.fee_date, entry, None)
            for entry in d.only_in_calendar:
                self.add_row(d.fee_date, None, entry)
        table.verticalScrollBar().setValue(scroll_position)

    def add_row(self, fee_date: date, statement_entry: PaymentEntry | None, calendar_entry: PaymentEntry | None,
                pair: ProbablePair | None = None, in_group: bool = False):
        table = self.ui.tw_discrepancies
        row = table.rowCount()
        table.insertRow(row)

        cells: list[tuple[int, str, str, str | None]] = [(0, fee_date.strftime("%d.%m.%Y"), "", None)]
        if statement_entry:
            cells += [(1, dec_strcommaspace(statement_entry.amount), "", COLOR_STATEMENT),
                      (2, statement_entry.descr, "", COLOR_STATEMENT)]
        if calendar_entry:
            cells += [(4, dec_strcommaspace(calendar_entry.amount), "", COLOR_CALENDAR),
                      (5, calendar_entry.descr, "", COLOR_CALENDAR)]
        if pair:
            sign = "+" if pair.difference > 0 else ""
            cells += [(self.DIFFERENCE_COLUMN, sign + dec_strcommaspace(pair.difference), "", None),
                      (self.CONFIDENCE_COLUMN, f"{pair.confidence:.0%}", "", None)]
        else:
            cells.append((self.DIFFERENCE_COLUMN, "", "", None))

        for column, text, tooltip, color in cells:
            item = QTableWidgetItem(text)
            item.setToolTip(tooltip)
            if color:
                item.setForeground(QBrush(QColor(color)))
            if column in (1, 4, self.CONFIDENCE_COLUMN):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            elif column == self.DIFFERENCE_COLUMN:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(QColor(COLOR_HEADER_BG)))
                item.setFont(self.difference_font)
            table.setItem(row, column, item)

        if pair or in_group:
            for column in range(self.BUTTON_COLUMN):
                if column != self.DIFFERENCE_COLUMN:
                    if table.item(row, column) is None:
                        table.setItem(row, column, QTableWidgetItem(""))
                    table.item(row, column).setBackground(QBrush(QColor(COLOR_PAIR_BG)))

        if pair:
            button = QPushButton("Исправить")
            button.setToolTip("Сумма платежа и сумма обязательства в календаре будут изменены на сумму из выписки")
            button.clicked.connect(partial(self.accept_statement_amount, pair))
            table.setCellWidget(row, self.BUTTON_COLUMN, button)
        elif statement_entry and not calendar_entry and not in_group:
            button = QPushButton("Создать")
            if statement_entry.fee_category:
                button.setToolTip("Открыть окно создания платежей по комиссиям из этой выписки")
                button.clicked.connect(self.make_fee_payments)
            else:
                button.setToolTip("Создать в календаре новый платёж с суммой из выписки")
                button.clicked.connect(partial(self.create_event, statement_entry.amount, self))
            table.setCellWidget(row, self.BUTTON_COLUMN, button)

    def make_fee_payments(self):
        self.create_fees(self.csv_path, self.match_result.fee_totals, self)
        self.reconcile()

    def add_group(self, group: RegroupedPayments):
        table = self.ui.tw_discrepancies
        for index in range(max(len(group.statement), len(group.calendar))):
            self.add_row(group.fee_date,
                         group.statement[index] if index < len(group.statement) else None,
                         group.calendar[index] if index < len(group.calendar) else None,
                         in_group=True)

        row = table.rowCount()
        table.insertRow(row)
        table.setSpan(row, 0, 1, self.BUTTON_COLUMN)
        item = QTableWidgetItem("Суммы группы равны, но платежи разбиты по-разному. Проверьте расчёт:\n"
                                + group.explanation)
        item.setBackground(QBrush(QColor(COLOR_PAIR_BG)))
        table.setItem(row, 0, item)
        button = QPushButton("Подтвердить")
        button.setToolTip("Считать эти платежи сверенными: группа исчезнет из расхождений до закрытия окна")
        button.clicked.connect(partial(self.confirm_group, group))
        table.setCellWidget(row, self.BUTTON_COLUMN, button)

    def confirm_group(self, group: RegroupedPayments):
        self.confirmed_groups.add(group.key)
        self.reconcile()

    def accept_statement_amount(self, pair: ProbablePair):
        if not self.dbh.correct_payment_sum(pair.calendar.payment_id, pair.statement.amount):
            ErrorInfoMessageBox("Не удалось изменить сумму платежа (подробнее см. лог)").exec()
            return
        self.reconcile()
