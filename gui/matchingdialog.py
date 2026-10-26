import hashlib
import html
import json
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Callable

import lovely_logger as log

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QMenu, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem, QToolButton, QWidget)

from gui.manualdialog import add_help_shortcut
from base.dbhandler import DBHandler
from base.edition import is_viewer
from base.feeparser import CSVParseError
from base.formatting import (dec_html, dec_strcommaspace, records_word, COLOR_STATEMENT, COLOR_CALENDAR,
                             COLOR_HEADER_BG, COLOR_OK, COLOR_WARNING)
from base.payment import PaymentEntry
from base.paymentmacther import (reconcile_statement_with_calendar, ReconciliationMarks, ReconciliationResult,
                                 ProbablePair, RegroupedPayments, ManualLink)
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.ui.matchingdialog_ui import Ui_matchingdialog


SORT_ROLE = Qt.ItemDataRole.UserRole
KEY_ROLE = Qt.ItemDataRole.UserRole + 1
RIGHT_ALIGN = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
CENTER_ALIGN = Qt.AlignmentFlag.AlignCenter
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.5
SAVED_FILES_LIMIT = 10
MAX_DESCR_LENGTH = 200
MAX_PROPOSALS_TABLE_HEIGHT = 200
DEFAULT_HEIGHT = 480
MIN_LIST_ROWS = 5
MAX_LIST_ROWS = 7
EMPTY_HINT = "<p align='center' style='font-size:14pt;'>Выберите CSV-файл выписки или перетащите его в это окно</p>"


class SortItem(QTableWidgetItem):

    def __lt__(self, other):
        return self.data(SORT_ROLE) < other.data(SORT_ROLE)


