from typing import Any

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QFont, QColor


class FinPlanTableModel(QAbstractTableModel):

    FINPLAN_STRUCTURE = {
        # 0: список подкатегорий, 1: вертикальный хедер, 2: название, 3: жирный, 4: считается ли исполнение
        10000: ([], "1.", "Остаток средств на начало периода", True, False),
        20000: ([21000, 22000, 23000], "2.", "Поступление денежных средств", True, True),
        21000: ([], "2.1.", "выручка от реализации услуг", False, True),
        22000: ([], "2.2.", "прочие доходы", False, True),
        23000: ([23100, 23200], "2.3.", "кредиты и займы", False, True),
        23100: ([], "2.3.1.", "овердрафт", False, True),
        23200: ([], "2.3.2.", "кредит", False, True),
        30000: ([31000, 32000], "3.", "Расходование денежных средств", True, True),
        31000: ([31100, 31200], "3.1.", "текущая деятельность", True, True),
        31100: ([31101, 31102, 31103], "3.1.1.", "переменные затраты", True, True),
        31101: ([], "3.1.1.1.", "заработная плата с налогами", False, True),
        31102: ([], "3.1.1.2.", "материалы", False, True),
        31103: ([], "3.1.1.3.", "услуги сторонних организаций", False, True),
        31200: ([31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213], "3.1.2.", "постоянные затраты", True, True),
        31201: ([], "3.1.2.1", "налоги", False, True),
        31202: ([], "3.1.2.2", "энергоносители", False, True),
        31203: ([], "3.1.2.3", "маркетинг", False, True),
        31204: ([], "3.1.2.4", "аренда офиса", False, True),
        31205: ([], "3.1.2.5", "аренда помещений", False, True),
        31206: ([], "3.1.2.6", "IT обслуживание", False, True),
        31207: ([], "3.1.2.7", "обеспечение текущей деятельности", False, True),
        31208: ([], "3.1.2.8", "обслуживание здания", False, True),
        31209: ([], "3.1.2.9", "банковские расходы", False, True),
        31210: ([], "3.1.2.10", "услуги связи", False, True),
        31211: ([], "3.1.2.11", "комиссионное вознаграждение", False, True),
        31212: ([], "3.1.2.12", "обучение персонала", False, True),
        31213: ([], "3.1.2.13", "техническое обслуживание и страхование оборудования", False, True),
        32000: ([32100, 32200, 32300], "3.2.", "финансовая деятельность", True, True),
        32100: ([32101, 32102], "3.2.1.", "погашение кредитных обязательств", False, True),
        32101: ([], "3.2.1.1", "погашение кредитов", False, True),
        32102: ([], "3.2.1.2", "погашение лизинга", False, True),
        32200: ([], "3.2.2", "погашение процентов по кредитам, займам", False, True),
        32300: ([], "3.2.3", "погашение займов учредителям", False, True),
        33000: ([], "3.3.", "инвестиционная деятельность", True, True),
        40000: ([], "4.", "Остаток средств на конец периода", True, False),
    }

    HORIZONTAL_HEADER_LABELS = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    EditableRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super(FinPlanTableModel, self).__init__(parent)

        self.categories = list(self.FINPLAN_STRUCTURE.keys())
        self.values: dict = {}

    def calculate_add_totals(self):
        for skey, svalue in reversed(list(self.FINPLAN_STRUCTURE.items())):
            if svalue[0]:
                running_totals = [0] * 12
                for key, value in self.values.items():
                    if key in svalue[0]:
                        for month in range(len(value)):
                            running_totals[month] += value[month]
                self.values[skey] = running_totals

    def rowCount(self, /, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.values)

    def columnCount(self, /, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return 13

    def data(self, index, /, role=...) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return self.FINPLAN_STRUCTURE[self.categories[index.row()]][2]
            else:
                value = self.values[self.categories[index.row()]][index.column() - 1]
                return value if value else ""
        elif role == Qt.ItemDataRole.FontRole:
            font: QFont = QFont()
            font.setBold(self.FINPLAN_STRUCTURE[self.categories[index.row()]][3])
            return font
        elif role == self.EditableRole:
            return not bool(self.FINPLAN_STRUCTURE[self.categories[index.row()]][0])
        elif role == Qt.ItemDataRole.BackgroundRole:
            if self.categories[index.row()] in (10000, 40000):
                return QColor("#E2D5B8")
            elif self.categories[index.row()] % 10000 == 0:
                return QColor("#9EC1A3")
            elif self.FINPLAN_STRUCTURE[self.categories[index.row()]][0]:
                if self.categories[index.row()] % 1000 == 0:
                    return QColor("#EAF1E4")
                else:
                    return QColor("#F5F8F2")

    def headerData(self, section, orientation, /, role=...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.HORIZONTAL_HEADER_LABELS[section]
            if orientation == Qt.Orientation.Vertical:
                return self.FINPLAN_STRUCTURE[self.categories[section]][1]

    def setData(self, index, value, /, role=...):
        if role == Qt.ItemDataRole.EditRole:
            try:
                int_value: int = int(value)
                self.values[self.categories[index.row()]][index.column() - 1] = int_value
                self.calculate_add_totals()
                self.dataChanged.emit(index, index)
                return True
            except ValueError:
                return False
        return False

    def flags(self, index):
        if index.data(self.EditableRole):
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        else:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
