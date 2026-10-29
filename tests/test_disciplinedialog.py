import sqlite3
from datetime import date

from PySide6.QtCore import QDate, Qt

from base.chart import DelayChartWidget
from base.discipline import DelayBucket
from base.liability import CATEGORY_NAMES, LiabilityCategory
from gui.disciplinedialog import DisciplineDialog, NumberItem
from tests.test_debtcalculator import debt_db, insert_event, insert_payment  # noqa: F401

PERIOD = (QDate(2026, 10, 1), QDate(2026, 10, 31))


def test_number_item_sorts_by_value_not_by_text(qapp):
    assert NumberItem("9", 9) < NumberItem("10", 10)
    assert not NumberItem("10", 10) < NumberItem("9", 9)


def test_dialog_fills_summary_and_tables(debt_db):
    late = insert_event(debt_db)
    in_time = insert_event(debt_db)
    insert_event(debt_db)
    insert_payment(debt_db, late, "2026-10-15", "100.00")
    insert_payment(debt_db, in_time, "2026-10-10", "100.00")

    dialog = DisciplineDialog(*PERIOD)

    assert dialog.ui.lb_kpi1_value.text() == "50,0%"
    assert dialog.ui.lb_kpi2_value.text() == "1 из 2"
    assert dialog.ui.lb_kpi4_value.text() == "1"
    assert dialog.ui.tbl_receivers.rowCount() == 1
    assert dialog.ui.tbl_receivers.item(0, 0).text() == "r"
    assert dialog.ui.tbl_receivers.item(0, 1).text() == "2"
    assert dialog.ui.tbl_receivers.item(0, 3).text() == "1"
    assert dialog.ui.tbl_categories.item(0, 0).text() == CATEGORY_NAMES[LiabilityCategory.SALARIES]
    assert dialog.ui.tbl_months.item(0, 0).text() == "Октябрь 2026"
    assert dialog.ui.tbl_overdue.rowCount() == 1
    assert dialog.ui.tbl_overdue.item(0, 4).text() == "100,00"
    assert dialog.ui.tw_report.tabText(dialog.ui.tw_report.indexOf(dialog.ui.tab_overdue)).endswith("(1)")
    assert dialog.ui.tbl_closed.rowCount() == 2
    assert dialog.ui.tbl_closed.item(0, 6).text() == "5"


def test_dialog_ignores_payments_outside_period(debt_db):
    event_id = insert_event(debt_db)
    insert_payment(debt_db, event_id, "2026-09-15", "100.00")

    dialog = DisciplineDialog(*PERIOD)

    assert dialog.ui.lb_kpi1_value.text() == "-"
    assert dialog.ui.tbl_receivers.rowCount() == 0
    assert dialog.ui.tbl_overdue.rowCount() == 0


def test_dialog_with_empty_database(debt_db):
    dialog = DisciplineDialog(*PERIOD)

    assert dialog.ui.tbl_months.rowCount() == 0
    assert dialog.ui.tw_report.tabText(dialog.ui.tw_report.indexOf(dialog.ui.tab_overdue)).endswith("(0)")
    assert dialog.ui.lb_kpi1_value.text() == "-"
    assert "0,00" in dialog.ui.lb_overdue.text()
    assert dialog.ui.label_period.text() == "Период: 01.10.2026 - 31.10.2026"


def make_paid_event(path, category: int, receiver: str) -> None:
    event_id = insert_event(path)
    con = sqlite3.connect(path)
    try:
        con.execute("UPDATE event SET category = ?, receiver = ? WHERE id = ?", (category, receiver, event_id))
        con.commit()
    finally:
        con.close()
    insert_payment(path, event_id, "2026-10-15", "100.00")


def select_category(dialog: DisciplineDialog, category: int) -> None:
    for index in range(dialog.ui.lw_categories.count()):
        item = dialog.ui.lw_categories.item(index)
        if item.data(Qt.ItemDataRole.UserRole) == category:
            item.setSelected(True)