def shorten(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_DESCR_LENGTH else text[:MAX_DESCR_LENGTH].rstrip() + "…"


class MatchingDialog(QDialog):

    PROPOSAL_HEADERS = ("Дата", "В выписке", "Назначение платежа", "Разница", "В календаре", "Платеж в календаре",
                        "Совпадение", "Действие")
    LIST_HEADERS = ("Дата", "Сумма", "Назначение")
    HIDDEN_HEADERS = ("Где", "Дата", "Сумма", "Назначение платежа")
    LINKED_HEADERS = ("В выписке", "Назначение платежа", "Разница", "В календаре", "Платеж в календаре")
    DIFFERENCE_COLUMN = 3
    CONFIDENCE_COLUMN = 6
    ACTION_COLUMN = 7

    def __init__(self, settings_handler, db_handler, create_event: Callable[[Decimal, date, QDialog], bool],
                 edit_event: Callable[[PaymentEntry, Decimal | None, QDialog], bool],
                 create_fees: Callable[[str, dict, QDialog], None], parent=None):
        super(MatchingDialog, self).__init__(parent)
        self.ui = Ui_matchingdialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "09-statement-matching.html")
        self.setAcceptDrops(True)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler
        self.create_event: Callable[[Decimal, date, QDialog], bool] = create_event
        self.edit_event: Callable[[PaymentEntry, Decimal | None, QDialog], bool] = edit_event
        self.create_fees: Callable[[str, dict, QDialog], None] = create_fees

        self.match_result: ReconciliationResult | None = None
        self.csv_path: str = ""
        self.csv_hash: str = ""
        self.marks: ReconciliationMarks = ReconciliationMarks()
        self.entries_by_key: dict[str, PaymentEntry] = {}
        self.refilling: bool = False
        self.refreshed_at: datetime = datetime.now()
        self.proposals_extra_height: int = 0

        self.difference_font: QFont = QFont(self.font())
        self.difference_font.setBold(True)

        self.setup_table(self.ui.tw_proposals, self.PROPOSAL_HEADERS, (2, 5), {1: COLOR_STATEMENT, 2: COLOR_STATEMENT,
                                                                                4: COLOR_CALENDAR, 5: COLOR_CALENDAR},
                         keep_selection_color=False)
        self.setup_table(self.ui.tw_statement, self.LIST_HEADERS, (2,), {1: COLOR_STATEMENT, 2: COLOR_STATEMENT})
        self.setup_table(self.ui.tw_calendar, self.LIST_HEADERS, (2,), {1: COLOR_CALENDAR, 2: COLOR_CALENDAR})
        self.setup_table(self.ui.tw_hidden, self.HIDDEN_HEADERS, (3,))
        self.setup_table(self.ui.tw_linked, self.LINKED_HEADERS, (1, 4), {0: COLOR_STATEMENT, 1: COLOR_STATEMENT,
                                                                          3: COLOR_CALENDAR, 4: COLOR_CALENDAR})
        self.ui.tw_proposals.horizontalHeader().setSectionResizeMode(self.ACTION_COLUMN, QHeaderView.ResizeMode.Fixed)
        self.ui.tw_proposals.horizontalHeader().resizeSection(self.ACTION_COLUMN, 190)
        for table in (self.ui.tw_proposals, self.ui.tw_statement, self.ui.tw_calendar, self.ui.tw_hidden,
                      self.ui.tw_linked):
            copy_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Copy), table)
            copy_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            copy_shortcut.activated.connect(partial(self.copy_rows, table))

        self.ui.pb_close.clicked.connect(self.close)
        self.ui.pb_opencsv.clicked.connect(self.open_csv)
        self.ui.pb_refresh.clicked.connect(self.reconcile)
        self.ui.pb_link.clicked.connect(self.link_selected)
        self.ui.pb_hide.clicked.connect(self.hide_selected)
        self.ui.pb_create.clicked.connect(self.create_selected)
        self.ui.pb_open.clicked.connect(self.open_selected)
        self.ui.tb_resolved.toggled.connect(self.toggle_resolved)
        self.ui.pb_unlink.clicked.connect(self.unlink_selected)
        self.ui.pb_restore.clicked.connect(self.restore_selected)
        self.ui.pb_restoreall.clicked.connect(self.restore_hidden)
        self.ui.tw_statement.itemSelectionChanged.connect(self.update_selection_state)
        self.ui.tw_calendar.itemSelectionChanged.connect(self.update_selection_state)
        self.ui.tw_linked.itemSelectionChanged.connect(self.update_resolved_buttons)
        self.ui.tw_hidden.itemSelectionChanged.connect(self.update_resolved_buttons)
        self.ui.le_searchstatement.textChanged.connect(partial(self.apply_search, self.ui.tw_statement))
        self.ui.le_searchcalendar.textChanged.connect(partial(self.apply_search, self.ui.tw_calendar))

        self.ui.la_summary.linkActivated.connect(self.show_resolved_tab)

        for button in self.findChildren(QPushButton):
            button.setAutoDefault(False)
        self.set_data_available(False)
        self.ui.la_summary.setText(EMPTY_HINT)
        self.update_selection_state()
        self.ui.la_file.setMinimumWidth(50)

        if is_viewer():
            self.ui.pb_create.hide()
            self.ui.pb_open.setText("Открыть платеж")

        self.restore_layout()
        self.finished.connect(self.save_layout)

    def set_data_available(self, available: bool):
        self.ui.spl_main.setEnabled(available)
        if not available:
            self.ui.gb_proposals.hide()
            self.ui.tb_resolved.hide()
        self.ui.pb_refresh.setEnabled(available)
        font = self.ui.pb_opencsv.font()
        font.setBold(not available)
        self.ui.pb_opencsv.setFont(font)

    def show_resolved_tab(self, target: str):
        self.ui.tb_resolved.setChecked(True)
        self.ui.tab_resolved.setCurrentWidget(self.ui.tab_linked if target == "linked" else self.ui.tab_hidden)

    def update_file_label(self):
        if not self.csv_path:
            return
        prefix = "Файл выписки: "
        period = self.match_result.period if self.match_result else None
        suffix = (f", период {period[0]:%d.%m.%Y} – {period[1]:%d.%m.%Y}" if period else "") + \
                 f", обновлено {self.refreshed_at:%H:%M}"
        metrics = self.ui.la_file.fontMetrics()
        free = self.ui.la_file.width() - metrics.horizontalAdvance(prefix + suffix) - 30
        name = metrics.elidedText(Path(self.csv_path).name, Qt.TextElideMode.ElideMiddle, max(free, 100))
        self.ui.la_file.setText(f"{prefix}<b>{html.escape(name)}</b>{suffix}")
        self.ui.la_file.setToolTip(self.csv_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_file_label()

    def setup_table(self, table: QTableWidget, headers: tuple[str, ...], stretch_columns: tuple[int, ...],
                    colors: dict[int, str] | None = None, keep_selection_color: bool = True):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header_font = header.font()
        header_font.setBold(True)
        header.setFont(header_font)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for column in stretch_columns:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        for column, color in (colors or {}).items():
            table.horizontalHeaderItem(column).setForeground(QBrush(QColor(color)))
        if not keep_selection_color:
            return
        palette = table.palette()
        for role in (QPalette.ColorRole.Highlight, QPalette.ColorRole.HighlightedText):
            palette.setColor(QPalette.ColorGroup.Inactive, role, palette.color(QPalette.ColorGroup.Active, role))
        table.setPalette(palette)

    def restore_layout(self):
        geometry = self.sh.settings.value("Matching/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            if not self.isMaximized():
                self.resize(self.width(), DEFAULT_HEIGHT)
        self.ui.spl_lists.setSizes([1, 1])
        state = self.sh.settings.value("Matching/listssplitter")
        if state:
            self.ui.spl_lists.restoreState(state)

    def toggle_resolved(self, checked: bool):
        self.ui.tab_resolved.setVisible(checked)
        self.ui.tb_resolved.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

    def save_layout(self):
        self.resize_height(-self.proposals_extra_height)
        self.proposals_extra_height = 0
        self.sh.settings.setValue("Matching/geometry", self.saveGeometry())
        self.sh.settings.setValue("Matching/listssplitter", self.ui.spl_lists.saveState())

    def resize_height(self, delta: int) -> int:
        if delta == 0 or self.isMaximized() or self.isFullScreen():
            return 0
        available = self.screen().availableGeometry().height()
        height_before = self.height()
        self.resize(self.width(), max(min(height_before + delta, available), 0))
        return self.height() - height_before

    def lists_height(self) -> int:
        statement, calendar = self.ui.tw_statement, self.ui.tw_calendar
        rows = min(max(statement.rowCount(), calendar.rowCount(), MIN_LIST_ROWS), MAX_LIST_ROWS)

        def table_height(table: QTableWidget) -> int:
            header = table.verticalHeader()
            body = sum(header.sectionSize(row) if row < table.rowCount() else header.defaultSectionSize()
                       for row in range(rows))
            return table.horizontalHeader().height() + body + 2 * table.frameWidth()

        return (self.ui.w_unmatched.sizeHint().height() - statement.sizeHint().height()
                + max(table_height(statement), table_height(calendar)))

    def fit_lists_height(self):
        splitter = self.ui.spl_main
        self.layout().activate()
        proposals_size, lists_size = splitter.sizes()
        needed = self.lists_height()
        self.resize_height(needed - lists_size)
        self.layout().activate()
        splitter.setSizes([proposals_size, needed])

    def proposals_height(self) -> int:
        table = self.ui.tw_proposals
        content = table.horizontalHeader().height() + table.verticalHeader().length() + 2 * table.frameWidth()
        group = self.ui.gb_proposals
        return min(content, MAX_PROPOSALS_TABLE_HEIGHT) + group.sizeHint().height() - table.sizeHint().height()

    def update_proposals_visibility(self):
        group, splitter = self.ui.gb_proposals, self.ui.spl_main
        if self.ui.tw_proposals.rowCount() == 0:
            group.hide()
            self.proposals_extra_height += self.resize_height(-self.proposals_extra_height)
            return
        self.layout().activate()
        lists_height = splitter.sizes()[1]
        group.show()
        self.layout().activate()
        self.ui.tw_proposals.resizeRowsToContents()
        needed = max(self.proposals_height(), self.proposals_extra_height - splitter.handleWidth())
        self.proposals_extra_height += self.resize_height(needed + splitter.handleWidth() - self.proposals_extra_height)
        self.layout().activate()
        splitter.setSizes([needed, lists_height])

    @staticmethod
    def dropped_csv(event) -> str:
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".csv"):
                return url.toLocalFile()
        return ""

    def dragEnterEvent(self, event):
        if self.dropped_csv(event):
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = self.dropped_csv(event)
        if file_path:
            event.acceptProposedAction()
            self.load_csv(file_path)

    def open_csv(self):
        last_path = self.sh.settings.value("CSVparser/lastloadpath")
        file_path: str = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выберите выписку",
            dir=last_path if last_path and Path(last_path).is_dir() else "",
            filter="Файл выписки в формате CSV (*.csv)", )[0]
        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path: str):
        try:
            csv_hash = hashlib.sha1(Path(file_path).read_bytes()).hexdigest()
        except OSError as exc:
            log.w(f"Не удалось прочитать CSV-файл выписки: {exc}")
            ErrorInfoMessageBox("Не удалось прочитать CSV-файл. Проверьте, что файл не открыт в другой программе и это выписка банка (см. подробнее лог)", parent=self).exec()
            return

        previous = self.csv_path, self.csv_hash, self.marks
        self.csv_path, self.csv_hash = file_path, csv_hash
        self.marks = self.load_marks()
        if not self.reconcile():
            self.csv_path, self.csv_hash, self.marks = previous
            return
        self.sh.settings.setValue("CSVparser/lastloadpath", str(Path(file_path).parent))
        self.set_data_available(True)
        self.fit_lists_height()

    def read_saved_marks(self) -> dict:
        try:
            saved = json.loads(self.sh.settings.value("Matching/state") or "{}")
        except ValueError:
            return {}
        return saved if isinstance(saved, dict) else {}

    def load_marks(self) -> ReconciliationMarks:
        saved = self.read_saved_marks().get(self.csv_hash, {})
        try:
            return ReconciliationMarks(set(saved.get("hidden", [])), [tuple(keys) for keys in saved.get("links", [])],
                                       set(saved.get("rejected", [])))
        except (AttributeError, TypeError, ValueError) as e:
            log.w(f"Пометки сверки для выписки повреждены и не загружены: {e!r}")
            return ReconciliationMarks()

    def save_marks(self):
        state = self.read_saved_marks()
        state.pop(self.csv_hash, None)
        state[self.csv_hash] = {"hidden": sorted(self.marks.hidden), "links": [list(keys) for keys in self.marks.links],
                                "rejected": sorted(self.marks.rejected)}
        while len(state) > SAVED_FILES_LIMIT:
            del state[next(iter(state))]
        self.sh.settings.setValue("Matching/state", json.dumps(state))

    def marks_changed(self):
        self.save_marks()
        self.reconcile()

    def reconcile(self) -> bool:
        try:
            result = reconcile_statement_with_calendar(self.csv_path, self.dbh, self.marks)
        except CSVParseError as exc:
            log.w(f"Не удалось прочитать CSV-файл выписки: {exc}")
            ErrorInfoMessageBox(f"Не удалось прочитать CSV-файл: {exc}", parent=self).exec()
            return False
        except Exception as exc:
            log.x(f"Не удалось обработать CSV-файл: {exc}")
            ErrorInfoMessageBox("Не удалось обработать CSV-файл (см. подробнее лог)", parent=self).exec()
            return False
        if result is None:
            ErrorInfoMessageBox("В процессе обработки CSV-файла произошла ошибка (см. лог)", parent=self).exec()
            return False

        self.match_result = result
        self.refreshed_at = datetime.now()
        self.update_file_label()
        self.print_report()
        return True

    @staticmethod
    @contextmanager
    def fixed_headers(tables):
        saved = []
        for table in tables:
            vertical = table.verticalHeader()
            horizontal = table.horizontalHeader()
            saved.append((vertical, horizontal, [horizontal.sectionResizeMode(column) for column in range(horizontal.count())]))
            vertical.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            horizontal.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        try:
            yield
        finally:
            for vertical, horizontal, modes in saved:
                vertical.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                for column, mode in enumerate(modes):
                    horizontal.setSectionResizeMode(column, mode)

    def print_report(self):
        result = self.match_result
        tables = (self.ui.tw_proposals, self.ui.tw_statement, self.ui.tw_calendar, self.ui.tw_linked,
                  self.ui.tw_hidden)
        scroll_positions = [table.verticalScrollBar().value() for table in tables]

        self.refilling = True
        try:
            with self.fixed_headers(tables):
                self.entries_by_key.clear()
                self.ui.la_summary.setText(result.format_summary())
                self.fill_proposals(result)
                self.fill_entry_list(self.ui.tw_statement, result.unmatched_statement, COLOR_STATEMENT)
                self.fill_entry_list(self.ui.tw_calendar, result.unmatched_calendar, COLOR_CALENDAR)
                self.fill_linked(result.links)
                self.fill_hidden(result)
            self.apply_search(self.ui.tw_statement, self.ui.le_searchstatement.text())
            self.apply_search(self.ui.tw_calendar, self.ui.le_searchcalendar.text())
        finally:
            self.refilling = False

        entries_count = result.proposal_entries_count
        self.update_proposals_visibility()
        self.ui.gb_proposals.setTitle(f"Предложения по сопоставлению ({self.ui.tw_proposals.rowCount()} — "
                                      f"{entries_count} {records_word(entries_count)})")
        self.ui.gb_statement.setTitle(f"Только в выписке ({self.ui.tw_statement.rowCount()})")
        self.ui.gb_calendar.setTitle(f"Только в календаре ({self.ui.tw_calendar.rowCount()})")
        self.ui.tab_resolved.setTabText(0, f"Связано вручную ({len(result.links)})")
        self.ui.tab_resolved.setTabText(1, f"Скрытые ({len(result.hidden_entries)})")
        self.ui.tb_resolved.setText(f"Связано вручную: {len(result.links)}, скрыто: {len(result.hidden_entries)}")
        self.ui.pb_restoreall.setEnabled(bool(self.marks.hidden))
        has_resolved = bool(result.links or result.hidden_entries)
        self.ui.tb_resolved.setVisible(has_resolved)
        self.ui.tab_resolved.setVisible(has_resolved and self.ui.tb_resolved.isChecked())
        self.update_selection_state()
        self.update_resolved_buttons()

        for table, position in zip(tables, scroll_positions):
            table.verticalScrollBar().setValue(position)

    def set_cell(self, table: QTableWidget, row: int, column: int, text: str, color: str | None = None,
                 align: Qt.AlignmentFlag | None = None, tooltip: str = "", sort_value=None, key: str | None = None,
                 background: str | None = None, bold: bool = False):
        item = QTableWidgetItem(text) if sort_value is None else SortItem(text)
        if sort_value is not None:
            item.setData(SORT_ROLE, sort_value)
        if key is not None:
            item.setData(KEY_ROLE, key)
        if tooltip:
            item.setToolTip(tooltip)
        if color:
            item.setForeground(QBrush(QColor(color)))
        if align:
            item.setTextAlignment(align)
        if background:
            item.setBackground(QBrush(QColor(background)))
        if bold:
            item.setFont(self.difference_font)
        table.setItem(row, column, item)

    def set_descr_cell(self, table: QTableWidget, row: int, column: int, text: str, color: str):
        shown = shorten(text)
        self.set_cell(table, row, column, shown, color, tooltip=text if shown != text else "")

    def fill_proposals(self, result: ReconciliationResult):
        table = self.ui.tw_proposals
        table.setRowCount(0)
        for d in result.discrepancies:
            for pair in d.probable_pairs:
                self.add_pair_row(pair)
            for group in d.groups:
                self.add_group_row(group)

    @staticmethod
    def confidence_text(confidence: float) -> tuple[str, str | None]:
        if confidence >= CONFIDENCE_HIGH:
            return "Высокое", COLOR_OK
        if confidence >= CONFIDENCE_MEDIUM:
            return "Среднее", COLOR_WARNING
        return "Низкое", None

    def add_pair_row(self, pair: ProbablePair):
        table = self.ui.tw_proposals
        row = table.rowCount()
        table.insertRow(row)
        statement_entry, calendar_entry = pair.statement, pair.calendar
        sign = "+" if pair.difference > 0 else ""
        level, level_color = self.confidence_text(pair.confidence)
        reasons = ", ".join(pair.reasons) or "слабые признаки"

        self.set_cell(table, row, 0, statement_entry.fee_date.strftime("%d.%m.%Y"))
        self.set_cell(table, row, 1, dec_strcommaspace(statement_entry.amount), COLOR_STATEMENT, RIGHT_ALIGN)
        self.set_descr_cell(table, row, 2, statement_entry.descr, COLOR_STATEMENT)
        self.set_cell(table, row, self.DIFFERENCE_COLUMN, sign + dec_strcommaspace(pair.difference), None, CENTER_ALIGN,
                      background=COLOR_HEADER_BG, bold=True)
        self.set_cell(table, row, 4, dec_strcommaspace(calendar_entry.amount), COLOR_CALENDAR, RIGHT_ALIGN)
        self.set_descr_cell(table, row, 5, calendar_entry.descr, COLOR_CALENDAR)
        self.set_cell(table, row, self.CONFIDENCE_COLUMN, f"{level}\n{pair.confidence:.0%}", level_color, CENTER_ALIGN,
                      tooltip=f"Совпало: {reasons}")

        link_action = ("Сверено, суммы не менять", partial(self.link_keys, (statement_entry.key, calendar_entry.key)))
        other_actions = [("Это не пара", partial(self.reject_proposal, pair.key)),
                         ("Скрыть", partial(self.hide_keys, (statement_entry.key, calendar_entry.key)))]
        if is_viewer():
            table.setCellWidget(row, self.ACTION_COLUMN, self.make_actions(
                "Сверено", "Считать эти записи сверенными (запоминается для этой выписки)", link_action[1],
                other_actions))
        else:
            table.setCellWidget(row, self.ACTION_COLUMN, self.make_actions(
                "Принять сумму",
                f"Сумма платежа в календаре будет изменена: {dec_strcommaspace(calendar_entry.amount)} → "
                f"{dec_strcommaspace(statement_entry.amount)}",
                partial(self.accept_statement_amount, pair),
                [link_action] + other_actions))

    def add_group_row(self, group: RegroupedPayments):
        table = self.ui.tw_proposals
        row = table.rowCount()
        table.insertRow(row)
        tooltip = "Суммы группы равны, но платежи разбиты по-разному. Проверьте расчёт:\n" + group.explanation

        def lines(entries: list[PaymentEntry]) -> str:
            return "\n".join(f"{dec_strcommaspace(e.amount)} — {shorten(e.descr)}" for e in entries)

        zero = Decimal("0")
        self.set_cell(table, row, 0, group.fee_date.strftime("%d.%m.%Y"), tooltip=tooltip)
        self.set_cell(table, row, 1, dec_strcommaspace(sum((e.amount for e in group.statement), zero)), COLOR_STATEMENT,
                      RIGHT_ALIGN, tooltip)
        self.set_cell(table, row, 2, lines(group.statement), COLOR_STATEMENT, tooltip=tooltip)
        self.set_cell(table, row, self.DIFFERENCE_COLUMN, dec_strcommaspace(zero), None, CENTER_ALIGN, tooltip,
                      background=COLOR_HEADER_BG, bold=True)
        self.set_cell(table, row, 4, dec_strcommaspace(sum((e.amount for e in group.calendar), zero)), COLOR_CALENDAR,
                      RIGHT_ALIGN, tooltip)
        self.set_cell(table, row, 5, lines(group.calendar), COLOR_CALENDAR, tooltip=tooltip)
        self.set_cell(table, row, self.CONFIDENCE_COLUMN, "Группа\nсуммы равны", COLOR_OK, CENTER_ALIGN, tooltip)

        keys = tuple(e.key for e in group.statement + group.calendar)
        table.setCellWidget(row, self.ACTION_COLUMN, self.make_actions(
            "Сверено",
            "Считать эти платежи сверенными: группа исчезнет из расхождений (запоминается для этой выписки)",
            partial(self.link_keys, keys),
            [("Показать расчёт", partial(self.show_explanation, group.explanation)),
             ("Это не группа", partial(self.reject_proposal, group.key))]))

    @staticmethod
    def make_actions(primary_text: str, primary_tooltip: str, primary_slot: Callable,
                     extra: list[tuple[str, Callable]]) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        primary = QPushButton(primary_text)
        primary.setAutoDefault(False)
        primary.setToolTip(primary_tooltip)
        primary.clicked.connect(primary_slot)
        layout.addWidget(primary, 1)
        menu = QMenu(widget)
        for text, slot in extra:
            menu.addAction(text).triggered.connect(slot)
        more = QToolButton()
        more.setText("Ещё")
        more.setToolTip("Другие действия с этим совпадением")
        more.setMenu(menu)
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        more.setMinimumWidth(56)
        layout.addWidget(more)
        return widget

    def fill_entry_list(self, table: QTableWidget, entries: list[PaymentEntry], color: str):
        table.setSortingEnabled(False)
        table.setRowCount(0)
        for entry in entries:
            self.entries_by_key[entry.key] = entry
            row = table.rowCount()
            table.insertRow(row)
            self.set_cell(table, row, 0, entry.fee_date.strftime("%d.%m.%Y"), sort_value=entry.fee_date.toordinal(),
                          key=entry.key)
            self.set_cell(table, row, 1, dec_strcommaspace(entry.amount), color, RIGHT_ALIGN,
                          sort_value=float(entry.amount))
            self.set_descr_cell(table, row, 2, entry.descr, color)
        table.setSortingEnabled(True)
        table.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def fill_hidden(self, result: ReconciliationResult):
        table = self.ui.tw_hidden
        table.setRowCount(0)
        for entry in result.hidden_entries:
            self.entries_by_key[entry.key] = entry
            color = COLOR_STATEMENT if entry.from_statement else COLOR_CALENDAR
            row = table.rowCount()
            table.insertRow(row)
            self.set_cell(table, row, 0, "Выписка" if entry.from_statement else "Календарь", color, key=entry.key)
            self.set_cell(table, row, 1, entry.fee_date.strftime("%d.%m.%Y"))
            self.set_cell(table, row, 2, dec_strcommaspace(entry.amount), color, RIGHT_ALIGN)
            self.set_descr_cell(table, row, 3, entry.descr, color)

    def fill_linked(self, links: list[ManualLink]):
        table = self.ui.tw_linked
        table.setRowCount(0)

        def lines(entries: list[PaymentEntry]) -> str:
            return "\n".join(f"{e.fee_date.strftime('%d.%m.%Y')}  {shorten(e.descr)}" for e in entries)

        def amounts(entries: list[PaymentEntry]) -> str:
            return "\n".join(dec_strcommaspace(e.amount) for e in entries)

        for link in sorted(links, key=lambda l: min(e.fee_date for e in l.statement + l.calendar)):
            row = table.rowCount()
            table.insertRow(row)
            sign = "+" if link.difference > 0 else ""
            self.set_cell(table, row, 0, amounts(link.statement), COLOR_STATEMENT, RIGHT_ALIGN,
                          key=json.dumps(list(link.keys)))
            self.set_cell(table, row, 1, lines(link.statement), COLOR_STATEMENT)
            self.set_cell(table, row, 2, sign + dec_strcommaspace(link.difference), None, CENTER_ALIGN,
                          background=COLOR_HEADER_BG, bold=True)
            self.set_cell(table, row, 3, amounts(link.calendar), COLOR_CALENDAR, RIGHT_ALIGN)
            self.set_cell(table, row, 4, lines(link.calendar), COLOR_CALENDAR)

    @staticmethod
    def search_text(entry: PaymentEntry) -> str:
        plain = f"{entry.amount:.2f}"
        return " ".join((entry.fee_date.strftime("%d.%m.%Y"), dec_strcommaspace(entry.amount), plain,
                         plain.replace(".", ","), entry.descr)).lower()

    def apply_search(self, table: QTableWidget, text: str):
        query = text.strip().lower()
        for row in range(table.rowCount()):
            entry = self.entries_by_key[table.item(row, 0).data(KEY_ROLE)]
            matches = query in self.search_text(entry)
            table.setRowHidden(row, not matches)
            if not matches:
                table.selectionModel().select(table.model().index(row, 0),
                                              QItemSelectionModel.SelectionFlag.Deselect
                                              | QItemSelectionModel.SelectionFlag.Rows)
        self.update_selection_state()

    def selected_entries(self, table: QTableWidget) -> list[PaymentEntry]:
        rows = sorted({index.row() for index in table.selectionModel().selectedRows()})
        return [self.entries_by_key[table.item(row, 0).data(KEY_ROLE)] for row in rows if not table.isRowHidden(row)]

    def update_selection_state(self):
        if self.refilling:
            return
        statement_entries = self.selected_entries(self.ui.tw_statement)
        calendar_entries = self.selected_entries(self.ui.tw_calendar)
        zero = Decimal("0")
        statement_sum = sum((e.amount for e in statement_entries), zero)
        calendar_sum = sum((e.amount for e in calendar_entries), zero)
        difference = statement_sum - calendar_sum

        if statement_entries or calendar_entries:
            difference_color = COLOR_OK if difference == 0 else COLOR_WARNING
            self.ui.la_selection.setText(
                f"Выбрано: в выписке <b>{len(statement_entries)}</b> на <b>{dec_html(statement_sum)}</b>, "
                f"в календаре <b>{len(calendar_entries)}</b> на <b>{dec_html(calendar_sum)}</b>, "
                f"разница <b style='color:{difference_color};'>{dec_html(difference)}</b>")
        else:
            self.ui.la_selection.clear()

        self.set_button_state(
            self.ui.pb_link, bool(statement_entries and calendar_entries),
            "Считать выбранные записи выписки и календаря одним и тем же платежом (можно с разными датами)",
            "Выберите записи и в списке «Только в выписке», и в списке «Только в календаре»")
        self.set_button_state(
            self.ui.pb_hide, bool(statement_entries or calendar_entries),
            "Убрать выбранные записи из списков (запоминается для этой выписки)",
            "Выберите записи в списках «Только в выписке» или «Только в календаре»")
        can_create = len(statement_entries) == 1 and not calendar_entries
        self.set_button_state(
            self.ui.pb_create, can_create,
            "Открыть окно создания платежей по комиссиям из этой выписки" if can_create
            and statement_entries[0].fee_category else "Создать в календаре новый платеж с суммой из выписки",
            "Выберите одну запись в списке «Только в выписке» (в списке календаря ничего выбранного быть не должно)")
        self.set_button_state(
            self.ui.pb_open, len(calendar_entries) == 1 and not statement_entries
            and calendar_entries[0].event_id is not None,
            "Открыть платеж, к которому относится выбранная оплата из календаря" if is_viewer()
            else "Изменить сумму выбранной оплаты из календаря (и, при необходимости, общую сумму платежа)",
            "Выберите один платеж в списке «Только в календаре» (в списке выписки ничего выбранного быть не должно)")

    @staticmethod
    def set_button_state(button: QPushButton, enabled: bool, enabled_tooltip: str, disabled_tooltip: str):
        button.setEnabled(enabled)
        button.setToolTip(enabled_tooltip if enabled else disabled_tooltip)

    def update_resolved_buttons(self):
        if self.refilling:
            return
        self.ui.pb_unlink.setEnabled(bool(self.ui.tw_linked.selectionModel().selectedRows()))
        self.ui.pb_restore.setEnabled(bool(self.ui.tw_hidden.selectionModel().selectedRows()))

    def copy_rows(self, table: QTableWidget):
        rows = sorted({index.row() for index in table.selectionModel().selectedRows()})
        lines = ["\t".join(table.item(row, column).text().replace("\n", " ") if table.item(row, column) else ""
                           for column in range(table.columnCount())) for row in rows]
        QApplication.clipboard().setText("\n".join(lines))

    def link_selected(self):
        statement_entries = self.selected_entries(self.ui.tw_statement)
        calendar_entries = self.selected_entries(self.ui.tw_calendar)
        if not (statement_entries and calendar_entries):
            return
        zero = Decimal("0")
        statement_sum = sum((e.amount for e in statement_entries), zero)
        calendar_sum = sum((e.amount for e in calendar_entries), zero)
        can_correct = len(statement_entries) == 1 and len(calendar_entries) == 1 and not is_viewer()

        if statement_sum != calendar_sum:
            choice = self.ask_link_with_difference(statement_sum, calendar_sum, can_correct)
            if choice is None:
                return
            if choice == "correct" and not self.edit_event(calendar_entries[0], statement_entries[0].amount, self):
                return
        self.link_keys(tuple(e.key for e in statement_entries + calendar_entries))

    def ask_link_with_difference(self, statement_sum: Decimal, calendar_sum: Decimal, can_correct: bool) -> str | None:
        difference = statement_sum - calendar_sum
        text = (f"Суммы различаются: в выписке {dec_strcommaspace(statement_sum, add_rub=True)}, "
                f"в календаре {dec_strcommaspace(calendar_sum, add_rub=True)} "
                f"(разница {dec_strcommaspace(difference, add_rub=True)}).")
        box = QMessageBox(QMessageBox.Icon.Question, "Суммы различаются", text, parent=self)
        correct_button = None
        if can_correct:
            correct_button = box.addButton(f"Изменить сумму в календаре на {dec_strcommaspace(statement_sum)}",
                                           QMessageBox.ButtonRole.AcceptRole)
        link_button = box.addButton("Связать без изменения сумм", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if correct_button is not None and box.clickedButton() is correct_button:
            return "correct"
        if box.clickedButton() is link_button:
            return "link"
        return None

    def show_explanation(self, text: str):
        ErrorInfoMessageBox(text, is_info=True, parent=self).exec()

    def link_keys(self, keys: tuple[str, ...]):
        self.marks.links.append(keys)
        self.marks_changed()

    def reject_proposal(self, key: str):
        self.marks.rejected.add(key)
        self.marks_changed()

    def hide_keys(self, keys: tuple[str, ...]):
        self.marks.hidden.update(keys)
        self.marks_changed()

    def hide_selected(self):
        entries = (self.selected_entries(self.ui.tw_statement) + self.selected_entries(self.ui.tw_calendar))
        if entries:
            self.hide_keys(tuple(e.key for e in entries))

    def restore_selected(self):
        table = self.ui.tw_hidden
        rows = {index.row() for index in table.selectionModel().selectedRows()}
        self.marks.hidden.difference_update(table.item(row, 0).data(KEY_ROLE) for row in rows)
        self.marks_changed()

    def restore_hidden(self):
        self.marks.hidden.clear()
        self.marks_changed()

    def unlink_selected(self):
        table = self.ui.tw_linked
        for index in table.selectionModel().selectedRows():
            keys = tuple(json.loads(table.item(index.row(), 0).data(KEY_ROLE)))
            if keys in self.marks.links:
                self.marks.links.remove(keys)
        self.marks_changed()

    def create_selected(self):
        entry = self.selected_entries(self.ui.tw_statement)[0]
        if entry.fee_category:
            self.make_fee_payments()
        else:
            self.create_payment(entry.amount, entry.fee_date)

    def open_selected(self):
        entry = self.selected_entries(self.ui.tw_calendar)[0]
        self.edit_calendar_payment(entry)

    def create_payment(self, amount: Decimal, fee_date: date):
        self.create_event(amount, fee_date, self)
        self.reconcile()

    def edit_calendar_payment(self, entry: PaymentEntry, new_amount: Decimal | None = None):
        self.edit_event(entry, new_amount, self)
        self.reconcile()

    def make_fee_payments(self):
        self.create_fees(self.csv_path, self.match_result.fee_totals, self)
        self.reconcile()

    def accept_statement_amount(self, pair: ProbablePair):
        self.edit_calendar_payment(pair.calendar, pair.statement.amount)
