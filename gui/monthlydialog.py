from decimal import Decimal
from typing import Callable

from PySide6.QtCore import QDate, QModelIndex, QSettings, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QStandardItemModel
from PySide6.QtWidgets import QDialog, QHeaderView, QPushButton, QStyle, QStyledItemDelegate, QTableWidgetItem, QWidget

from base.date import MONTHS_RU, date_displstr
from base.contract import DocumentTitle
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.liability import Col, FilterFlags, RowType
from base.monthly import HiddenMonthly, MonthlyEntry, MonthlyState, MonthlyTemplate, first_of_month, planned_due_date
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.liabilitytablemodel import LiabilityTableModel
from gui.manualdialog import add_help_shortcut
from gui.ui.monthlydialog_ui import Ui_MonthlyDialog


def template_model(template: MonthlyTemplate) -> QStandardItemModel:
    amount = template.amount or Decimal(0)
    values = {
        Col.ID: 0, Col.TYPE: int(RowType.LIABILITY), Col.REMAINAMOUNT: amount, Col.TOTALAMOUNT: amount,
        Col.DUEDATE: template.due_date or template.incurrence_date, Col.INCURRENCEDATE: template.incurrence_date,
        Col.TODAYSHARE: Decimal(0), Col.LASTPAYMENTDATE: None, Col.FILTERFLAGS: FilterFlags.NOTPAID, Col.FEATURED: 0,
        **template.values,
    }
    model = QStandardItemModel(1, len(Col))
    for column, value in values.items():
        model.setData(model.index(0, column), value, LiabilityTableModel.qtValueRole)
    return model


class StateRowDelegate(QStyledItemDelegate):

    def initStyleOption(self, option, index, /):
        super().initStyleOption(option, index)
        if option.state & QStyle.StateFlag.State_Selected:
            option.backgroundBrush = QBrush(index.data(Qt.ItemDataRole.UserRole))
        option.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_HasFocus)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.setPen(QPen(index.data(Qt.ItemDataRole.UserRole + 1), 1))
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
            painter.restore()


