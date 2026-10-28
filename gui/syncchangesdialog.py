from PySide6.QtCore import QModelIndex, QSettings, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableView, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from gui.manualdialog import add_help_shortcut
from base.diffview import ACTION_TITLES, ACTIONS, ADDED, CHANGED, REMOVED, SECTION_TITLES, DiffEntry, build_entries, format_time, summary_lines
from base.formatting import COLOR_CALENDAR, COLOR_OK, COLOR_STATEMENT, COLOR_WARNING, COLOR_WARNING_BG
from base.syncdiff import Conflict, DETAILED_TABLES, DbDiff, describe_other_table

ENTRY_ROLE = Qt.ItemDataRole.UserRole
SORT_ROLE = Qt.ItemDataRole.UserRole + 1
ACTION_COLORS = {ADDED: COLOR_OK, CHANGED: COLOR_WARNING, REMOVED: COLOR_STATEMENT}


class DiffFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.actions: set[str] = set(ACTIONS)
        self.table: str = ""
        self.text: str = ""
        self.setSortRole(SORT_ROLE)

    def set_filters(self, actions: set[str], table: str, text: str) -> None:
        self.beginFilterChange()
        self.actions, self.table, self.text = actions, table, text
        self.endFilterChange()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        entry: DiffEntry = self.sourceModel().index(source_row, 0, source_parent).data(ENTRY_ROLE)
        return (entry.action in self.actions and (not self.table or self.table in entry.tables)
                and self.text in entry.title.casefold())


