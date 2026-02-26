from enum import IntEnum

import resources_rc
import lovely_logger as log
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIcon, QBrush, QFont


class TermCategory(IntEnum):
    UNPAID = 0
    DUE = 1
    TODAY = 2
    WEEK = 3
    MONTH = 4
    PAID = 5


class FilterListWidget(QtWidgets.QListWidget):

    ITEMS = {}

    def __init__(self, parent=None):
        super(FilterListWidget, self).__init__(parent)

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
        super(TermFilterListWidget, self).__init__(parent)

    @QtCore.Slot(object)
    def update_labels(self, stats: dict) -> None:
        try:
            filter_stats: dict = stats["term_filter"]
        except KeyError:
            log.x(f"В словаре, переданном функции, отсутствует часть '{self.FILTER_ID}'")
            raise KeyError
        if len(filter_stats) != len(self.ITEMS):
            log.x("Длина словаря, переданная функции, не соответствует количеству элементов в списке")
            raise IndexError
        for row in range(self.count()):
            self.item(row).setText(self.ITEMS[row][0] + f" ({len(filter_stats[row])})")
            font = QFont()
            font.setBold(self.ITEMS[row][2])
            self.item(row).setFont(font)


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
        super(CategoryFilterListWidget, self).__init__(parent)

        self.term_filter_state_paid: bool = False
        self.saved_stats: dict | None = None

    @QtCore.Slot(bool)
    def on_term_filter_state_change(self, is_paid_chosen: bool) -> None:
        self.term_filter_state_paid = is_paid_chosen
        self.update_labels()

    @QtCore.Slot(object)
    def update_labels(self, stats: dict | None = None) -> None:
        if not stats:
            stats = self.saved_stats
        try:
            category_paid_stats: dict = stats["category_filter_paid"]
            category_notpaid_stats: dict = stats["category_filter_notpaid"]
        except KeyError:
            log.x(f"В словаре, переданном функции, отсутствует часть '{self.FILTER_ID}'")
            raise KeyError
        if len(category_paid_stats) != len(self.ITEMS) or len(category_notpaid_stats) != len(self.ITEMS):
            log.x("Длина словаря, переданная функции, не соответствует количеству элементов в списке")
            raise IndexError
        self.saved_stats = stats
        stats_as_list: list = list(category_paid_stats.values()) if self.term_filter_state_paid else list(category_notpaid_stats.values())
        for row in range(self.count()):
            self.item(row).setText(self.ITEMS[row][0] + f" ({len(stats_as_list[row]) if self.term_filter_state_paid else len(stats_as_list[row])})")
            font = QFont()
            font.setBold(self.ITEMS[row][2])
            self.item(row).setFont(font)