class MonthlyDialog(QDialog):

    STATE_TEXT = {MonthlyState.MISSING: "не создан", MonthlyState.UNPAID: "создан, не оплачен", MonthlyState.PAID: "оплачен"}
    STATE_COLOR = {MonthlyState.MISSING: "#c0392b", MonthlyState.UNPAID: "#b9770e", MonthlyState.PAID: "#1e8449"}
    ROW_COLOR = {MonthlyState.MISSING: "#f8e6e4", MonthlyState.UNPAID: "#faf2dc", MonthlyState.PAID: "#e4f1e7"}
    SELECTED_ROW_COLOR = {MonthlyState.MISSING: "#f2e9e8", MonthlyState.UNPAID: "#f4efe2", MonthlyState.PAID: "#eaf1ec"}
    OVERDUE_COLOR = "#d00000"
    HEADERS = ("Контрагент", "Договор и документ", "Сумма", "Срок оплаты", "Статус")
    EMPTY_TEXT = ("Нет документов с отметкой ежемесячного платежа.\nВключите её в карточке документа "
                  "(Договоры → документ), и он появится в этом списке.")
    ALL_CREATED_TEXT = "Все ежемесячные платежи за этот месяц созданы ✓"
    ALL_HIDDEN_TEXT = "Все ежемесячные платежи за этот месяц скрыты"
    NO_HIDDEN_TEXT = "Скрытых платежей за этот месяц нет"
    NO_SAVED_VALUES_TEXT = "Для быстрого создания платежа заполните сохранённые поля для этого документа."

    def __init__(self, db_handler: DBHandler, create_event: Callable[[MonthlyEntry, QDate, bool, QWidget], bool],
                 open_event: Callable[[int, QWidget], bool] | None = None, settings: QSettings | None = None,
                 open_document: Callable[[DocumentTitle, QWidget], bool] | None = None, parent=None):
        super().__init__(parent)
        self.ui = Ui_MonthlyDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "08-monthly.html")

        self.dbh = db_handler
        self.create_event = create_event
        self.open_event = open_event
        self.open_document = open_document
        self.settings = settings
        self.hidden = HiddenMonthly(settings)
        self.month: QDate = first_of_month(QDate.currentDate())
        self.entries: list[MonthlyEntry] = []
        self.visible_entries: list[MonthlyEntry] = []
        self.hidden_entries: list[MonthlyEntry] = []
        self.shown: list[MonthlyEntry] = []

        table = self.ui.tbl_monthly
        table.setColumnCount(len(self.HEADERS))
        table.setHorizontalHeaderLabels(self.HEADERS)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)
        table.setColumnWidth(0, 260)
        table.setWordWrap(False)
        table.setItemDelegate(StateRowDelegate(table))

        if settings is not None:
            geometry = settings.value("Monthly/geometry")
            if geometry:
                self.restoreGeometry(geometry)
            self.ui.chb_onlymissing.setChecked(settings.value("Monthly/onlymissing", False, type=bool))

        self.ui.tb_prev.clicked.connect(lambda: self.change_month(-1))
        self.ui.tb_next.clicked.connect(lambda: self.change_month(1))
        self.ui.chb_onlymissing.toggled.connect(self.fill_table)
        self.ui.chb_hidden.toggled.connect(self.fill_table)
        table.activated.connect(self.activate_row)
        table.itemSelectionChanged.connect(self.update_buttons)
        self.ui.pb_create.clicked.connect(lambda: self.create_or_open(self.selected_entry()))
        self.ui.pb_hide.clicked.connect(self.toggle_hidden)
        self.ui.pb_opendocument.clicked.connect(self.open_entry_document)
        self.ui.pb_close.clicked.connect(self.accept)

        self.fix_button_width(self.ui.pb_create, ("Создать платеж", "Открыть платеж"))
        self.fix_button_width(self.ui.pb_hide, ("Скрыть платеж", "Вернуть платеж"))

        self.reload()

    @staticmethod
    def fix_button_width(button: QPushButton, texts: tuple[str, ...]) -> None:
        width = 0
        for text in texts:
            button.setText(text)
            width = max(width, button.sizeHint().width())
        button.setMinimumWidth(width)

    def done(self, result: int) -> None:
        if self.settings is not None:
            self.settings.setValue("Monthly/geometry", self.saveGeometry())
            self.settings.setValue("Monthly/onlymissing", self.ui.chb_onlymissing.isChecked())
        super().done(result)

    def change_month(self, step: int) -> None:
        self.set_month(self.month.addMonths(step))

    def set_month(self, month: QDate) -> None:
        self.month = month
        self.reload()

    def selected_entry(self) -> MonthlyEntry | None:
        row = self.ui.tbl_monthly.currentRow()
        return self.shown[row] if 0 <= row < len(self.shown) else None

    def update_buttons(self) -> None:
        entry = self.selected_entry()
        hidden_mode = self.ui.chb_hidden.isChecked()
        created = entry is not None and entry.event is not None
        self.ui.pb_create.setText("Открыть платеж" if created else "Создать платеж")
        self.ui.pb_create.setEnabled(entry is not None and not hidden_mode and (not created or self.open_event is not None))
        self.ui.pb_hide.setText("Вернуть платеж" if hidden_mode else "Скрыть платеж")
        self.ui.pb_hide.setEnabled(entry is not None and not created)
        self.ui.pb_opendocument.setEnabled(entry is not None and self.open_document is not None)

    def reload(self, keep_document_id: int | None = None) -> None:
        self.ui.la_month.setText(f"{MONTHS_RU[self.month.month() - 1]} {self.month.year()}")
        entries = self.dbh.load_monthly_entries(self.month)
        if entries is None:
            ErrorInfoMessageBox("Не удалось загрузить перечень ежемесячных платежей (подробности см. в логе)", parent=self).exec()
            entries = []
        self.entries = entries
        self.hidden_entries = [entry for entry in entries
                               if entry.event is None and self.hidden.is_hidden(entry.title.document_id, self.month)]
        self.visible_entries = [entry for entry in entries if entry not in self.hidden_entries]
        for entry in entries:
            if entry.event is None and not entry.relative_term:
                entry.planned_date =planned_due_date(self.dbh, entry.title.document_id, self.month)
        missing = sum(entry.state == MonthlyState.MISSING for entry in self.visible_entries)
        summary = f"Не создано: {missing} из {len(self.visible_entries)}" if self.visible_entries else ""
        if self.hidden_entries:
            summary += f" (скрыто {len(self.hidden_entries)})" if summary else f"Скрыто: {len(self.hidden_entries)}"
        self.ui.la_summary.setText(summary)
        self.fill_table(keep_document_id=keep_document_id)

    @staticmethod
    def amount_text(entry: MonthlyEntry) -> str:
        amount = entry.event.amount if entry.event is not None else entry.amount
        return dec_strcommaspace(amount) if amount else "по счёту"

    @staticmethod
    def entry_due_date(entry: MonthlyEntry) -> QDate | None:
        due_date = entry.event.due_date if entry.event is not None else entry.planned_date
        return due_date if isinstance(due_date, QDate) and due_date.isValid() else None

    def sort_key(self, entry: MonthlyEntry) -> tuple:
        due_date = self.entry_due_date(entry)
        return entry.state.value, due_date is None, due_date.toJulianDay() if due_date is not None else 0

    def is_overdue(self, entry: MonthlyEntry) -> bool:
        due_date = self.entry_due_date(entry)
        return entry.state != MonthlyState.PAID and due_date is not None and due_date < QDate.currentDate()

    def fill_table(self, *_, keep_document_id: int | None = None) -> None:
        table = self.ui.tbl_monthly
        previous_row = table.currentRow()
        if keep_document_id is None and self.selected_entry() is not None:
            keep_document_id = self.selected_entry().title.document_id
        if self.ui.chb_hidden.isChecked():
            self.shown = list(self.hidden_entries)
        else:
            only_missing = self.ui.chb_onlymissing.isChecked()
            self.shown = [entry for entry in self.visible_entries if not only_missing or entry.state == MonthlyState.MISSING]
        self.shown.sort(key=self.sort_key)
        table.setRowCount(len(self.shown))
        for row, entry in enumerate(self.shown):
            title = entry.title
            contract = f"№ {title.contract_number} от {date_displstr(title.contract_date)}"
            if entry.event is not None:
                due_date = date_displstr(entry.event.due_date)
            elif entry.relative_term:
                due_date = entry.relative_term
            else:
                due_date = date_displstr(entry.planned_date) if entry.planned_date is not None else "—"
            cells = (title.contractor_name, f"{contract} — {title.document_name}", self.amount_text(entry), due_date,
                     self.STATE_TEXT[entry.state])
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                item.setBackground(QColor(self.ROW_COLOR[entry.state]))
                item.setData(Qt.ItemDataRole.UserRole, QColor(self.SELECTED_ROW_COLOR[entry.state]))
                item.setData(Qt.ItemDataRole.UserRole + 1, QColor(self.STATE_COLOR[entry.state]))
                if column == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if column == 4:
                    item.setForeground(QColor(self.STATE_COLOR[entry.state]))
                if column == 3 and self.is_overdue(entry):
                    item.setForeground(QColor(self.OVERDUE_COLOR))
                if entry.event is None and (column == 3 and (entry.planned_date is not None or entry.relative_term) or column == 2 and entry.amount):
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                table.setItem(row, column, item)
        selected = False
        for row, entry in enumerate(self.shown):
            if entry.title.document_id == keep_document_id:
                table.selectRow(row)
                selected = True
        if not selected and self.shown and previous_row >= 0:
            table.selectRow(min(previous_row, len(self.shown) - 1))
        self.update_buttons()
        self.update_empty_state()

    def update_empty_state(self) -> None:
        if self.shown:
            self.ui.stk_monthly.setCurrentWidget(self.ui.page_table)
            return
        if self.ui.chb_hidden.isChecked():
            text = self.NO_HIDDEN_TEXT
        elif not self.entries:
            text = self.EMPTY_TEXT
        elif not self.visible_entries:
            text = self.ALL_HIDDEN_TEXT
        else:
            text = self.ALL_CREATED_TEXT
        self.ui.la_empty.setText(text)
        self.ui.stk_monthly.setCurrentWidget(self.ui.page_empty)

    def activate_row(self, index: QModelIndex) -> None:
        if 0 <= index.row() < len(self.shown):
            self.create_or_open(self.shown[index.row()])

    def create_or_open(self, entry: MonthlyEntry | None) -> None:
        if entry is None:
            return
        if entry.event is not None:
            self.open_payment(entry)
        elif not self.ui.chb_hidden.isChecked():
            self.create(entry)

    def create(self, entry: MonthlyEntry) -> None:
        if not entry.has_saved_values:
            ErrorInfoMessageBox(self.NO_SAVED_VALUES_TEXT, is_info=True, parent=self).exec()
        if self.create_event(entry, self.month, not entry.has_saved_values, self):
            self.reload(keep_document_id=entry.title.document_id)

    def toggle_hidden(self) -> None:
        entry = self.selected_entry()
        if entry is None or entry.event is not None:
            return
        if self.ui.chb_hidden.isChecked():
            self.hidden.restore(entry.title.document_id, self.month)
        else:
            self.hidden.hide(entry.title.document_id, self.month)
        self.reload()

    def open_entry_document(self) -> None:
        entry = self.selected_entry()
        if entry is None or self.open_document is None:
            return
        self.open_document(entry.title, self)
        self.reload(keep_document_id=entry.title.document_id)

    def open_payment(self, entry: MonthlyEntry | None) -> None:
        if entry is None or entry.event is None or self.open_event is None:
            return
        self.open_event(entry.event.event_id, self)
        self.reload(keep_document_id=entry.title.document_id)
