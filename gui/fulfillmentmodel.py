from PySide6 import QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, QModelIndex


class TreeItem:
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0


class FulfillmentModel(QtCore.QAbstractItemModel):

    FULFILLMENT_STRUCTURE = {
        # 0: список подкатегорий, 1: вертикальный хедер, 2: жирный, 3: считается ли исполнение
        10000: ([], "1. Остаток средств на начало периода", True, False),
        20000: ([21000, 22000, 23000], "2. Поступление денежных средств", True, True),
        21000: ([], "2.1. выручка от реализации услуг", False, True),
        22000: ([], "2.2. прочие доходы", False, True),
        23000: ([23100, 23200], "2.3. кредиты и займы", False, True),
        23100: ([], "2.3.1. овердрафт", False, True),
        23200: ([], "2.3.2. кредит", False, True),
        30000: ([31000, 32000], "3. Расходование денежных средств", True, True),
        31000: ([31100, 31200], "3.1. текущая деятельность", True, True),
        31100: ([31101, 31102, 31103], "3.1.1. переменные затраты", True, True),
        31101: ([], "3.1.1.1. заработная плата с налогами", False, True),
        31102: ([], "3.1.1.2. материалы", False, True),
        31103: ([], "3.1.1.3. услуги сторонних организаций", False, True),
        31200: ([31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213], "3.1.2. постоянные затраты", True, True),
        31201: ([], "3.1.2.1. налоги", False, True),
        31202: ([], "3.1.2.2. энергоносители", False, True),
        31203: ([], "3.1.2.3. маркетинг", False, True),
        31204: ([], "3.1.2.4. аренда офиса", False, True),
        31205: ([], "3.1.2.5. аренда помещений", False, True),
        31206: ([], "3.1.2.6. IT обслуживание", False, True),
        31207: ([], "3.1.2.7. обеспечение текущей деятельности", False, True),
        31208: ([], "3.1.2.8. обслуживание здания", False, True),
        31209: ([], "3.1.2.9. банковские расходы", False, True),
        31210: ([], "3.1.2.10. услуги связи", False, True),
        31211: ([], "3.1.2.11. комиссионное вознаграждение", False, True),
        31212: ([], "3.1.2.12. обучение персонала", False, True),
        31213: ([], "3.1.2.13. техническое обслуживание и страхование оборудования", False, True),
        32000: ([32100, 32200, 32300], "3.2. финансовая деятельность", True, True),
        32100: ([32101, 32102], "3.2.1. погашение кредитных обязательств", False, True),
        32101: ([], "3.2.1.1. погашение кредитов", False, True),
        32102: ([], "3.2.1.2. погашение лизинга", False, True),
        32200: ([], "3.2.2. погашение процентов по кредитам, займам", False, True),
        32300: ([], "3.2.3. погашение займов учредителям", False, True),
        33000: ([], "3.3. инвестиционная деятельность", True, True),
        40000: ([], "4. Остаток средств на конец периода", True, False),
    }

    spanRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, data, parent=None):
        super(FulfillmentModel, self).__init__(parent)

        self.rootItem = TreeItem(("Виды поступлений и расходов", "План", "Факт", "Отклонение", "Исполнение"))

    def setup_model(self):
        for data in self.FULFILLMENT_STRUCTURE.values():
            self.rootItem.appendChild(TreeItem((data[1], ""), self.rootItem))
        for values in (("Пример 1 --------------------", 346436), ("Пример 2 --------------------------------", 5646)):
            self.rootItem.child(8).appendChild(TreeItem(values, self.rootItem.child(8)))

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())
        elif role == self.spanRole:
            return not index.parent() == QModelIndex()
        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

