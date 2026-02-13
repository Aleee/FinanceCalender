from dataclasses import fields
from typing import Any, get_type_hints

import lovely_logger as log
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate

from base.formatting import dec_strcommaspace
from base.payment import Payment, PaymentField


class PaymentHistoryTableModel(QAbstractTableModel):

    HEADERS = {
        PaymentField.ID: "",
        PaymentField.EVENT: "",
        PaymentField.PAYMENT_DATE: " Дата",
        PaymentField.SUM: " Сумма",
        PaymentField.CREATE_DATE: "",
    }

    internalValueRole: int = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super(PaymentHistoryTableModel, self).__init__(parent)

        self.payment_list: list = []
        self.paymemts_loaded: bool = False

        self.column_count: int = len(fields(Payment))
        self.type_hints: list = list(get_type_hints(Payment).values())
        self.last_id: int | None = None

    def load_payments(self, payments: list[Payment]) -> bool:
        if not self.paymemts_loaded:
            if not payments:
                self.last_id = 0
            else:
                self.payment_list.extend(payments)
                self.last_id = self.get_last_id()
            self.paymemts_loaded = True
            return True
        else:
            return False

    def get_last_id(self) -> int:
        return max(self.payment_list, key=lambda payment: payment.payment_id).payment_id

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.payment_list)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.column_count

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        try:
            entry: Payment = self.payment_list[index.row()]
        except IndexError:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == PaymentField.SUM:
                return dec_strcommaspace(entry.payment_sum)
            else:
                return index.data(self.internalValueRole)
        elif role == self.internalValueRole:
            return list(vars(entry).values())[index.column()]

    def setData(self, index, value, /, role=...):
        if not index.isValid():
            return False
        try:
            entry: Payment = self.payment_list[index.row()]
        except IndexError:
            return False
        if role == self.internalValueRole:
            if not isinstance(value, self.type_hints[index.column()]):
                return False
            attr_name: str = fields(entry)[index.column()].name
            setattr(entry, attr_name, value)
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.HEADERS[section]
            elif role == Qt.ItemDataRole.ToolTipRole:
                return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignLeft
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def insertRows(self, row, count, /, parent=...) -> bool:
        if self.last_id is None:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            default_row: Payment = Payment(self.last_id + 1, 0, QDate(), 0, QDate())
            self.payment_list.append(default_row)
        self.endInsertRows()
        self.last_id += 1
        return True

    def removeRows(self, row, count, /, parent=...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            self.payment_list.pop(row + i)
        self.endRemoveRows()
        return True

    def append_row(self, data: list) -> bool:
        if len(data) != len(fields(Payment)) - 1:
            log.x("Набор передаваемых в append_row данных должен охватывать все атрибуты класса-хранителя за исключением id")
            raise IndexError
        position: int = self.rowCount(QModelIndex())
        if self.insertRows(position, 1, QModelIndex()):
            for column, value in enumerate(data):
                index: QModelIndex = self.index(position, column + 1, QModelIndex())
                if not self.setData(index, value, self.internalValueRole):
                    self.removeRows(self.rowCount(), 1)
                    log.c(f"Не удалось записать данные {value} в столбец {column + 1}")
            return True
        return False

    def delete_rows_byeventid(self, eventid: int) -> None:
        for row in range(self.rowCount()):
            if self.index(row, PaymentField.EVENT).data(self.internalValueRole) == eventid:
                self.removeRow(row)