def test_dialog_filters_by_category_and_receiver(debt_db):
    make_paid_event(debt_db, 1101, "ООО Ромашка")
    make_paid_event(debt_db, 1103, "ИП Петров")
    make_paid_event(debt_db, 1103, "ООО Ромашка")

    dialog = DisciplineDialog(*PERIOD)
    assert dialog.ui.tbl_categories.rowCount() == 2
    assert dialog.ui.tbl_receivers.rowCount() == 2

    select_category(dialog, 1103)
    assert dialog.ui.tbl_categories.rowCount() == 1
    assert dialog.ui.tbl_receivers.rowCount() == 2

    dialog.ui.le_receiver.setText("ромашка")
    assert dialog.ui.tbl_receivers.rowCount() == 1
    assert dialog.ui.tbl_receivers.item(0, 1).text() == "1"

    dialog.ui.le_receiver.setText("нет такого")
    assert dialog.ui.tbl_receivers.rowCount() == 0
    assert dialog.ui.lb_kpi1_value.text() == "-"


def test_group_selects_all_current_categories(debt_db):
    dialog = DisciplineDialog(*PERIOD)
    group_item = dialog.group_item

    group_item.setSelected(True)
    assert all(item.isSelected() for item in dialog.group_children)

    dialog.group_children[0].setSelected(False)
    assert not group_item.isSelected()

    dialog.group_children[0].setSelected(True)
    assert group_item.isSelected()

    group_item.setSelected(False)
    assert not any(item.isSelected() for item in dialog.group_children)


def test_group_selection_filters_only_current_categories(debt_db):
    make_paid_event(debt_db, 1101, "a")
    make_paid_event(debt_db, 2100, "b")

    dialog = DisciplineDialog(*PERIOD)
    assert dialog.ui.tbl_receivers.rowCount() == 2

    dialog.group_item.setSelected(True)
    assert dialog.ui.tbl_receivers.rowCount() == 1
    assert dialog.ui.tbl_receivers.item(0, 0).text() == "a"


def test_bucket_click_filters_tables_and_second_click_resets(debt_db):
    make_paid_event(debt_db, 1101, "late")
    on_time = insert_event(debt_db)
    insert_payment(debt_db, on_time, "2026-10-09", "100.00")

    dialog = DisciplineDialog(*PERIOD)
    assert dialog.ui.tbl_closed.rowCount() == 2

    dialog.on_bucket_clicked(DelayBucket.WEEK)
    assert dialog.ui.tbl_closed.rowCount() == 1
    assert dialog.ui.tbl_closed.item(0, 6).text() == "5"
    assert dialog.ui.tbl_receivers.rowCount() == 1

    dialog.on_bucket_clicked(DelayBucket.WEEK)
    assert dialog.bucket is None
    assert dialog.ui.tbl_closed.rowCount() == 2


def test_overdue_column_click_opens_overdue_tab(debt_db):
    dialog = DisciplineDialog(*PERIOD)

    dialog.on_bucket_clicked(DelayChartWidget.OVERDUE_INDEX)

    assert dialog.ui.tw_report.currentWidget() is dialog.ui.tab_overdue
    assert dialog.bucket is None


def test_bucket_is_reset_when_it_becomes_empty(debt_db):
    make_paid_event(debt_db, 1101, "late")
    dialog = DisciplineDialog(*PERIOD)
    dialog.on_bucket_clicked(DelayBucket.WEEK)
    assert dialog.bucket == DelayBucket.WEEK

    dialog.ui.le_receiver.setText("нет такого")

    assert dialog.bucket is None


