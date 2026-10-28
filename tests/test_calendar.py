from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem

from base.liability import TermCategory
from base.liabilitystore import CalendarDay
from gui.calendarwidget import CalendarWidget, DayStatus, MonthGridModel, day_count_text, day_status, day_title, day_tooltip
from tests.test_readpath import TODAY, add_event, add_payment, day, db_file, models, open_models, reload  # noqa: F401


def test_calendar_days_group_by_due_date_and_sum_remain(models):
    first = add_event(models.path, total="1000.00", due=day(0))
    second = add_event(models.path, total="500.00", due=day(0))
    add_payment(models.path, second, day(0), "200.00")
    third = add_event(models.path, total="100.00", due=day(5))
    reload(models)

    days, undated = models.store.calendar_days()

    assert undated == 0
    assert set(days) == {TODAY, TODAY.addDays(5)}
    assert set(days[TODAY].event_ids) == {first, second}
    assert days[TODAY].remain == Decimal("1300")
    assert days[TODAY.addDays(5)] == CalendarDay((third,), Decimal("100"), Decimal("100"), 1)


def test_calendar_day_lists_largest_remain_first_and_paid_last(models):
    paid = add_event(models.path, total="900.00", due=day(0))
    add_payment(models.path, paid, day(-1), "900.00")
    small = add_event(models.path, total="100.00", due=day(0))
    large = add_event(models.path, total="700.00", due=day(0))
    middle = add_event(models.path, total="300.00", due=day(0))
    reload(models)

    assert models.store.calendar_days()[0][TODAY].event_ids == (large, middle, small, paid)


def test_calendar_days_count_events_without_due_date(models):
    add_event(models.path, due=day(1))
    add_event(models.path, due="")
    add_event(models.path, due="")
    reload(models)

    days, undated = models.store.calendar_days()

    assert list(days) == [TODAY.addDays(1)]
    assert undated == 2


def test_calendar_days_follow_sidebar_filters_except_term(models):
    unpaid = add_event(models.path, total="100.00", due=day(1), receiver="Альфа")
    other = add_event(models.path, total="100.00", due=day(1), receiver="Бета")
    paid = add_event(models.path, total="100.00", due=day(2), receiver="Альфа")
    add_payment(models.path, paid, day(-1), "100.00")
    reload(models)

    days = models.store.calendar_days()[0]
    assert set(days[TODAY.addDays(1)].event_ids) == {unpaid, other}
    assert days[TODAY.addDays(2)] == CalendarDay((paid,), Decimal(0), Decimal("100"), 0)

    models.apply(term=TermCategory.PAID)
    assert set(models.store.calendar_days()[0]) == {TODAY.addDays(1), TODAY.addDays(2)}

    models.apply(term=TermCategory.UNPAID, search="альфа")
    days = models.store.calendar_days()[0]
    assert days[TODAY.addDays(1)].event_ids == (unpaid,)
    assert days[TODAY.addDays(2)].event_ids == (paid,)


def test_calendar_days_ignore_period_filter(models):
    near = add_event(models.path, due=day(1))
    far = add_event(models.path, due=day(20))
    reload(models)

    models.store.set_filters(TermCategory.UNPAID, 0, "", 0, False, 3, False, TODAY.addDays(10), None)

    assert [row.event_id for row in models.store.visible_rows() if row.event_id] == [far]
    assert {event_id for entry in models.store.calendar_days()[0].values() for event_id in entry.event_ids} == {near, far}


def test_calendar_days_skip_service_rows(models):
    add_event(models.path, due=day(1))
    reload(models)
    models.store.set_header_filter(True)
    models.store.set_footer_filter(True)

    days, undated = models.store.calendar_days()

    assert sum(len(entry.event_ids) for entry in days.values()) == 1
    assert undated == 0


