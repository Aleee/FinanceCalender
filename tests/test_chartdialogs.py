from PySide6.QtCore import QDate, Qt

from base.liability import LiabilityCategory
from gui.chartdialogs import DebtChartDialog
from gui.filterwidget import CategoryFilterListWidget
from tests.test_debtcalculator import debt_db  # noqa: F401


def test_debt_chart_dialog_lists_all_categories_with_their_names(debt_db):
    dialog = DebtChartDialog(QDate(2026, 10, 1), QDate(2026, 10, 31))

    list_widget = dialog.ui.lw_categories
    categories = [list_widget.item(row).data(Qt.ItemDataRole.UserRole) for row in range(list_widget.count())]
    assert categories == [member.value for member in LiabilityCategory][1:]
    assert list_widget.item(0).text() == CategoryFilterListWidget.ITEMS[LiabilityCategory.SALARIES][0]
