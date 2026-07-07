from enum import IntEnum
from typing import Any

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel

from base.dbhandler import DBHandler


class PersonalCol(IntEnum):
    ID = 0
    NAME = 1
    DEPT = 2
    ARCHIVED = 3


class PersonalTableModel(QAbstractTableModel):

    COLUMN_COUNT: int = 4
    internalValueRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, dbh: DBHandler, parent=None):
        super().__init__(parent)
        self.dbh = dbh
        self.tdata: list = []
        self.last_id: int = 0

    def setup_model(self):
        data_from_db: tuple | None = self.dbh.load_personal_data()
        if data_from_db is None:
            return
        self.tdata = data_from_db[0]
        self.last_id = data_from_db[2]

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.tdata)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self.COLUMN_COUNT

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.tdata[index.row()][index.column()])
        elif role == self.internalValueRole:
            if index.column() == PersonalCol.NAME:
                return self.tdata[index.row()][index.column()]
            else:
                return int(self.tdata[index.row()][index.column()])
        else:
            return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole:
            self.tdata[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False


class PersonalSortFilterModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.actual_to_show: bool = True

        self.sort(1)
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, source_row, source_parent):
        archived_value: int = self.sourceModel().index(
            source_row, PersonalCol.ARCHIVED, source_parent).data(PersonalTableModel.internalValueRole)
        return archived_value != int(self.actual_to_show)

    def show_actuals(self, yes_please: bool):
        self.actual_to_show = yes_please
        self.invalidate()
