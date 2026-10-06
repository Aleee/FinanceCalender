import resources_rc
import lovely_logger as log
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIcon, QFont

from base.liability import CATEGORY_NAMES, TermCategory


class FilterListWidget(QtWidgets.QListWidget):

    ITEMS = {}

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Цвет выделения в фокусе и без
        self.setStyleSheet("""QListWidget::item:selected {background-color: #dae8f5; color: black;}
                    QListWidget::item:selected:!focus {background-color: #dae8f5; color: black;}""")

        # Присвоение имен и иконок
        for entry in self.ITEMS.values():
            self.addItem(QtWidgets.QListWidgetItem(QIcon(entry[1]), entry[0]))
        self.setCurrentRow(0)

    def update_height(self) -> None:
        # Подгонка высоты виджета под размер шрифта
        item_height: int = self.sizeHintForRow(0)
        total_items: int = self.count()
        frame_width: int = self.frameWidth() * 2
        required_height: int = item_height * total_items + frame_width
        self.setFixedHeight(required_height)

    @QtCore.Slot(object)
    def update_labels(self, stats: dict) -> None:
        if len(stats) != len(self.ITEMS):
            log.e("Длина словаря, переданная функции, не соответствует количеству элементов в списке")
            raise IndexError
        stats_as_list = list(stats.values())
        for row in range(self.count()):
            item = self.item(row)
            item.setText(self.ITEMS[row][0] + f" ({stats_as_list[row]})")
            font = QFont()
            font.setBold(self.ITEMS[row][2])
            item.setFont(font)


class TermFilterListWidget(FilterListWidget):

    FILTER_ID = "term_filter"
    ITEMS = {
        TermCategory.UNPAID: ("Все неоплаченные", ":/icon-terms/designer/icons/allitems.svg", True),    # 2 - is bold
        TermCategory.DUE: ("Просроченные", ":/icon-terms/designer/icons/termdue.svg", False),
        TermCategory.TODAY: ("Сегодня", ":/icon-terms/designer/icons/termtoday.svg", False),
        TermCategory.WEEK: ("На этой неделе", ":/icon-terms/designer/icons/termweek.svg", False),
        TermCategory.MONTH: ("В этом месяце", ":/icon-terms/designer/icons/termmonth.svg", False),
        TermCategory.PAID: ("Оплаченные", ":/icon-terms/designer/icons/termpaid.svg", True),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

    def current_term(self) -> TermCategory:
        return list(self.ITEMS.keys())[self.currentRow()]


class CategoryFilterListWidget(FilterListWidget):

    FILTER_ID = "category_filter"
    ITEMS = {
        0: ("Все", ":/icon-categories/designer/icons/000all.svg", True),
        1: ("Заработная плата", ":/icon-categories/designer/icons/101loan.svg", False),
        2: ("Налоги и сборы", ":/icon-categories/designer/icons/102taxes.svg", False),
        3: ("Расходные мат-лы", ":/icon-categories/designer/icons/103stuff.svg", False),
        4: ("Энергоносители", ":/icon-categories/designer/icons/104energy.svg", False),
        5: ("Маркетинг", ":/icon-categories/designer/icons/105marketing.svg", False),
        6: ("Аренда офисов", ":/icon-categories/designer/icons/106office.svg", False),
        7: ("Аренда помещений", ":/icon-categories/designer/icons/107buildings.svg", False),
        8: ("Оргтехника", ":/icon-categories/designer/icons/108printer.svg", False),
        9: ("Текущие расходы", ":/icon-categories/designer/icons/109other.svg", False),
        10: ("Обслуж-е зданий", ":/icon-categories/designer/icons/110maintenance.svg", False),
        11: ("Банковские расходы", ":/icon-categories/designer/icons/111bank.svg", False),
        12: ("Связь", ":/icon-categories/designer/icons/112phone.svg", False),
        13: ("Обучение", ":/icon-categories/designer/icons/113education.svg", False),
        14: ("Услуги организаций", ":/icon-categories/designer/icons/114goods.svg", False),
        15: ("Комиссии", ":/icon-categories/designer/icons/115rate.svg", False),
        16: ("Медоборудование", ":/icon-categories/designer/icons/116medequipment.svg", False),
        17: ("Финансовая д-ть", ":/icon-categories/designer/icons/200finance.svg", False),
        18: ("Инвестиционная д-ть", ":/icon-categories/designer/icons/300invest.svg", False),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

    def current_category(self) -> int:
        row = self.currentRow()
        if row == 0:
            return 0
        return list(CATEGORY_NAMES.keys())[row]
