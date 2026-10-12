import hashlib
import json
from datetime import date
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Callable

import lovely_logger as log

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon
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

    COLUMN_HEADERS = ("Дата", "В выписке", "Назначение платежа", "Разница", "В календаре", "Платеж в календаре", "", "", "")
    DESCR_COLUMNS = (2, 5)
    CONFIDENCE_COLUMN = 6
    BUTTON_COLUMN = 7
    IGNORE_COLUMN = 8
    DIFFERENCE_COLUMN = 3

    def __init__(self, settings_handler, db_handler, create_event: Callable[[Decimal, date, QDialog], bool],
                 edit_event: Callable[[PaymentEntry, date, QDialog], bool],
                 create_fees: Callable[[str, dict, QDialog], None], parent=None):
        super(MatchingDialog, self).__init__(parent)
        self.ui = Ui_matchingdialog()
        self.ui.setupUi(self)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler
        self.create_event: Callable[[Decimal, date, QDialog], bool] = create_event
        self.edit_event: Callable[[PaymentEntry, date, QDialog], bool] = edit_event
        self.create_fees: Callable[[str, dict, QDialog], None] = create_fees

        self.match_result: ReconciliationResult | None = None
        self.csv_path: str = ""
        self.hidden: set[str] = set()

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
        header.setSectionResizeMode(self.IGNORE_COLUMN, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.IGNORE_COLUMN, 36)

        self.pb_restorehidden = QPushButton("Вернуть скрытые")
        self.pb_restorehidden.setToolTip("Снова показать все платежи, скрытые вручную")
        self.pb_restorehidden.setEnabled(False)
        self.pb_restorehidden.clicked.connect(self.restore_hidden)
        self.ui.gridLayout.addWidget(self.pb_restorehidden, 3, 0)

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
        self.load_hidden()
        self.reconcile()

    def load_hidden(self):
        try:
            csv_hash = hashlib.sha1(Path(self.csv_path).read_bytes()).hexdigest()
        except OSError as exc:
            log.w(f"Не удалось прочитать CSV-файл для проверки скрытых платежей: {exc}")
            self.hidden = set()
            return
        if self.sh.settings.value("Matching/csvhash") == csv_hash:
            self.hidden = set(json.loads(self.sh.settings.value("Matching/hidden") or "[]"))
        else:
            self.hidden = set()
            self.sh.settings.setValue("Matching/csvhash", csv_hash)
            self.save_hidden()

    def save_hidden(self):
        self.sh.settings.setValue("Matching/hidden", json.dumps(sorted(self.hidden)))

    def hide_entries(self, keys: tuple[str, ...]):
        self.hidden.update(keys)
        self.save_hidden()
        self.reconcile()

    def restore_hidden(self):
        self.hidden.clear()
        self.save_hidden()
        self.reconcile()

    def reconcile(self):
        try:
            self.match_result = reconcile_statement_with_calendar(self.csv_path, self.dbh, frozenset(self.hidden))
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
            self.pb_restorehidden.setEnabled(False)
            return
        self.ui.lb_summary.setText(self.match_result.format_summary())
        self.pb_restorehidden.setEnabled(bool(self.hidden))

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
            button.setToolTip("Сумма оплаты и сумма платежа в календаре будут изменены на сумму из выписки")
            button.clicked.connect(partial(self.accept_statement_amount, pair))
            table.setCellWidget(row, self.BUTTON_COLUMN, button)
            self.add_ignore_button(row, (pair.statement.key, pair.calendar.key))
        elif statement_entry and not calendar_entry and not in_group:
            button = QPushButton("Создать")
            if statement_entry.fee_category:
                button.setToolTip("Открыть окно создания платежей по комиссиям из этой выписки")
                button.clicked.connect(self.make_fee_payments)
            else:
                button.setToolTip("Создать в календаре новый платеж с суммой из выписки")
                button.clicked.connect(partial(self.create_payment, statement_entry.amount, fee_date))
            table.setCellWidget(row, self.BUTTON_COLUMN, button)
        elif calendar_entry and not statement_entry and not in_group and calendar_entry.event_id is not None:
            button = QPushButton("Исправить")
            button.setToolTip("Открыть окно редактирования этого платежа из календаря")
            button.clicked.connect(partial(self.edit_calendar_payment, calendar_entry, fee_date))
            table.setCellWidget(row, self.BUTTON_COLUMN, button)

        if not pair and not in_group:
            self.add_ignore_button(row, ((statement_entry or calendar_entry).key,))

    def add_ignore_button(self, row: int, keys: tuple[str, ...]):
        button = QPushButton()
        button.setIcon(QIcon(":/designer/icons/remove.svg"))
        button.setToolTip("Игнорировать: скрыть это расхождение (запоминается для этой выписки)")
        button.clicked.connect(partial(self.hide_entries, keys))
        self.ui.tw_discrepancies.setCellWidget(row, self.IGNORE_COLUMN, button)

    def create_payment(self, amount: Decimal, fee_date: date):
        self.create_event(amount, fee_date, self)
        self.reconcile()

    def edit_calendar_payment(self, entry: PaymentEntry, fee_date: date):
        self.edit_event(entry, fee_date, self)
        self.reconcile()

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
        button.setToolTip("Считать эти платежи сверенными: группа исчезнет из расхождений (запоминается для этой выписки)")
        button.clicked.connect(partial(self.hide_entries, (group.key,)))
        table.setCellWidget(row, self.BUTTON_COLUMN, button)

    def accept_statement_amount(self, pair: ProbablePair):
        if not self.dbh.correct_payment_sum(pair.calendar.payment_id, pair.statement.amount):
            ErrorInfoMessageBox("Не удалось изменить сумму платежа (подробнее см. лог)").exec()
            return
        self.reconcile()