def test_day_status():
    today = QDate(2026, 10, 28)

    assert day_status(today, None, today) is None
    assert day_status(today, CalendarDay((1,), Decimal(10)), today) == DayStatus.OPEN
    assert day_status(today.addDays(3), CalendarDay((1,), Decimal(10)), today) == DayStatus.OPEN
    assert day_status(today.addDays(-1), CalendarDay((1,), Decimal(10)), today) == DayStatus.OVERDUE
    assert day_status(today.addDays(-1), CalendarDay((1,), Decimal(0)), today) == DayStatus.PAID
    assert day_status(today.addDays(-1), CalendarDay((1,), Decimal(0), Decimal(-5)), today) == DayStatus.REFUND


def test_day_count_text_shows_unpaid_share_only_for_mixed_day():
    assert day_count_text(CalendarDay((1, 2), Decimal(10), Decimal(20), 2)) == "2 пл."
    assert day_count_text(CalendarDay((1, 2), Decimal(10), Decimal(20), 1)) == "1 из 2"
    assert day_count_text(CalendarDay((1, 2), Decimal(0), Decimal(20), 0)) == "2 пл."


def test_day_tooltip_explains_status_and_amount():
    today = QDate(2026, 10, 28)
    mixed = CalendarDay((1, 2), Decimal(10), Decimal(20), 1)

    text = day_tooltip(today.addDays(-1), mixed, DayStatus.OVERDUE)

    assert "Просрочено" in text and "не оплачено: 1" in text and "Остаток" in text
    assert "Возврат" in day_tooltip(today, CalendarDay((1,), Decimal(0), Decimal(-5)), DayStatus.REFUND)


