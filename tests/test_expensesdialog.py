import sqlite3
from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QKeyEvent, QWheelEvent

from base.chart import ExpenseBarWidget, ExpenseMonthsWidget
from base.expenses import StructureRow
from gui.expensesdialog import ChangeItem, ExpensesDialog
from tests.test_debtcalculator import debt_db, insert_event, insert_payment  # noqa: F401

PERIOD = (QDate(2026, 10, 1), QDate(2026, 10, 31))


def make_payment(path, category: int, receiver: str, day: str, amount: str) -> int:
    event_id = insert_event(path)
    con = sqlite3.connect(path)
    try:
        con.execute("UPDATE event SET category = ?, receiver = ? WHERE id = ?", (category, receiver, event_id))
        con.commit()
    finally:
        con.close()
    insert_payment(path, event_id, day, amount)
    return event_id


def select_category(dialog: ExpensesDialog, category: int) -> None:
    for index in range(dialog.ui.lw_categories.count()):
        item = dialog.ui.lw_categories.item(index)
        if item.data(Qt.ItemDataRole.UserRole) == category:
            item.setSelected(True)


def set_receiver(dialog: ExpensesDialog, text: str) -> None:
    dialog.ui.le_receiver.setText(text)
    dialog.receiver_timer.timeout.emit()


def test_change_item_puts_missing_values_below_numbers(qapp):
    assert ChangeItem("—", None) < ChangeItem("-5%", -0.05)
    assert ChangeItem("-5%", -0.05) < ChangeItem("+5%", 0.05)


def test_dialog_counts_refunds_and_fills_tables(debt_db):
    make_payment(debt_db, 1101, "Альфа", "2026-10-10", "300.00")
    make_payment(debt_db, 1101, "Альфа", "2026-10-12", "-50.00")
    make_payment(debt_db, 1102, "Бета", "2026-10-15", "100.00")

    dialog = ExpensesDialog(*PERIOD)

    assert dialog.ui.lb_kpi1_value.text().startswith("350")
    assert "возвраты: 50" in dialog.ui.lb_kpi1_caption.text()
    assert dialog.ui.lb_kpi2_value.text().startswith("343")
    assert "Октябрь 2026" in dialog.ui.lb_kpi2_caption.text()
    assert dialog.ui.tbl_categories.rowCount() == 2
    assert dialog.ui.tbl_categories.item(0, 0).text() == "Заработная плата"
    assert dialog.ui.tbl_receivers.rowCount() == 2
    assert dialog.ui.tbl_months.rowCount() == 1
    assert dialog.ui.tbl_months.item(0, 0).text() == "Октябрь 2026"
    assert dialog.ui.tbl_payments.rowCount() == 3
    assert dialog.ui.label_period.text() == "Период: 01.10.2026 - 31.10.2026"


def test_dialog_with_empty_database(debt_db):
    dialog = ExpensesDialog(*PERIOD)

    assert dialog.ui.lb_kpi1_value.text() == "-"
    assert dialog.ui.tbl_categories.rowCount() == 0
    assert dialog.ui.tbl_payments.rowCount() == 0


def test_skip_checkboxes_exclude_finance_and_investment(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "100.00")
    make_payment(debt_db, 2100, "B", "2026-10-10", "200.00")
    make_payment(debt_db, 3100, "C", "2026-10-10", "400.00")
    dialog = ExpensesDialog(*PERIOD)
    assert dialog.ui.tbl_categories.rowCount() == 3

    dialog.ui.cb_skip_finance.setChecked(True)
    assert dialog.ui.tbl_categories.rowCount() == 2
    dialog.ui.cb_skip_investment.setChecked(True)
    assert dialog.ui.tbl_categories.rowCount() == 1
    dialog.ui.pb_reset.click()
    assert dialog.ui.tbl_categories.rowCount() == 3
    assert not dialog.ui.cb_skip_finance.isChecked()


def test_category_and_receiver_filters(debt_db):
    make_payment(debt_db, 1101, "Альфа", "2026-10-10", "100.00")
    make_payment(debt_db, 1102, "Бета", "2026-10-10", "200.00")
    dialog = ExpensesDialog(*PERIOD)

    select_category(dialog, 1102)
    assert dialog.ui.tbl_categories.rowCount() == 1

    set_receiver(dialog, "альф")
    assert dialog.ui.tbl_categories.rowCount() == 0