class DiffView(QWidget):
    eventActivated = Signal(int)

    COLUMNS = ("Действие", "Тип", "Запись", "Сумма", "Срок / дата", "Что изменилось", "Кто", "Когда")
    TITLE_COLUMN, AMOUNT_COLUMN, DATE_COLUMN, CHANGES_COLUMN, AUTHOR_COLUMN, TIME_COLUMN = 2, 3, 4, 5, 6, 7
    CHANGES_WIDTH = 260
    ROW_HEIGHT = 26
    MIN_ENTRIES_FOR_FILTERS = 10

    def __init__(self, diff: DbDiff, openable: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.entries: list[DiffEntry] = build_entries(diff)
        self.openable: bool = openable
        self.action_boxes: dict[str, QCheckBox] = {}
        self.cmb_table: QComboBox | None = None
        self.edt_search: QLineEdit | None = None
        self.lbl_status: QLabel | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        if self.entries:
            self.proxy = DiffFilterProxy(self)
            self.proxy.setSourceModel(self.create_model())
            layout.addWidget(self.create_summary())
            if len(self.entries) >= self.MIN_ENTRIES_FOR_FILTERS:
                layout.addWidget(self.create_filters())
            self.table = self.create_table()
            layout.addWidget(self.table, 1)
            self.lbl_status = QLabel(self)
            self.lbl_status.setStyleSheet("color: #555;")
            layout.addWidget(self.lbl_status)
            self.update_status()
        if diff.other_tables:
            lines = [f"•  {describe_other_table(table, counts)}" for table, counts in diff.other_tables.items()]
            lbl_other = QLabel("Также изменились данные, которые здесь не раскрываются:\n" + "\n".join(lines), self)
            lbl_other.setWordWrap(True)
            lbl_other.setStyleSheet("color: #555;")
            layout.addWidget(lbl_other)
        if not self.entries:
            layout.addStretch()

    def create_summary(self) -> QLabel:
        label = QLabel("\n".join(summary_lines(self.entries)), self)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def create_filters(self) -> QWidget:
        bar = QWidget(self)
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        for action in ACTIONS:
            count = sum(1 for entry in self.entries if entry.action == action)
            if not count:
                continue
            box = QCheckBox(f"{ACTION_TITLES[action]} ({count})", bar)
            box.setChecked(True)
            box.setStyleSheet(f"QCheckBox {{ color: {ACTION_COLORS[action]}; font-weight: bold; }}")
            box.toggled.connect(self.apply_filters)
            row.addWidget(box)
            self.action_boxes[action] = box
        tables = [(table, sum(1 for entry in self.entries if table in entry.tables)) for table in DETAILED_TABLES]
        tables = [(table, count) for table, count in tables if count]
        if len(tables) > 1:
            self.cmb_table = QComboBox(bar)
            self.cmb_table.addItem("Все разделы", "")
            for table, count in tables:
                self.cmb_table.addItem(f"{SECTION_TITLES[table]} ({count})", table)
            self.cmb_table.currentIndexChanged.connect(self.apply_filters)
            row.addWidget(self.cmb_table)
        self.edt_search = QLineEdit(bar)
        self.edt_search.setPlaceholderText("Поиск по записи")
        self.edt_search.setClearButtonEnabled(True)
        self.edt_search.textChanged.connect(self.apply_filters)
        row.addWidget(self.edt_search, 1)
        return bar

    def apply_filters(self) -> None:
        actions = {action for action, box in self.action_boxes.items() if box.isChecked()}
        table = "" if self.cmb_table is None else self.cmb_table.currentData()
        text = "" if self.edt_search is None else self.edt_search.text().strip().casefold()
        self.proxy.set_filters(actions, table, text)
        self.update_status()

    def update_status(self) -> None:
        text = f"Показано {self.proxy.rowCount()} из {len(self.entries)}."
        if self.openable:
            text += " Двойной щелчок по платежу или оплате — показать платеж в календаре."
        self.lbl_status.setText(text)

    def create_model(self) -> QStandardItemModel:
        model = QStandardItemModel(0, len(self.COLUMNS), self)
        model.setHorizontalHeaderLabels(list(self.COLUMNS))
        for entry in self.entries:
            model.appendRow(self.create_row(entry))
        return model

    def create_row(self, entry: DiffEntry) -> list[QStandardItem]:
        table_order = DETAILED_TABLES.index(entry.table)
        title_key = f"{entry.title.casefold()}\0{table_order}\0{ACTIONS.index(entry.action)}"
        action_item = self.make_item(ACTION_TITLES[entry.action], f"{ACTIONS.index(entry.action)}\0{title_key}", entry,
                                     color=ACTION_COLORS[entry.action], bold=True)
        removed = entry.action == REMOVED
        moment = "" if entry.changed_at is None else entry.changed_at.isoformat()
        return [
            action_item,
            self.make_item(entry.kind, f"{table_order}\0{title_key}", entry),
            self.make_item(entry.title, title_key, entry, tooltip=entry.title, strike=removed),
            self.make_item(entry.amount_text, float(entry.amount or 0), entry, right=True, strike=removed,
                           color=COLOR_WARNING if entry.amount_changed else None, bold=entry.amount_changed),
            self.make_item(entry.date_text, entry.date_sort, entry, right=True, strike=removed,
                           color=COLOR_WARNING if entry.date_changed else None, bold=entry.date_changed),
            self.make_item(entry.details, entry.details.casefold(), entry, tooltip=entry.details_tooltip),
            self.make_item(entry.author, entry.author.casefold(), entry),
            self.make_item(format_time(entry.changed_at), moment, entry),
        ]

    @staticmethod
    def make_item(text: str, sort_value: str | float, entry: DiffEntry, tooltip: str = "", color: str | None = None, bold: bool = False,
                  strike: bool = False, right: bool = False) -> QStandardItem:
        item = QStandardItem(text)
        item.setEditable(False)
        item.setData(entry, ENTRY_ROLE)
        item.setData(sort_value, SORT_ROLE)
        if tooltip:
            item.setToolTip(tooltip)
        if color is not None:
            item.setForeground(QBrush(QColor(color)))
        if bold or strike:
            font = QFont()
            font.setBold(bold)
            font.setStrikeOut(strike)
            item.setFont(font)
        if right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def create_table(self) -> QTableView:
        table = QTableView(self)
        table.setModel(self.proxy)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)
        table.setSortingEnabled(True)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSortIndicatorShown(True)
        for column in range(len(self.COLUMNS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.TITLE_COLUMN, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.CHANGES_COLUMN, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(self.CHANGES_COLUMN, self.CHANGES_WIDTH)
        table.setColumnHidden(self.CHANGES_COLUMN, not any(entry.details for entry in self.entries))
        has_origins = any(entry.author or entry.changed_at for entry in self.entries)
        table.setColumnHidden(self.AUTHOR_COLUMN, not has_origins)
        table.setColumnHidden(self.TIME_COLUMN, not has_origins)
        table.sortByColumn(self.TITLE_COLUMN, Qt.SortOrder.AscendingOrder)
        if self.openable:
            table.doubleClicked.connect(self.activate_index)
            table.activated.connect(self.activate_index)
        return table

    def activate_index(self, index: QModelIndex) -> None:
        entry: DiffEntry = index.siblingAtColumn(0).data(ENTRY_ROLE)
        if self.openable and entry.event_id is not None:
            self.eventActivated.emit(int(entry.event_id))


class ConflictTableWidget(QTableWidget):
    MAX_VISIBLE_ROWS = 6

    def __init__(self, conflicts: list[Conflict], parent: QWidget | None = None):
        super().__init__(len(conflicts), 4, parent)
        self.setHorizontalHeaderLabels(["Запись", "Что", "У вас", "В общей базе"])
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setWordWrap(False)
        self.verticalHeader().hide()
        for row, conflict in enumerate(conflicts):
            for column, text in enumerate((conflict.title, conflict.topic, conflict.mine, conflict.theirs)):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.setItem(row, column, item)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for column in (2, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(column, 170)
        visible_rows = min(len(conflicts), self.MAX_VISIBLE_ROWS)
        self.setFixedHeight(header.height() + visible_rows * self.verticalHeader().defaultSectionSize() + 2 * self.frameWidth() + 2)


class WarningListWidget(QListWidget):
    MAX_VISIBLE_ROWS = 4

    def __init__(self, warnings: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        for warning in warnings:
            item = QListWidgetItem(warning)
            item.setToolTip(warning)
            self.addItem(item)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setStyleSheet(f"QListWidget {{ background: {COLOR_WARNING_BG}; color: {COLOR_WARNING}; }}")
        visible_rows = min(len(warnings), self.MAX_VISIBLE_ROWS)
        self.setFixedHeight(self.sizeHintForRow(0) * visible_rows + 2 * self.frameWidth() + 2)


class SyncChangesDialog(QDialog):
    GEOMETRY_KEY = "SyncChanges/geometry"

    def __init__(self, message: str, tabs: list[tuple[str, DbDiff | None]], parent: QWidget | None = None, info: str = "",
                 conflicts: list[Conflict] | None = None, warnings: list[str] | None = None, settings: QSettings | None = None,
                 openable_tabs: tuple[str, ...] = ()):
        super().__init__(parent)
        add_help_shortcut(self, "15-sync.html")
        self.setWindowTitle("Синхронизация")
        self.settings: QSettings | None = settings
        self.event_to_show: int | None = None

        layout = QVBoxLayout(self)
        lbl_message = QLabel(message, self)
        lbl_message.setWordWrap(True)
        font = lbl_message.font()
        font.setBold(True)
        lbl_message.setFont(font)
        layout.addWidget(lbl_message)
        if info:
            lbl_info = QLabel(info, self)
            lbl_info.setWordWrap(True)
            layout.addWidget(lbl_info)
        if conflicts:
            layout.addWidget(self.section_label(f"Автоматически объединить не удалось ({len(conflicts)}):", COLOR_STATEMENT))
            layout.addWidget(ConflictTableWidget(conflicts, self))
        if warnings:
            layout.addWidget(self.section_label(f"Проверьте после объединения ({len(warnings)}):", COLOR_WARNING))
            layout.addWidget(WarningListWidget(warnings, self))

        shown_tabs = [(title, diff) for title, diff in tabs if diff is not None and not diff.is_empty]
        if shown_tabs:
            tab_widget = QTabWidget(self)
            for title, diff in shown_tabs:
                view = DiffView(diff, title in openable_tabs, tab_widget)
                view.eventActivated.connect(self.request_event)
                tab_widget.addTab(view, title)
            layout.addWidget(tab_widget, 1)
        else:
            layout.addStretch()

        self.button_box = QDialogButtonBox(self)
        self.create_buttons()
        layout.addWidget(self.button_box)

        geometry = None if settings is None else settings.value(self.GEOMETRY_KEY)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1100, 640)

    def request_event(self, event_id: int) -> None:
        self.event_to_show = event_id
        self.accept()

    def done(self, result: int) -> None:
        if self.settings is not None:
            self.settings.setValue(self.GEOMETRY_KEY, self.saveGeometry())
        super().done(result)

    def section_label(self, text: str, color: str = COLOR_CALENDAR) -> QLabel:
        label = QLabel(text, self)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        return label

    def create_buttons(self) -> None:
        self.button_box.addButton("ОК", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.accepted.connect(self.accept)
