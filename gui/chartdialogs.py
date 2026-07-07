from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QDialog, QListWidgetItem, QVBoxLayout
import lovely_logger as log

from base.chart import DebtChartWidget
from base.debtcalculator import DebtRepository, DebtTimelineBuilder
from base.liability import LiabilityCategory, CATEGORY_NAMES
from gui.filterwidget import CategoryFilterListWidget
from gui.ui.debtchartdialog_ui import Ui_DebtChartDialog


class DebtChartDialog(QDialog):

    def __init__(self, start_date: QDate, end_date: QDate, parent=None):
        super(DebtChartDialog, self).__init__(parent)
        self.ui = Ui_DebtChartDialog()
        self.ui.setupUi(self)

        self.start_date: QDate = start_date
        self.end_date: QDate = end_date

        for index, category in enumerate([member.value for member in LiabilityCategory]):
            if index == 0:
                continue
            new_item = QListWidgetItem(CategoryFilterListWidget.ITEMS[index][0])
            new_item.setData(Qt.ItemDataRole.UserRole, category)
            self.ui.lw_categories.addItem(new_item)

        self.all_categories = [self.ui.lw_categories.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.ui.lw_categories.count())]

        self.repo = DebtRepository()
        self.builder = DebtTimelineBuilder(self.repo)
        self.builder.load()

        self.placeholder_layout = QVBoxLayout()
        self.ui.widget.setLayout(self.placeholder_layout)

        self.plot()

        self.ui.spb_smooth.valueChanged.connect(self.replot)

        self.ui.lw_categories.itemSelectionChanged.connect(self.replot)



    def plot(self):
        timeline = self.builder.build(
            begin=self.start_date.toPython(),
            end=self.end_date.toPython(),
            categories=self.all_categories,
        )

        palette = self.palette()
        qt_window_color = palette.color(QPalette.ColorRole.Window)

        self.chart = DebtChartWidget(qt_window_color)
        self.chart.setTimeline(timeline, smoothing=10)
        self.chart.resize(1000, 500)
        self.ui.widget.layout().addWidget(self.chart)

    def replot(self):
        selected_items = self.ui.lw_categories.selectedItems()
        if len(selected_items) == 0:
            categories_to_count = self.all_categories
        else:
            categories_to_count = []
            for item in selected_items:
                categories_to_count.append(item.data(Qt.ItemDataRole.UserRole))

        timeline = self.builder.build(
            begin=self.start_date.toPython(),
            end=self.end_date.toPython(),
            categories=set(categories_to_count),
        )
        self.chart.setTimeline(timeline, smoothing=self.ui.spb_smooth.value())