def test_month_grid_starts_on_monday_and_marks_weekends(models, qapp):
    model = MonthGridModel(models.store.db_handler)
    model.set_month(QDate(2026, 10, 15))

    assert model.month == QDate(2026, 10, 1)
    assert model.first_cell == QDate(2026, 9, 28)
    assert model.rowCount() == 6 and model.columnCount() == 7
    assert [model.headerData(section, Qt.Orientation.Horizontal) for section in range(7)] == [
        "Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    index = model.index_of(QDate(2026, 10, 15))
    assert (index.row(), index.column()) == (2, 3)
    assert model.date_at(index) == QDate(2026, 10, 15)
    assert model.data(model.index_of(QDate(2026, 10, 3)), MonthGridModel.NonWorkingRole)
    assert not model.data(model.index_of(QDate(2026, 10, 5)), MonthGridModel.NonWorkingRole)
    assert not model.index_of(QDate(2026, 12, 1)).isValid()


def test_month_grid_covers_month_that_starts_on_sunday(models, qapp):
    model = MonthGridModel(models.store.db_handler)
    model.set_month(QDate(2026, 11, 1))

    assert model.first_cell == QDate(2026, 10, 26)
    assert model.index_of(QDate(2026, 11, 30)).isValid()


def make_widget(models) -> CalendarWidget:
    return CalendarWidget(models.store, models.store.db_handler)


def test_widget_shows_payments_of_selected_day(models, qapp):
    first = add_event(models.path, total="1000.00", due=day(0), receiver="Альфа")
    add_event(models.path, total="500.00", due=day(0), receiver="Бета")
    add_event(models.path, due="")
    reload(models)

    widget = make_widget(models)

    assert widget.model.month == QDate(TODAY.year(), TODAY.month(), 1)
    assert widget.selected == TODAY
    assert widget.ui.tbl_events.rowCount() == 2
    assert {widget.ui.tbl_events.item(row, 0).text() for row in range(2)} == {"Альфа", "Бета"}
    assert "1" in widget.ui.pb_undated.text()
    row = next(row for row in range(2) if widget.ui.tbl_events.item(row, 0).text() == "Альфа")
    assert widget.ui.tbl_events.item(row, 1).text() == "1 000,00"
    assert widget.ui.tbl_events.item(row, 0).data(Qt.ItemDataRole.UserRole) == first


def test_widget_remain_is_the_second_column_and_red_only_when_overdue(models, qapp):
    add_event(models.path, total="100.00", due=day(-3), receiver="Просрочен")
    add_event(models.path, total="200.00", due=day(3), receiver="Впереди")
    paid_late = add_event(models.path, total="300.00", due=day(-3), receiver="Оплачен")
    add_payment(models.path, paid_late, day(-1), "300.00")
    reload(models)
    widget = make_widget(models)
    table = widget.ui.tbl_events

    assert widget.EVENT_HEADERS == ("Получатель", "Остаток", "Название")

    widget.show_date(TODAY.addDays(-3))
    items = {table.item(row, 0).text(): table.item(row, 1) for row in range(table.rowCount())}
    assert items["Просрочен"].foreground().color() == widget.OVERDUE_REMAIN_COLOR
    assert items["Оплачен"].foreground().color() == widget.PAID_ROW_COLOR

    widget.show_date(TODAY.addDays(3))
    assert table.item(0, 1).foreground().style() == Qt.BrushStyle.NoBrush


def test_selected_row_keeps_red_remain_color(models, qapp):
    add_event(models.path, total="100.00", due=day(-3), receiver="Просрочен")
    add_event(models.path, total="200.00", due=day(-3), receiver="Второй")
    reload(models)
    widget = make_widget(models)
    widget.show_date(TODAY.addDays(-3))
    table = widget.ui.tbl_events
    delegate = table.itemDelegate()

    for column, expected in ((1, widget.OVERDUE_REMAIN_COLOR), (0, QColor(table.palette().text().color()))):
        option = QStyleOptionViewItem()
        delegate.initStyleOption(option, table.model().index(0, column))
        assert option.palette.highlightedText().color() == expected


def test_day_list_is_beside_the_grid_and_has_no_cell_focus_frame(models, qapp):
    add_event(models.path, due=day(0))
    reload(models)
    widget = make_widget(models)
    table = widget.ui.tbl_events

    assert widget.ui.spl_calendar.orientation() == Qt.Orientation.Horizontal
    assert widget.ui.spl_calendar.widget(1) is widget.ui.wdg_day

    option = QStyleOptionViewItem()
    option.state |= QStyle.StateFlag.State_HasFocus
    table.itemDelegate().initStyleOption(option, table.model().index(0, 0))
    assert not option.state & QStyle.StateFlag.State_HasFocus


def test_widget_day_without_payments(models, qapp):
    add_event(models.path, due=day(0))
    reload(models)
    widget = make_widget(models)

    widget.show_date(TODAY.addMonths(-3))

    assert widget.ui.tbl_events.rowCount() == 0
    assert widget.ui.pb_undated.isHidden()
    assert widget.current_event_id is None


def test_widget_clicking_a_cell_changes_the_list(models, qapp):
    add_event(models.path, due=day(0))
    reload(models)
    widget = make_widget(models)
    other_date = QDate(TODAY.year(), TODAY.month(), 1) if TODAY.day() != 1 else QDate(TODAY.year(), TODAY.month(), 2)

    widget.ui.tv_calendar.setCurrentIndex(widget.model.index_of(other_date))

    assert widget.selected == other_date
    assert widget.ui.tbl_events.rowCount() == 0


def test_widget_month_navigation_keeps_day_and_today_button_returns(models, qapp):
    reload(models)
    widget = make_widget(models)
    widget.show_date(QDate(2026, 1, 31))

    widget.ui.tb_next.click()

    assert widget.model.month == QDate(2026, 2, 1)
    assert widget.selected == QDate(2026, 2, 28)
    assert widget.ui.pb_month.text() == "Февраль 2026"

    widget.ui.tb_prev.click()
    assert widget.model.month == QDate(2026, 1, 1) and widget.selected == QDate(2026, 1, 28)

    widget.ui.pb_today.click()
    assert widget.selected == TODAY and widget.model.month == QDate(TODAY.year(), TODAY.month(), 1)


def test_widget_clicking_a_day_of_another_month_switches_the_month(models, qapp):
    reload(models)
    widget = make_widget(models)
    widget.show_date(QDate(2026, 10, 15))

    widget.ui.tv_calendar.setCurrentIndex(widget.model.index_of(QDate(2026, 11, 1)))
    QTest.qWait(10)

    assert widget.model.month == QDate(2026, 11, 1)
    assert widget.selected == QDate(2026, 11, 1)
    assert widget.ui.pb_month.text() == "Ноябрь 2026"


def test_widget_first_payment_of_a_clicked_day_is_selected_and_reported(models, qapp):
    today_event = add_event(models.path, total="100.00", due=day(0))
    tomorrow_event = add_event(models.path, total="200.00", due=day(1))
    reload(models)
    widget = make_widget(models)
    reported: list[int] = []
    widget.eventSelected.connect(reported.append)

    widget.ui.tv_calendar.setCurrentIndex(widget.model.index_of(TODAY.addDays(1)))

    assert reported == [tomorrow_event]
    assert widget.current_event_id == tomorrow_event
    assert widget.ui.tbl_events.currentRow() == 0

    widget.ui.tv_calendar.setCurrentIndex(widget.model.index_of(TODAY))
    assert reported == [tomorrow_event, today_event]


def test_widget_choosing_a_row_reports_that_payment(models, qapp):
    add_event(models.path, total="100.00", due=day(0))
    add_event(models.path, total="200.00", due=day(0))
    reload(models)
    widget = make_widget(models)
    reported: list[int] = []
    widget.eventSelected.connect(reported.append)
    table = widget.ui.tbl_events
    other_row = 1 - table.currentRow()

    table.selectRow(other_row)

    assert reported == [table.item(other_row, 0).data(Qt.ItemDataRole.UserRole)]


def test_widget_select_event_moves_to_its_day_without_reporting(models, qapp):
    add_event(models.path, due=day(0))
    far = add_event(models.path, total="300.00", due=day(40))
    reload(models)
    widget = make_widget(models)
    reported: list[int] = []
    widget.eventSelected.connect(reported.append)

    widget.select_event(far)

    assert widget.selected == TODAY.addDays(40)
    assert widget.model.month == QDate(TODAY.addDays(40).year(), TODAY.addDays(40).month(), 1)
    assert widget.current_event_id == far
    assert widget.ui.tbl_events.currentRow() == 0
    assert reported == []


def test_widget_select_event_ignores_unknown_and_undated(models, qapp):
    add_event(models.path, due=day(0))
    undated = add_event(models.path, due="")
    reload(models)
    widget = make_widget(models)
    before = widget.selected

    widget.select_event(None)
    widget.select_event(undated)
    widget.select_event(999999)

    assert widget.selected == before


def test_widget_double_click_activates_day_with_single_payment(models, qapp):
    add_event(models.path, total="100.00", due=day(0))
    reload(models)
    widget = make_widget(models)
    activated: list[bool] = []
    widget.eventActivated.connect(lambda: activated.append(True))

    widget.open_day_event(widget.model.index_of(TODAY))

    assert activated == [True]


def test_widget_double_click_ignores_empty_or_busy_day(models, qapp):
    add_event(models.path, total="100.00", due=day(0))
    add_event(models.path, total="200.00", due=day(0))
    reload(models)
    widget = make_widget(models)
    activated: list[bool] = []
    widget.eventActivated.connect(lambda: activated.append(True))

    widget.open_day_event(widget.model.index_of(TODAY))
    widget.open_day_event(widget.model.index_of(TODAY.addDays(1)))

    assert activated == []


def test_widget_activating_the_list_row_reports_activation(models, qapp):
    add_event(models.path, due=day(0))
    reload(models)
    widget = make_widget(models)
    activated: list[bool] = []
    widget.eventActivated.connect(lambda: activated.append(True))

    widget.open_current_event()

    assert activated == [True]


def test_widget_activating_without_selection_does_nothing(models, qapp):
    reload(models)
    widget = make_widget(models)
    activated: list[bool] = []
    widget.eventActivated.connect(lambda: activated.append(True))

    widget.open_current_event()

    assert activated == []


def test_widget_hidden_postpones_reload_until_shown(models, qapp):
    reload(models)
    widget = make_widget(models)
    assert widget.ui.tbl_events.rowCount() == 0
    add_event(models.path, due=day(0))
    reload(models)

    widget.schedule_reload()

    assert widget.dirty and widget.ui.tbl_events.rowCount() == 0
    widget.show()
    assert not widget.dirty and widget.ui.tbl_events.rowCount() == 1
    widget.close()


def test_widget_visible_reloads_after_scheduled_change(models, qapp):
    reload(models)
    widget = make_widget(models)
    widget.show()
    add_event(models.path, due=day(0))
    reload(models)

    widget.schedule_reload()
    widget.schedule_reload()
    QTest.qWait(30)

    assert widget.ui.tbl_events.rowCount() == 1
    widget.close()


def test_widget_overdue_button_shows_summary_and_cycles_through_days(models, qapp):
    add_event(models.path, total="100.00", due=day(-5))
    add_event(models.path, total="200.00", due=day(-5))
    add_event(models.path, total="400.00", due=day(-1))
    reload(models)
    widget = make_widget(models)
    button = widget.ui.pb_overdue

    assert not button.isHidden()
    assert button.text() == "Просрочено: 3 на 700,00"

    button.click()
    assert widget.selected == TODAY.addDays(-5)
    button.click()
    assert widget.selected == TODAY.addDays(-1)
    button.click()
    assert widget.selected == TODAY.addDays(-5)


def test_widget_overdue_button_hidden_without_overdue_payments(models, qapp):
    add_event(models.path, due=day(3))
    reload(models)

    widget = make_widget(models)

    assert widget.ui.pb_overdue.isHidden()


def test_overdue_days_include_only_unpaid_past_payments(models):
    late = add_event(models.path, total="100.00", due=day(-3))
    partly = add_event(models.path, total="300.00", due=day(-3))
    add_payment(models.path, partly, day(-4), "100.00")
    paid = add_event(models.path, total="50.00", due=day(-2))
    add_payment(models.path, paid, day(-4), "50.00")
    add_event(models.path, total="70.00", due=day(2))
    reload(models)

    overdue = models.store.overdue_days()

    assert list(overdue) == [TODAY.addDays(-3)]
    assert set(overdue[TODAY.addDays(-3)].event_ids) == {late, partly}
    assert overdue[TODAY.addDays(-3)].remain == Decimal("300")


def test_overdue_days_follow_sidebar_filters(models):
    add_event(models.path, total="100.00", due=day(-3), receiver="Альфа")
    add_event(models.path, total="100.00", due=day(-1), receiver="Бета")
    reload(models)

    models.apply(search="бета")

    assert list(models.store.overdue_days()) == [TODAY.addDays(-1)]


def test_overdue_days_skip_payment_fully_paid_today(models):
    paid_today = add_event(models.path, total="100.00", due=day(-5))
    add_payment(models.path, paid_today, day(0), "100.00")
    late = add_event(models.path, total="200.00", due=day(-2))
    reload(models)

    overdue = models.store.overdue_days()

    assert list(overdue) == [TODAY.addDays(-2)]
    assert overdue[TODAY.addDays(-2)].event_ids == (late,)


def test_day_title_names_date_and_sums_up_day():
    date = QDate(2026, 10, 12)
    day_data = CalendarDay((1, 2), Decimal(10), Decimal(20), 1)

    assert day_title(date, None, None) == "12 октября 2026, Пн"
    text = day_title(date, day_data, DayStatus.OVERDUE)
    assert "платежей: 2" in text and "остаток: 10,00" in text


def test_undated_event_ids_lists_only_events_without_due_date(models):
    add_event(models.path, due=day(1))
    undated = add_event(models.path, due="")
    reload(models)

    assert models.store.undated_event_ids() == [undated]


def test_widget_shows_empty_hint_on_day_without_payments(models, qapp):
    add_event(models.path, due=day(1))
    reload(models)
    widget = make_widget(models)

    widget.show_date(TODAY)
    assert not widget.empty_label.isHidden()

    widget.show_date(TODAY.addDays(1))
    assert widget.empty_label.isHidden()