def test_reset_clears_all_filters(debt_db):
    make_paid_event(debt_db, 1101, "a")
    dialog = DisciplineDialog(*PERIOD)
    select_category(dialog, 1103)
    dialog.ui.le_receiver.setText("a")
    assert dialog.ui.tbl_closed.rowCount() == 0

    dialog.ui.pb_reset.click()

    assert dialog.ui.le_receiver.text() == ""
    assert not dialog.ui.lw_categories.selectedItems()
    assert dialog.ui.tbl_closed.rowCount() == 1


def test_count_amount_toggle_rebuilds_chart(debt_db):
    make_paid_event(debt_db, 1101, "a")
    dialog = DisciplineDialog(*PERIOD)

    dialog.ui.rb_amount.setChecked(True)

    assert dialog.chart.plot.getAxis("left").labelText == "Сумма, руб."


def test_short_headers_have_full_names_in_tooltips(debt_db):
    dialog = DisciplineDialog(*PERIOD)

    table = dialog.ui.tbl_receivers
    assert table.horizontalHeaderItem(4).toolTip() == "Сумма опозданий"
    assert table.horizontalHeaderItem(6).toolTip().startswith("Средняя задержка, дн.")
    assert table.horizontalHeaderItem(7).toolTip() == "Максимальная задержка, дн."
    assert table.horizontalHeaderItem(5).toolTip().startswith("В срок, % по кол-ву")
    assert table.horizontalHeaderItem(1).toolTip() == ""


def test_amount_mode_switches_in_time_share_to_amount(debt_db):
    small_late = insert_event(debt_db)
    big_in_time = insert_event(debt_db)
    con = sqlite3.connect(debt_db)
    con.execute("UPDATE event SET totalamount = '300.00' WHERE id = ?", (big_in_time,))
    con.commit()
    con.close()
    insert_payment(debt_db, small_late, "2026-10-15", "100.00")
    insert_payment(debt_db, big_in_time, "2026-10-09", "300.00")
    dialog = DisciplineDialog(*PERIOD)
    table = dialog.ui.tbl_receivers

    assert dialog.ui.lb_kpi1_value.text() == "50,0%"
    assert table.item(0, 5).text() == "50,0%"
    assert table.horizontalHeaderItem(5).data(Qt.ItemDataRole.UserRole) == "В срок, % по кол-ву"

    dialog.ui.rb_amount.setChecked(True)

    assert dialog.ui.lb_kpi1_value.text() == "75,0%"
    assert table.item(0, 5).text() == "75,0%"
    assert table.horizontalHeaderItem(5).data(Qt.ItemDataRole.UserRole) == "В срок, % по сумме"

    dialog.ui.rb_count.setChecked(True)

    assert table.item(0, 5).text() == "50,0%"


def test_export_is_disabled_without_settings(debt_db):
    assert not DisciplineDialog(*PERIOD).ui.pb_export.isEnabled()


def test_report_sheets_follow_tables(debt_db):
    make_paid_event(debt_db, 1101, "ООО Ромашка")
    dialog = DisciplineDialog(*PERIOD)

    sheets = {sheet.name: sheet for sheet in dialog.report_sheets()}

    assert list(sheets) == ["Сводка", "Распределение", "По получателям", "По категориям", "По месяцам",
                            "Оплаченные платежи", "Неоплаченные просроченные"]
    closed = sheets["Оплаченные платежи"]
    assert closed.rows[0][0] == "ООО Ромашка"
    assert closed.rows[0][3] == date(2026, 10, 10)
    assert closed.rows[0][4] == date(2026, 10, 15)
    assert closed.rows[0][6] == 5
    receivers = sheets["По получателям"]
    assert chr(10) not in "".join(receivers.headers)
    assert receivers.headers[3:] == ["Опоздало, шт.", "Сумма опозданий", "В срок, % по кол-ву", "Средняя задержка, дн.",
                                     "Максимальная задержка, дн."]
    assert receivers.rows[0][3] == 1
    distribution = sheets["Распределение"]
    assert [row[1] for row in distribution.rows] == [0, 1, 0, 0, 0]
