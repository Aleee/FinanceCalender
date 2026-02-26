from dataclasses import dataclass, field
from decimal import Decimal

from PySide6 import QtCore
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QFont, QColor

from base.date import str_date, date_displstr
from base.event import EventCategory, EventFinanceSubcategory
from base.formatting import dec_strcommaspace, int_strspace, float_strpercentage


@dataclass
class Palette:
    base: QColor = field(default_factory=lambda: QColor("white"))
    base1: QColor = field(default_factory=lambda: QColor("#ffdfdf"))
    base2: QColor = field(default_factory=lambda: QColor("#ffd5d5"))
    base3: QColor = field(default_factory=lambda: QColor("#ffbfbf"))
    mid: QColor = field(default_factory=lambda: QColor("#E9ECEF"))
    mid1: QColor = field(default_factory=lambda: QColor("#ebd2d4"))
    mid2: QColor = field(default_factory=lambda: QColor("#eccacd"))
    mid3: QColor = field(default_factory=lambda: QColor("#edbdbf"))
    high: QColor = field(default_factory=lambda: QColor("#CED4DA"))
    high1: QColor = field(default_factory=lambda: QColor("#d4babf"))
    high2: QColor = field(default_factory=lambda: QColor("#d6b1b6"))
    high3: QColor = field(default_factory=lambda: QColor("#da9fa4"))


