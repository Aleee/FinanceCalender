import zipfile
from datetime import date
from decimal import Decimal

from PySide6.QtGui import QColor

from base.chart import DelayChartWidget, MonthTrendWidget, WholeNumberAxis
from base.discipline import DelayBucket, DisciplineStats, ClosedPayment
from base.debtcalculator import Event, Payment
from base.xlswriter import DisciplineXlsWriter, ExportSheet
from tests.conftest import FakeSettingsHandler


def make_stats(*delays: int) -> DisciplineStats:
    stats = DisciplineStats()
    for number, delay in enumerate(delays):
        due = date(2026, 10, 10)
        event = Event(number, 1101, Decimal(100), date(2026, 10, 1), due, [], "", "r")
        stats.add(ClosedPayment(event, date.fromordinal(due.toordinal() + delay)))
    return stats


def test_axis_keeps_only_whole_ticks(qapp):
    axis = WholeNumberAxis(orientation="left")
    levels = axis.tickValues(0, 3, 300)
    assert levels
    assert all(spacing >= 1 for spacing, _ in levels)
    assert all(float(value).is_integer() for _, values in levels for value in values)


def test_column_at_ignores_empty_columns_and_gaps(qapp):
    chart = DelayChartWidget(QColor("white"))
    chart.setStats(make_stats(0, 0, 5), overdue_count=2)

    assert chart.columnAt(0.2) == 0
    assert chart.columnAt(1.0) == 1
    assert chart.columnAt(2.0) is None
    assert chart.columnAt(4.0) == 4
    assert chart.columnAt(5.2) is None
    assert chart.columnAt(-1.0) is None


def test_chart_switches_axis_label_between_count_and_amount(qapp):
    chart = DelayChartWidget(QColor("white"))
    stats = make_stats(0, 5)

    chart.setStats(stats)
    assert chart.plot.getAxis("left").labelText == "Кол-во платежей"
    assert chart.heights == [1, 1, 0, 0, 0]

    chart.setStats(stats, by_amount=True)
    assert chart.plot.getAxis("left").labelText == "Сумма, руб."
    assert chart.heights == [100, 100, 0, 0, 0]


def test_chart_shows_overdue_as_fifth_column(qapp):
    chart = DelayChartWidget(QColor("white"))
    chart.setStats(make_stats(0), overdue_count=3, overdue_amount=Decimal(250), by_amount=True)

    assert chart.heights[DelayChartWidget.OVERDUE_INDEX] == 250
    assert "3 шт." in chart.hints[DelayChartWidget.OVERDUE_INDEX]


def test_empty_chart_has_no_columns(qapp):
    chart = DelayChartWidget(QColor("white"))
    chart.setStats(DisciplineStats())

    assert chart.heights == []
    assert chart.columnAt(0.0) is None


def test_chart_with_only_overdue_is_not_empty(qapp):
    chart = DelayChartWidget(QColor("white"))
    chart.setStats(DisciplineStats(), overdue_count=2)

    assert chart.heights == [0, 0, 0, 0, 2]


def test_chart_tint_is_translucent(qapp):
    assert DelayChartWidget.tint(DelayBucket.IN_TIME).alpha() == DelayChartWidget.TINT_ALPHA


def test_trend_accepts_gaps_and_empty_list(qapp):
    trend = MonthTrendWidget(QColor("white"))
    trend.setMonths([(24324, "Дек 26", 1.0), (24326, "Фев 27", 0.5)])
    trend.setMonths([])


def test_discipline_writer_writes_sheet_per_tab(tmp_path, qapp):
    sheets = [
        ExportSheet("Первый", ["Название", "Дата", "Сумма"], [["=1+1", date(2026, 10, 5), Decimal("10.5")]],
                    [None, "date", "#,##0.00"], [20, 12, 12]),
        ExportSheet("Второй", ["Пусто"], [], [None], [10]),
    ]
    path = tmp_path / "out.xlsx"

    DisciplineXlsWriter(FakeSettingsHandler(tmp_path / "settings.ini")).write_workbook(sheets, str(path))

    with zipfile.ZipFile(path) as archive:
        workbook = archive.read("xl/workbook.xml").decode("utf-8")
        strings = archive.read("xl/sharedStrings.xml").decode("utf-8")
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "Первый" in workbook and "Второй" in workbook
    assert "=1+1" in strings
    assert "<f>" not in sheet
    assert "<v>10.5</v>" in sheet
