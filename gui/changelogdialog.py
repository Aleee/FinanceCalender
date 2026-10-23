from html import escape

from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from base.changelog import DELETE, EVENT_TABLE, INSERT, PAYMENT_TABLE, ChangeOperation
from base.formatting import COLOR_OK, COLOR_STATEMENT, COLOR_WARNING
from gui.manualdialog import add_help_shortcut

ACTION_COLORS = {INSERT: COLOR_OK, DELETE: COLOR_STATEMENT}
TIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class ChangeLogTree(QTreeWidget):
    EXPAND_ALL_LIMIT = 200

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setHeaderLabels(["Когда", "Кто", "Что изменено", "Было", "Стало"])
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformRowHeights(True)
        header = self.header()
        header.setStretchLastSection(False)
        for column, width in enumerate((150, 130, 300, 200, 200)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(column, width)

    def fill(self, operations: list[ChangeOperation]) -> None:
        self.clear()
        for operation in operations:
            item = QTreeWidgetItem(self, [operation.time.strftime(TIME_FORMAT), operation.author or "—", operation.title])
            item.setToolTip(1, f"Компьютер: {operation.machine}" if operation.machine else "Компьютер не указан")
            item.setForeground(2, QBrush(QColor(ACTION_COLORS.get(operation.action, COLOR_WARNING))))
            for column in (0, 1, 2):
                font = item.font(column)
                font.setBold(True)
                item.setFont(column, font)
            for title, old_value, new_value in operation.fields:
                field_item = QTreeWidgetItem(item, ["", "", title, old_value, new_value])
                field_item.setForeground(3, QBrush(QColor(COLOR_STATEMENT)))
                field_item.setForeground(4, QBrush(QColor(COLOR_OK)))
                for column, text in ((2, title), (3, old_value), (4, new_value)):
                    field_item.setToolTip(column, text)
        if len(operations) + sum(len(operation.fields) for operation in operations) <= self.EXPAND_ALL_LIMIT:
            self.expandAll()


class ChangeLogDialog(QDialog):
    SCOPES = (("Платеж и оплаты", None), ("Только платеж", EVENT_TABLE), ("Только оплаты", PAYMENT_TABLE))

    def __init__(self, operations: list[ChangeOperation], title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"История изменений: {title}")
        self.resize(1000, 520)
        add_help_shortcut(self, "04-payment.html")
        self.operations = operations

        self.cmb_scope = QComboBox(self)
        for text, table in self.SCOPES:
            self.cmb_scope.addItem(text, table)
        self.tree = ChangeLogTree(self)
        self.la_empty = QLabel("Записей нет", self)
        self.la_empty.setStyleSheet("color: gray;")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)

        head_layout = QHBoxLayout()
        head_layout.addWidget(QLabel(f"<b>{escape(title)}</b>", self), 1)
        head_layout.addWidget(self.cmb_scope)
        layout = QVBoxLayout(self)
        layout.addLayout(head_layout)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.la_empty)
        layout.addWidget(buttons)

        self.cmb_scope.currentIndexChanged.connect(self.show_operations)
        self.show_operations()

    def show_operations(self) -> None:
        table = self.cmb_scope.currentData()
        shown = [operation for operation in self.operations if table is None or operation.table == table]
        self.tree.fill(shown)
        self.la_empty.setVisible(not shown)
        self.tree.setVisible(bool(shown))
