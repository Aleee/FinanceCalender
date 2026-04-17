from dataclasses import fields
from decimal import Decimal
from enum import IntEnum
from typing import Any, get_type_hints

import lovely_logger as log
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate
from PySide6.QtSql import QSqlTableModel

from base.date import str_date, date_displstr
from base.formatting import dec_strcommaspace


class PaymentCol(IntEnum):
    ID = 0
    EVENT = 1
    PAYMENT_DATE = 2
    SUM = 3
    CREATE_DATE = 4


class PaymentHistoryTableModel(QSqlTableModel):

    HEADERS = {
        PaymentCol.ID: "",
        PaymentCol.EVENT: "",
        PaymentCol.PAYMENT_DATE: " Дата",
        PaymentCol.SUM: " Сумма",
        PaymentCol.CREATE_DATE: "",
    }

    dbValueRole: int = Qt.ItemDataRole.UserRole + 1
    qtValueRole: int = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super(PaymentHistoryTableModel, self).__init__(parent)

        self.current_event_id: int = 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == PaymentCol.SUM:
                return dec_strcommaspace(index.data(self.qtValueRole))
            elif index.column() == PaymentCol.PAYMENT_DATE:
                return date_displstr(index.data(self.qtValueRole))
            else:
                return index.data(self.dbValueRole)
        elif role == self.dbValueRole:
            return super(PaymentHistoryTableModel, self).data(index)
        elif role == self.qtValueRole:
            if index.column() == PaymentCol.SUM:
                return Decimal(index.data(self.dbValueRole))
            elif index.column() == PaymentCol.PAYMENT_DATE:
                return str_date(index.data(self.dbValueRole))
            elif index.column() in (PaymentCol.EVENT, PaymentCol.ID):
                return int(index.data(self.dbValueRole))
        return super(PaymentHistoryTableModel, self).data(index, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.HEADERS[section]
            elif role == Qt.ItemDataRole.ToolTipRole:
                return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignLeft
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def update_filter(self, event_id: int | None = None):
        if event_id is not None:
            self.current_event_id = event_id
        self.setFilter(f"eventid = {self.current_event_id}")
        self.select()

    def reset_filter(self):
        self.setFilter("")

    def append_row(self, data: list) -> bool:
        if len(data) != len(PaymentCol) - 1:
            log.x("Набор передаваемых в append_row данных должен охватывать все атрибуты класса-хранителя за исключением id")
            raise IndexError

        self.reset_filter()
        position: int = self.rowCount()

        if self.insertRow(position):
            for column, value in enumerate(data):
                index: QModelIndex = self.index(position, column + 1)
                if not self.setData(index, value):
                    self.removeRows(self.rowCount(), 1)
                    log.c(f"Не удалось записать данные {value} в столбец {column + 1}")
                    self.update_filter()
                    return False
            if not self.submitAll():
                log.c(f"Не удалось записать изменения в таблицу payment: {self.lastError().text()}")
            self.update_filter()
            return True
        self.update_filter()
        return False

    def delete_rows_byeventid(self, eventid: int) -> None:
        for row in range(self.rowCount()):
            if self.index(row, PaymentCol.EVENT).data(self.qtValueRole) == eventid:
                self.removeRow(row)