def test_click_on_chart_row_filters_detail_tables_and_second_click_clears(debt_db):
    make_payment(debt_db, 1101, "Альфа", "2026-10-10", "300.00")
    make_payment(debt_db, 1102, "Бета", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    assert dialog.ui.tbl_payments.rowCount() == 2

    dialog.chart.rowClicked.emit(1)
    assert dialog.focus == (1102,)
    assert dialog.ui.tbl_payments.rowCount() == 1
    assert dialog.ui.tbl_receivers.item(0, 0).text() == "Бета"
    assert dialog.ui.tbl_categories.rowCount() == 2
    assert dialog.ui.tw_report.currentWidget() is dialog.ui.tab_receivers

    dialog.chart.rowClicked.emit(1)
    assert dialog.focus is None
    assert dialog.ui.tbl_payments.rowCount() == 2


def test_focus_is_dropped_when_its_row_disappears(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "300.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.chart.rowClicked.emit(1)

    set_receiver(dialog, "A")

    assert dialog.focus is None
    assert dialog.ui.tbl_payments.rowCount() == 1


def test_compare_adds_columns_and_change(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "150.00")
    make_payment(debt_db, 1101, "A", "2026-09-20", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    assert dialog.ui.tbl_categories.columnCount() == 5
    assert dialog.ui.lb_kpi4_value.text() == "▲ +50,0%"

    dialog.ui.cb_compare.setChecked(True)

    assert dialog.ui.tbl_categories.columnCount() == 7
    assert dialog.ui.tbl_categories.item(0, 6).text() == "+50,0%"
    assert dialog.ui.tbl_categories.item(0, 5).data(Qt.ItemDataRole.UserRole) == Decimal("100.00")


def test_merge_small_categories_changes_chart_rows(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "1000.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "1.00")
    make_payment(debt_db, 1103, "C", "2026-10-10", "1.00")
    dialog = ExpensesDialog(*PERIOD)
    assert len(dialog.rows) == 3

    dialog.ui.cb_merge_small.setChecked(True)
    assert [row.categories for row in dialog.rows] == [(1101,), (1102, 1103)]
    assert dialog.row_label(dialog.rows[1]) == "Прочее (2)"


def test_export_sheets_have_all_tables(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "100.00")
    make_payment(debt_db, 1101, "A", "2026-09-20", "50.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.ui.cb_compare.setChecked(True)

    sheets = dialog.report_sheets()

    assert [sheet.name for sheet in sheets] == ["Сводка", "По категориям", "По получателям", "По месяцам", "Оплаты"]
    categories = sheets[1]
    assert len(categories.headers) == len(categories.formats) == len(categories.rows[0]) == 7
    assert sheets[4].rows[0][0] == date(2026, 10, 10)
    assert sheets[0].rows[0][1] == "01.10.2026 - 31.10.2026"


def test_chart_widgets_accept_rows_and_series(qapp):
    chart = ExpenseBarWidget(QColor("white"))
    rows = [StructureRow((1101,), Decimal(100), Decimal(50), 2, Decimal(1))]
    chart.setRows(rows, ["Заработная плата"], ["#2a78d6"], compare=True, selected=0)
    chart.setRows([], [], [])

    months = ExpenseMonthsWidget(QColor("white"))
    months.setSeries([(2026 * 12 + 10, "окт 26")], [("Заработная плата", "#2a78d6", {2026 * 12 + 10: Decimal(100)})])
    months.setSeries([], [])


def test_tables_keep_sort_order_when_filters_change(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "100.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "200.00")
    make_payment(debt_db, 2100, "C", "2026-10-10", "400.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.ui.tbl_categories.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    dialog.ui.cb_skip_finance.setChecked(True)

    header = dialog.ui.tbl_categories.horizontalHeader()
    assert (header.sortIndicatorSection(), header.sortIndicatorOrder()) == (0, Qt.SortOrder.AscendingOrder)
    assert dialog.ui.tbl_categories.item(0, 0).text() == "Заработная плата"


def test_receiver_filter_waits_for_a_pause_in_typing(debt_db):
    make_payment(debt_db, 1101, "Альфа", "2026-10-10", "100.00")
    make_payment(debt_db, 1102, "Бета", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)

    dialog.ui.le_receiver.setText("альф")

    assert dialog.receiver_timer.isActive()
    assert dialog.ui.tbl_categories.rowCount() == 2
    dialog.receiver_timer.timeout.emit()
    assert dialog.ui.tbl_categories.rowCount() == 1
    assert not dialog.receiver_timer.isActive()


def test_chart_row_click_switches_to_receivers_tab_and_categories_tab_is_hidden(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "300.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    tabs = dialog.ui.tw_report
    assert not tabs.isTabVisible(tabs.indexOf(dialog.ui.tab_categories))
    assert tabs.currentWidget() is dialog.ui.tab_receivers

    tabs.setCurrentWidget(dialog.ui.tab_payments)
    dialog.chart.rowClicked.emit(1)

    assert tabs.currentWidget() is dialog.ui.tab_receivers
    tabs.setCurrentWidget(dialog.ui.tab_months)
    dialog.chart.rowClicked.emit(1)
    assert dialog.focus is None
    assert tabs.currentWidget() is dialog.ui.tab_months


def test_reset_filters_clears_chart_focus(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "300.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.chart.rowClicked.emit(1)
    assert dialog.ui.tbl_payments.rowCount() == 1

    dialog.ui.pb_reset.click()

    assert dialog.focus is None
    assert dialog.ui.tbl_payments.rowCount() == 2


def test_double_click_on_payment_opens_event_and_reloads_report(debt_db):
    event_id = make_payment(debt_db, 1101, "A", "2026-10-10", "300.00")
    opened = []

    def open_event(opened_id: int, parent) -> bool:
        opened.append(opened_id)
        make_payment(debt_db, 1101, "A", "2026-10-11", "50.00")
        return True

    dialog = ExpensesDialog(*PERIOD, open_event=open_event)
    assert dialog.ui.tbl_payments.rowCount() == 1

    dialog.ui.tbl_payments.cellDoubleClicked.emit(0, 0)

    assert opened == [event_id]
    assert dialog.ui.tbl_payments.rowCount() == 2


def test_merged_row_lists_its_categories_and_is_gray(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "1000.00")
    make_payment(debt_db, 1102, "B", "2026-10-10", "1.00")
    make_payment(debt_db, 1103, "C", "2026-10-10", "1.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.ui.cb_merge_small.setChecked(True)

    assert dialog.row_color(dialog.rows[0]) == dialog.TOP_COLORS[0]
    assert dialog.row_color(dialog.rows[1]) == ExpenseBarWidget.OTHER_COLOR
    details = dialog.row_details(dialog.rows[1])
    assert "Налоги и сборы" in details and "Расходные мат-лы" in details
    assert "Налоги и сборы" in dialog.chart.hints[1]


def test_categories_list_has_unselectable_section_headers(debt_db):
    dialog = ExpensesDialog(*PERIOD)
    headers = [item for item in (dialog.ui.lw_categories.item(index) for index in range(dialog.ui.lw_categories.count()))
               if item.data(Qt.ItemDataRole.UserRole) is None]

    assert [item.text() for item in headers] == ["Текущая деятельность", "Финансы и инвестиции"]
    assert all(not item.flags() & Qt.ItemFlag.ItemIsSelectable for item in headers)


def test_tile_shows_growth_with_arrow_and_color(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "50.00")
    make_payment(debt_db, 1101, "A", "2026-09-20", "100.00")
    dialog = ExpensesDialog(*PERIOD)

    assert dialog.ui.lb_kpi4_value.text() == "▼ -50,0%"
    assert ExpenseBarWidget.DROP_COLOR in dialog.ui.lb_kpi4_value.styleSheet()
    assert dialog.report_sheets()[0].rows[-1][1] == "-50,0%"


def test_bar_chart_keyboard_navigation(qapp):
    chart = ExpenseBarWidget(QColor("white"))
    rows = [StructureRow((code,), Decimal(100 - code), Decimal(0), 1, Decimal("0.33")) for code in range(1, 4)]
    chart.setRows(rows, ["a", "b", "c"], ["#2a78d6"] * 3)
    clicked, revealed = [], []
    chart.rowClicked.connect(clicked.append)
    chart.rowRevealed.connect(revealed.append)

    def press(key) -> None:
        chart.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))

    press(Qt.Key.Key_Down)
    assert chart.cursor_row == 0
    assert chart.cursor_shown
    press(Qt.Key.Key_Down)
    press(Qt.Key.Key_Down)
    press(Qt.Key.Key_Down)
    assert chart.cursor_row == 2
    press(Qt.Key.Key_Home)
    assert chart.cursor_row == 0
    press(Qt.Key.Key_Return)
    assert clicked == [0]
    assert len(revealed) == 5


def test_bar_chart_wheel_is_left_for_the_scroll_area(qapp):
    chart = ExpenseBarWidget(QColor("white"))
    position = QPointF(10, 10)
    event = QWheelEvent(position, position, QPoint(0, 0), QPoint(0, -120), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)

    chart.plot.wheelEvent(event)

    assert not event.isAccepted()


def test_months_legend_hides_and_shows_series(qapp):
    months = ExpenseMonthsWidget(QColor("white"))
    month = 2026 * 12 + 10
    months.setSeries([(month, "окт 26")], [("Аренда", "#2a78d6", {month: Decimal(100)}),
                                           ("Налоги", "#eb6834", {month: Decimal(50)})])
    assert "Аренда" in months.legend.text() and "Налоги" in months.legend.text()
    assert [item[0] for item in months.segments[0]] == ["Аренда", "Налоги"]

    months.toggleSeries("0")

    assert [item[0] for item in months.segments[0]] == ["Налоги"]
    assert months.nets == [50.0]
    assert "<s>Аренда</s>" in months.legend.text()
    assert months.tooltipText(0, "Налоги").splitlines() == ["окт 26", "Итого: 50", "▶ Налоги: 50"]
    months.toggleSeries("0")
    assert [item[0] for item in months.segments[0]] == ["Аренда", "Налоги"]


def test_months_chart_is_stacked_only_for_few_categories(debt_db):
    for category in range(1101, 1101 + ExpensesDialog.STACK_LIMIT):
        make_payment(debt_db, category, "A", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    assert len(dialog.months_chart.series) == ExpensesDialog.STACK_LIMIT

    make_payment(debt_db, 1101 + ExpensesDialog.STACK_LIMIT, "A", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)

    assert [name for name, _, _ in dialog.months_chart.series] == [ExpensesDialog.ALL_NAME]
    assert dialog.months_chart.legend.text() == ""
    dialog.chart.rowClicked.emit(0)
    assert len(dialog.months_chart.series) == 1


def test_previous_period_dates_default_to_previous_full_month_and_follow_the_checkbox(debt_db):
    dialog = ExpensesDialog(*PERIOD)

    assert dialog.ui.de_prev_start.date() == QDate(2026, 9, 1)
    assert dialog.ui.de_prev_end.date() == QDate(2026, 9, 30)
    assert not dialog.ui.de_prev_start.isEnabled() and not dialog.ui.de_prev_end.isEnabled()
    dialog.ui.cb_compare.setChecked(True)
    assert dialog.ui.de_prev_start.isEnabled() and dialog.ui.de_prev_end.isEnabled()


def test_changing_previous_period_dates_rebuilds_comparison_and_keeps_dates_ordered(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "300.00")
    make_payment(debt_db, 1101, "A", "2026-09-10", "100.00")
    make_payment(debt_db, 1101, "A", "2026-03-10", "50.00")
    dialog = ExpensesDialog(*PERIOD)
    dialog.ui.cb_compare.setChecked(True)
    assert dialog.rows[0].previous == Decimal("100.00")

    dialog.ui.de_prev_start.setDate(QDate(2026, 3, 1))
    dialog.ui.de_prev_end.setDate(QDate(2026, 3, 31))

    assert dialog.rows[0].previous == Decimal("50.00")
    dialog.ui.de_prev_start.setDate(QDate(2026, 4, 15))
    assert dialog.ui.de_prev_end.date() == QDate(2026, 4, 15)
    dialog.ui.de_prev_end.setDate(QDate(2026, 4, 1))
    assert dialog.ui.de_prev_start.date() == QDate(2026, 4, 1)
    assert dialog.previous_start == date(2026, 4, 1) and dialog.previous_end == date(2026, 4, 1)


def test_category_columns_sort_by_category_number_not_by_text(debt_db):
    for category in (1110, 1102, 2100, 0, 1101, 1116, 1109):
        make_payment(debt_db, category, "A", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)
    expected = [1101, 1102, 1109, 1110, 1116, 2100, 0]

    for table, column in ((dialog.ui.tbl_categories, 0), (dialog.ui.tbl_payments, 3)):
        table.sortByColumn(column, Qt.SortOrder.AscendingOrder)
        assert [table.item(row, column).data(Qt.ItemDataRole.UserRole) for row in range(table.rowCount())] == expected
        table.sortByColumn(column, Qt.SortOrder.DescendingOrder)
        assert [table.item(row, column).data(Qt.ItemDataRole.UserRole) for row in range(table.rowCount())] == expected[::-1]


def test_months_table_is_not_narrower_than_its_columns(debt_db):
    make_payment(debt_db, 1101, "A", "2026-10-10", "100.00")
    dialog = ExpensesDialog(*PERIOD)

    table = dialog.ui.tbl_months
    header = table.horizontalHeader()
    assert table.minimumWidth() >= sum(header.sectionSize(column) for column in range(1, table.columnCount()))
