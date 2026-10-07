from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

import lovely_logger as log
from PySide6 import QtCore
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QFont, QColor

from base.date import str_date, date_displstr
from base.formatting import dec_strcommaspace, int_strspace, float_strpercentage
from base.liability import LiabilityCategory, LiabilityFinanceSubcategory


@dataclass
class TablePalette:
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

    def get_categorie(self) -> int:
        return self.categorie


class FulfilmentModel(QtCore.QAbstractItemModel):

    CATEGORY_MAP = {
        LiabilityCategory.SALARIES: 31101,
        LiabilityCategory.TAXES: 31201,
        LiabilityCategory.CONSUMABLES: 31102,
        LiabilityCategory.ENERGY: 31202,
        LiabilityCategory.MARKETING: 31203,
        LiabilityCategory.OFFICERENT: 31204,
        LiabilityCategory.ROOMRENT: 31205,
        LiabilityCategory.EQUIPMENT: 31206,
        LiabilityCategory.CURRENT: 31207,
        LiabilityCategory.BUILDINGMAINT: 31208,
        LiabilityCategory.BANKING: 31209,
        LiabilityCategory.TELECOM: 31210,
        LiabilityCategory.TRAINING: 31212,
        LiabilityCategory.THIRDPARTYSERVICES: 31103,
        LiabilityCategory.COMMISSION: 31211,
        LiabilityCategory.MEDEQREPAIR: 31213,
        LiabilityCategory.TOP_FINANCES * 10 + LiabilityFinanceSubcategory.LOAN: 32101,
        LiabilityCategory.TOP_FINANCES * 10 + LiabilityFinanceSubcategory.LEASING: 32102,
        LiabilityCategory.TOP_FINANCES * 10 + LiabilityFinanceSubcategory.INTEREST: 32200,
        LiabilityCategory.TOP_FINANCES * 10 + LiabilityFinanceSubcategory.FOUNDERLOAN: 32300,
        LiabilityCategory.TOP_INVESTMENT: 33000,
    }

    FULFILLMENT_STRUCTURE = {
        # 0: список подкатегорий, 1: вертикальный хедер, 2: название
        10000: ([], "1.", "Остаток средств на начало периода"),
        20000: ([21000, 22000, 23000], "2.", "Поступление денежных средств"),
        21000: ([], "2.1.", "выручка от реализации услуг"),
        22000: ([], "2.2.", "прочие доходы"),
        23000: ([23100, 23200], "2.3.", "кредиты и займы"),
        23100: ([], "2.3.1.", "овердрафт"),
        23200: ([], "2.3.2.", "кредит"),
        30000: ([31000, 32000, 33000], "3.", "Расходование денежных средств"),
        31000: ([31100, 31200], "3.1.", "текущая деятельность"),
        31100: ([31101, 31102, 31103], "3.1.1.", "переменные затраты"),
        31101: ([], "3.1.1.1.", "заработная плата с налогами"),
        31102: ([], "3.1.1.2.", "материалы"),
        31103: ([], "3.1.1.3.", "услуги сторонних организаций"),
        31200: ([31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213], "3.1.2.", "постоянные затраты"),
        31201: ([], "3.1.2.1.", "налоги"),
        31202: ([], "3.1.2.2.", "энергоносители"),
        31203: ([], "3.1.2.3.", "маркетинг"),
        31204: ([], "3.1.2.4.", "аренда офиса"),
        31205: ([], "3.1.2.5.", "аренда помещений"),
        31206: ([], "3.1.2.6.", "IT обслуживание"),
        31207: ([], "3.1.2.7.", "обеспечение текущей деятельности"),
        31208: ([], "3.1.2.8.", "обслуживание здания"),
        31209: ([], "3.1.2.9.", "банковские расходы"),
        31210: ([], "3.1.2.10.", "услуги связи"),
        31211: ([], "3.1.2.11.", "комиссионное вознаграждение"),
        31212: ([], "3.1.2.12.", "обучение персонала"),
        31213: ([], "3.1.2.13.", "техническое обслуживание и страхование оборудования"),
        32000: ([32100, 32200, 32300], "3.2.", "финансовая деятельность"),
        32100: ([32101, 32102], "3.2.1.", "погашение кредитных обязательств"),
        32101: ([], "3.2.1.1.", "погашение кредитов"),
        32102: ([], "3.2.1.2.", "погашение лизинга"),
        32200: ([], "3.2.2.", "погашение процентов по кредитам, займам"),
        32300: ([], "3.2.3.", "погашение займов учредителям"),
        33000: ([], "3.3.", "инвестиционная деятельность"),
        40000: ([], "4.", "Остаток средств на конец периода"),
    }

    spanRole = Qt.ItemDataRole.UserRole + 1
    internalValueRole = Qt.ItemDataRole.UserRole + 2

    NORMAL_CUTPOINT: float = 1.1
    HIGH_CUTPOINT: float = 1.3
    VERYHIGH_CUTPOINT: float = 1.5

    def __init__(self, parent=None):
        super(FulfilmentModel, self).__init__(parent)
        self.rootItem = None
        self.fulfillment_mode: bool = True
        self.categories = list(self.FULFILLMENT_STRUCTURE.keys())
        self.payments_categories = list(key for key in self.FULFILLMENT_STRUCTURE.keys() if key // 10000 == 3)
        self.plt = TablePalette()

    def setup_model(self, is_fulfillment: bool, payments: list, inflow_values: list, plan_values: dict):
        if is_fulfillment:
            self.rootItem = TreeItem(("#", "Виды поступлений и расходов", "План", "Факт", "Отклонение", "Исполнение"))
        else:
            self.rootItem = TreeItem(("#", "Виды поступлений и расходов", "Сумма", "Сумма без НДС"))
        self.fulfillment_mode = is_fulfillment
        if is_fulfillment:
            # Заполнение заголовочных строк
            factuals: dict = self.calculate_factuals(payments, inflow_values)
            for categorie, data in self.FULFILLMENT_STRUCTURE.items():
                try:
                    plan_value = plan_values[categorie]
                except KeyError:
                    plan_value = None
                if plan_value is not None:
                    deviation = factuals[categorie] - plan_value
                    if plan_value != 0:
                        fulfillment = factuals[categorie] / plan_value
                    else:
                        fulfillment = -1
                else:
                    deviation = None
                    fulfillment = None
                self.rootItem.appendChild(TreeItem((data[1], data[2], plan_value, factuals[categorie], deviation, fulfillment), self.rootItem, categorie))
            # Заполнение платежей
            for payment in payments:
                category, amount, textamount, date, receiver, name, subcategory = (int(payment[0]), Decimal(payment[1]), dec_strcommaspace(Decimal(payment[1])),
                                                                                   date_displstr(str_date(payment[2])), str(payment[3]), str(payment[4]), int(payment[5]))
                mapped_category = self.map_category(category, subcategory)
                if mapped_category is None:
                    continue
                text = f"{textamount} р.\t{date}\t{receiver}  ({name})"
                self.rootItem.child(self.categories.index(mapped_category)).appendChild(TreeItem((text,), self.rootItem.child(self.categories.index(mapped_category))))
        else:
            factuals, ndsfree = self.calculate_ndsfree(payments)
            for categorie, data in self.FULFILLMENT_STRUCTURE.items():
                if categorie // 10000 != 3:
                    continue
                self.rootItem.appendChild(TreeItem((data[1], data[2], factuals[categorie], ndsfree[categorie]), self.rootItem, categorie))
            for payment in payments:
                category, amount, textamount, date, receiver, name, subcategory, nds = (int(payment[0]), Decimal(str(payment[1])),
                                                                                        dec_strcommaspace(Decimal(str(payment[1]))), date_displstr(str_date(payment[2])),
                                                                                        str(payment[3]), str(payment[4]), int(payment[5]), int(payment[6]))
                mapped_category = self.map_category(category, subcategory)
                if mapped_category is None or mapped_category // 10000 != 3:
                    continue
                ndsfree_amount = self.nds_free_value(amount, nds)
                ndsfree_text = dec_strcommaspace(ndsfree_amount)
                text = f"{textamount} р. (НДС {str(nds)}%)\t {ndsfree_text} р.\t{date}\t{receiver}  ({name})"
                self.rootItem.child(self.payments_categories.index(mapped_category)).appendChild(TreeItem((text,), self.rootItem.child(self.payments_categories.index(mapped_category))))

    def map_category(self, category: int, subcategory: int) -> int | None:
        key = category if category != LiabilityCategory.TOP_FINANCES else category * 10 + subcategory
        try:
            return self.CATEGORY_MAP[key]
        except KeyError:
            log.w(f"Не найдена категория {category}/{subcategory} в CATEGORY_MAP, платеж пропущен")
            return None

    def aggregate_totals(self, values_dict: dict) -> None:
        for skey, svalue in reversed(list(self.FULFILLMENT_STRUCTURE.items())):
            if svalue[0]:
                values_dict[skey] = sum(values_dict[child] for child in svalue[0])

    def calculate_ndsfree(self, payments: list) -> tuple[dict, dict]:
        factuals_dict = dict.fromkeys(self.FULFILLMENT_STRUCTURE, 0)
        ndsfree_dict = dict.fromkeys(self.FULFILLMENT_STRUCTURE, 0)
        for payment in payments:
            category, subcategory, amount, nds = int(payment[0]), int(payment[5]), Decimal(payment[1]), int(payment[6])
            mapped_category = self.map_category(category, subcategory)
            if mapped_category is None:
                continue
            factuals_dict[mapped_category] += amount
            ndsfree_amount = self.nds_free_value(amount, nds)
            ndsfree_dict[mapped_category] += ndsfree_amount
        self.aggregate_totals(factuals_dict)
        self.aggregate_totals(ndsfree_dict)
        return factuals_dict, ndsfree_dict

    @staticmethod
    def nds_free_value(total_value: Decimal, nds: int):
        return Decimal(total_value / (1+Decimal(str(nds/100)))).quantize(Decimal('0.01'), ROUND_HALF_UP)

    def calculate_factuals(self, payments: list, inflow_values: list) -> dict:
        factuals_dict = dict.fromkeys(self.FULFILLMENT_STRUCTURE, 0)
        factuals_dict[10000], factuals_dict[21000], factuals_dict[22000], factuals_dict[23100], factuals_dict[23200] = inflow_values
        for payment in payments:
            category, subcategory = int(payment[0]), int(payment[5])
            amount = Decimal(payment[1])
            mapped_category = self.map_category(category, subcategory)
            if mapped_category is None:
                continue
            factuals_dict[mapped_category] += amount

        self.aggregate_totals(factuals_dict)

        return {key: int(Decimal(value).to_integral_value(rounding=ROUND_HALF_UP)) for key, value in factuals_dict.items()}

    def categorie_level(self, categorie: int) -> int:
        subcategories_present = bool(self.FULFILLMENT_STRUCTURE[categorie][0])
        if categorie % 10000 == 0:
            return 2
        elif (categorie % 100 == 0 and subcategories_present) or categorie == self.CATEGORY_MAP[LiabilityCategory.TOP_INVESTMENT]:
            return 1
        else:
            return 0

    def columnCount(self, parent):
        if self.rootItem is None:
            return 0
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == self.internalValueRole:
            if index.column() in (2, 3, 4, 5):
                return item.data(index.column())
            else:
                return self.data(index, Qt.ItemDataRole.DisplayRole)
        elif role == Qt.ItemDataRole.DisplayRole:
            if index.column() in (2, 3, 4):
                if item.data(index.column()) is None:
                    return ""
                elif not item.data(index.column()):
                    return "0"
                else:
                    if self.fulfillment_mode:
                        return int_strspace(item.data(index.column()))
                    else:
                        return dec_strcommaspace(item.data(index.column()))
            elif index.column() == 5:
                if item.data(index.column()) is None:
                    return ""
                elif item.data(index.column()) == -1:
                    return "—"
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
                font.setBold(self.categorie_level(categorie) in (1, 2))
                return font
            else:
                font = QFont()
                font.setPointSize(9)
                return font
        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.parent() == QModelIndex():
                categorie: int = index.internalPointer().categorie
                if self.fulfillment_mode:
                    fulfilment_value: float | None = index.internalPointer().itemData[5]
                else:
                    fulfilment_value: float | None = None
                if self.categorie_level(categorie) == 2:
                    if not self.fulfillment_mode or fulfilment_value is None or fulfilment_value <= self.NORMAL_CUTPOINT:
                        return self.plt.high
                    elif fulfilment_value < self.HIGH_CUTPOINT:
                        return self.plt.high1
                    elif fulfilment_value < self.VERYHIGH_CUTPOINT:
                        return self.plt.high2
                    else:
                        return self.plt.high3
                elif self.categorie_level(categorie) == 1:
                    if not self.fulfillment_mode or fulfilment_value is None or fulfilment_value <= self.NORMAL_CUTPOINT:
                        return self.plt.mid
                    elif fulfilment_value < self.HIGH_CUTPOINT:
                        return self.plt.mid1
                    elif fulfilment_value < self.VERYHIGH_CUTPOINT:
                        return self.plt.mid2
                    else:
                        return self.plt.mid3
                else:
                    if not self.fulfillment_mode or fulfilment_value is None or fulfilment_value <= self.NORMAL_CUTPOINT:
                        return self.plt.base
                    elif fulfilment_value < self.HIGH_CUTPOINT:
                        return self.plt.base1
                    elif fulfilment_value < self.VERYHIGH_CUTPOINT:
                        return self.plt.base2
                    else:
                        return self.plt.base3
            else:
                return None
        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if self.rootItem is None:
            return None
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
        if self.rootItem is None or parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