class TreeItem:
    def __init__(self, data, parent=None, categorie: int = 0):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.categorie: int = categorie

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

    CATEGORY_MAP = {
        EventCategory.SALARIES: 31101,
        EventCategory.TAXES: 31201,
        EventCategory.CONSUMABLES: 31102,
        EventCategory.ENERGY: 31202,
        EventCategory.MARKETING: 31203,
        EventCategory.OFFICERENT: 31204,
        EventCategory.ROOMRENT: 31205,
        EventCategory.EQUIPMENT: 31206,
        EventCategory.CURRENT: 31207,
        EventCategory.BUILDINGMAINT: 31208,
        EventCategory.BANKING: 31209,
        EventCategory.TELECOM: 31210,
        EventCategory.TRAINING: 31212,
        EventCategory.THIRDPARTYSERVICES: 31103,
        EventCategory.COMMISSION: 31211,
        EventCategory.MEDEQREPAIR: 31213,
        EventCategory.TOP_FINANCES * 10 + EventFinanceSubcategory.LOAN: 32101,
        EventCategory.TOP_FINANCES * 10 + EventFinanceSubcategory.LEASING: 32102,
        EventCategory.TOP_FINANCES * 10 + EventFinanceSubcategory.INTEREST: 32200,
        EventCategory.TOP_FINANCES * 10 + EventFinanceSubcategory.FOUNDERLOAN: 32300,
        EventCategory.TOP_INVESTMENT: 33000,
    }

    FULFILLMENT_STRUCTURE = {
        # 0: список подкатегорий, 1: вертикальный хедер, 2: жирный, 3: считается ли исполнение
        10000: ([], "1.", "Остаток средств на начало периода", True, False),
        20000: ([21000, 22000, 23000], "2.", "Поступление денежных средств", True, True),
        21000: ([], "2.1.", "выручка от реализации услуг", False, True),
        22000: ([], "2.2.", "прочие доходы", False, True),
        23000: ([23100, 23200], "2.3.", "кредиты и займы", False, True),
        23100: ([], "2.3.1.", "овердрафт", False, True),
        23200: ([], "2.3.2.", "кредит", False, True),
        30000: ([31000, 32000, 33000], "3.", "Расходование денежных средств", True, True),
        31000: ([31100, 31200], "3.1.", "текущая деятельность", True, True),
        31100: ([31101, 31102, 31103], "3.1.1.", "переменные затраты", True, True),
        31101: ([], "3.1.1.1.", "заработная плата с налогами", False, True),
        31102: ([], "3.1.1.2.", "материалы", False, True),
        31103: ([], "3.1.1.3.",  "услуги сторонних организаций", False, True),
        31200: ([31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213], "3.1.2.", "постоянные затраты", True, True),
        31201: ([], "3.1.2.1.", "налоги", False, True),
        31202: ([], "3.1.2.2.", "энергоносители", False, True),
        31203: ([], "3.1.2.3.", "маркетинг", False, True),
        31204: ([], "3.1.2.4.", "аренда офиса", False, True),
        31205: ([], "3.1.2.5.", "аренда помещений", False, True),
        31206: ([], "3.1.2.6.", "IT обслуживание", False, True),
        31207: ([], "3.1.2.7.", "обеспечение текущей деятельности", False, True),
        31208: ([], "3.1.2.8.", "обслуживание здания", False, True),
        31209: ([], "3.1.2.9.", "банковские расходы", False, True),
        31210: ([], "3.1.2.10.", "услуги связи", False, True),
        31211: ([], "3.1.2.11.", "комиссионное вознаграждение", False, True),
        31212: ([], "3.1.2.12.", "обучение персонала", False, True),
        31213: ([], "3.1.2.13.", "техническое обслуживание и страхование оборудования", False, True),
        32000: ([32100, 32200, 32300], "3.2.", "финансовая деятельность", True, True),
        32100: ([32101, 32102], "3.2.1.", "погашение кредитных обязательств", False, True),
        32101: ([], "3.2.1.1.", "погашение кредитов", False, True),
        32102: ([], "3.2.1.2.", "погашение лизинга", False, True),
        32200: ([], "3.2.2.", "погашение процентов по кредитам, займам", False, True),
        32300: ([], "3.2.3.", "погашение займов учредителям", False, True),
        33000: ([], "3.3.", "инвестиционная деятельность", True, True),
        40000: ([], "4.", "Остаток средств на конец периода", True, False),
    }

    spanRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super(FulfillmentModel, self).__init__(parent)
        self.rootItem = TreeItem(("#", "Виды поступлений и расходов", "План", "Факт", "Отклонение", "Исполнение"))
        self.categories = list(self.FULFILLMENT_STRUCTURE.keys())
        self.plt = Palette()

    def setup_model(self, payments: list, inflow_values: list, plan_values: dict):
        # Заполнение заголовочных строк
        factuals: dict = self.calculate_factuals(payments, inflow_values)
        for categorie, data in self.FULFILLMENT_STRUCTURE.items():
            try:
                plan_value = plan_values[categorie]
            except KeyError, AttributeError:
                plan_value = None
            if plan_value is not None:
                deviation = factuals[categorie] - plan_value
                if plan_value != 0:
                    fulfillment = factuals[categorie] / plan_value
                else:
                    fulfillment = -1
            else:
                deviation = ""
                fulfillment = ""
            self.rootItem.appendChild(TreeItem((data[1], data[2], plan_value, factuals[categorie], deviation, fulfillment), self.rootItem, categorie))
        # Заполнение платежей
        for payment in payments:
            category, amount, textamount, date, receiver, name, subcategory = (int(payment[0]), Decimal(payment[1]), dec_strcommaspace(Decimal(payment[1])),
                                                                               date_displstr(str_date(payment[2])), str(payment[3]), str(payment[4]), int(payment[5]))
            text = f"{textamount} р.\t{date}\t{receiver}  ({name})"
            mapped_category: int = self.CATEGORY_MAP[category] if category != EventCategory.TOP_FINANCES else self.CATEGORY_MAP[category*10+subcategory]
            self.rootItem.child(self.categories.index(mapped_category)).appendChild(TreeItem((text,), self.rootItem.child(self.categories.index(mapped_category))))

    def calculate_factuals(self, payments: list, inflow_values: list) -> dict:
        factuals_dict = dict.fromkeys(self.FULFILLMENT_STRUCTURE, 0)
        factuals_dict[10000], factuals_dict[21000], factuals_dict[22000], factuals_dict[23100], factuals_dict[23200] = inflow_values
        for payment in payments:
            category, subcategory, amount = int(payment[0]), int(payment[5]), round(Decimal(payment[1]))
            mapped_category: int = self.CATEGORY_MAP[category] if category != EventCategory.TOP_FINANCES else self.CATEGORY_MAP[category * 10 + subcategory]
            factuals_dict[mapped_category] += amount

        for skey, svalue in reversed(list(self.FULFILLMENT_STRUCTURE.items())):
            if svalue[0]:
                running_total = 0
                for key, value in factuals_dict.items():
                    if key in svalue[0]:
                        running_total += value
                factuals_dict[skey] = running_total

        return factuals_dict


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
            if index.column() in (2, 3, 4):
                if item.data(index.column()) is None:
                    return ""
                elif not item.data(index.column()):
                    return "0"
                else:
                    return int_strspace(item.data(index.column()))
            elif index.column() == 5:
                if not item.data(index.column()):
                    return ""
                elif item.data(index.column()) == -1:
                    return "--"
                else:
                    return float_strpercentage(item.data(index.column()))
            return item.data(index.column())
        elif role == self.spanRole:
            return not index.parent() == QModelIndex()
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (2, 3, 4):
                return Qt.AlignmentFlag.AlignRight
            elif index.column() == 5:
                return Qt.AlignmentFlag.AlignHCenter
            else:
                return Qt.AlignmentFlag.AlignLeft
        elif role == Qt.ItemDataRole.FontRole:
            if index.parent() == QModelIndex():
                font = QFont()
                categorie: int = index.internalPointer().categorie
                subcategories_present = bool(self.FULFILLMENT_STRUCTURE[categorie][0])
                font.setBold(categorie % 10000 == 0 or categorie == self.CATEGORY_MAP[EventCategory.TOP_INVESTMENT] or (categorie % 100 == 0 and subcategories_present))
                return font
            else:
                font = QFont()
                font.setPointSize(9)
                return font
        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.parent() == QModelIndex():
                categorie: int = index.internalPointer().categorie
                subcategories_present = bool(self.FULFILLMENT_STRUCTURE[categorie][0])
                if categorie % 10000 == 0:
                    if index.internalPointer().itemData[5] <= 1:
                        return self.plt.high
                    elif 1 < index.internalPointer().itemData[5] < 1.2:
                        return self.plt.high1
                    elif 1 < index.internalPointer().itemData[5] < 1.4:
                        return self.plt.high2
                    else:
                        return self.plt.high3
                elif (categorie % 100 == 0 and subcategories_present) or categorie == self.CATEGORY_MAP[EventCategory.TOP_INVESTMENT]:
                    if index.internalPointer().itemData[5] <= 1:
                        return self.plt.mid
                    elif 1 < index.internalPointer().itemData[5] < 1.2:
                        return self.plt.mid1
                    elif 1 < index.internalPointer().itemData[5] < 1.4:
                        return self.plt.mid2
                    else:
                        return self.plt.mid3
                else:
                    if index.internalPointer().itemData[5] <= 1:
                        return self.plt.base
                    elif 1 < index.internalPointer().itemData[5] < 1.2:
                        return self.plt.base1
                    elif 1 < index.internalPointer().itemData[5] < 1.4:
                        return self.plt.base2
                    else:
                        return self.plt.base3


        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.rootItem.data(section)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
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

