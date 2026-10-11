from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QLabel, QListWidget,
                               QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from base.formatting import COLOR_CALENDAR, COLOR_OK, COLOR_STATEMENT, COLOR_WARNING, COLOR_WARNING_BG
from base.syncdiff import Conflict, DbDiff, TableDiff, describe_other_table, describe_row, field_changes


class DiffTreeWidget(QTreeWidget):
    TABLE_TITLES = (("event", "Платежи"), ("payment", "Оплаты"))
    EXPAND_ALL_LIMIT = 100

    def __init__(self, diff: DbDiff, parent: QWidget | None = None):
        super().__init__(parent)
        self.setHeaderLabels(["Запись", "Было", "Стало"])
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformRowHeights(True)
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(column, 180)

        for table, title in self.TABLE_TITLES:
            table_diff: TableDiff | None = diff.tables.get(table)
            if table_diff is not None and not table_diff.is_empty:
                self.add_table(table, title, table_diff)
        for table, counts in diff.other_tables.items():
            self.make_bold(QTreeWidgetItem(self, [describe_other_table(table, counts)]))

        if len(self.findItems("*", Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive)) <= self.EXPAND_ALL_LIMIT:
            self.expandAll()
        else:
            self.expandToDepth(1)

    @staticmethod
    def make_bold(item: QTreeWidgetItem) -> None:
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

    def add_table(self, table: str, title: str, table_diff: TableDiff) -> None:
        table_item = QTreeWidgetItem(self, [title])
        self.make_bold(table_item)
        self.add_group(table_item, "Добавлено", COLOR_OK, [describe_row(table, row) for row in table_diff.added])
        changed_items = self.add_group(table_item, "Изменено", COLOR_WARNING,
                                       [describe_row(table, new_row) for _, new_row in table_diff.changed])
        for item, (old_row, new_row) in zip(changed_items, table_diff.changed):
            for field_title, old_value, new_value in field_changes(old_row, new_row):
                change_item = QTreeWidgetItem(item, [field_title, old_value, new_value])
                change_item.setForeground(1, QBrush(QColor(COLOR_STATEMENT)))
                change_item.setForeground(2, QBrush(QColor(COLOR_OK)))
        self.add_group(table_item, "Удалено", COLOR_STATEMENT, [describe_row(table, row) for row in table_diff.removed])

    def add_group(self, parent: QTreeWidgetItem, title: str, color: str, texts: list[str]) -> list[QTreeWidgetItem]:
        if not texts:
            return []
        group_item = QTreeWidgetItem(parent, [f"{title} ({len(texts)})"])
        group_item.setForeground(0, QBrush(QColor(color)))
        self.make_bold(group_item)
        return [QTreeWidgetItem(group_item, [text]) for text in texts]


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
    def __init__(self, message: str, tabs: list[tuple[str, DbDiff | None]], parent: QWidget | None = None, info: str = "",
                 conflicts: list[Conflict] | None = None, warnings: list[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация")
        self.resize(820, 560)

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
                tab_widget.addTab(DiffTreeWidget(diff, tab_widget), title)
            layout.addWidget(tab_widget, 1)
        else:
            layout.addStretch()

        self.button_box = QDialogButtonBox(self)
        self.create_buttons()
        layout.addWidget(self.button_box)

    def section_label(self, text: str, color: str = COLOR_CALENDAR) -> QLabel:
        label = QLabel(text, self)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        return label

    def create_buttons(self) -> None:
        self.button_box.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.accepted.connect(self.accept)
