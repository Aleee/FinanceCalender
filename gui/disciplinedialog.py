from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, QItemSelectionModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QDialog, QHeaderView, QListWidgetItem, QTableWidget, QTableWidgetItem, QVBoxLayout

from base.chart import DelayChartWidget, MonthTrendWidget
from base.date import MONTHS_RU
from base.debtcalculator import DebtRepository
from base.discipline import (BUCKET_NAMES, ClosedPayment, DelayBucket, DisciplineStats, OverduePayment, collect_stats,
                             filter_events, find_closed, find_overdue, total_stats)
from base.formatting import dec_strcommaspace, float_strcomma, float_strpercentage, int_strspace
from base.liability import CATEGORY_NAMES, LiabilityCategory, category_section
from base.xlswriter import DisciplineXlsWriter, ExportSheet
from gui.exportsuccessdialog import ExportSuccessDialog
from gui.filterwidget import CategoryFilterListWidget
from gui.manualdialog import add_help_shortcut
from gui.settings import SettingsHandler
from gui.ui.disciplinedialog_ui import Ui_DisciplineDialog


class NumberItem(QTableWidgetItem):

    def __init__(self, text: str, value: float | int) -> None:
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, value)
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return self.data(Qt.ItemDataRole.UserRole) < other.data(Qt.ItemDataRole.UserRole)


class DisciplineDialog(QDialog):

    STATS_HEADERS = [("Платежей", "Платежей"), ("Сумма", "Сумма"), ("Опозд.,\nшт.", "Опоздало, шт."),
                     ("Сумма\nопозд.", "Сумма опозданий"), ("В срок,\n% шт.", "В срок, % по кол-ву"),
                     ("Задержка\nсред., дн.", "Средняя задержка, дн."), ("Задержка\nмакс., дн.", "Максимальная задержка, дн.")]
    IN_TIME_HEADERS = {False: ("В срок,\n% шт.", "В срок, % по кол-ву"), True: ("В срок,\n% от суммы", "В срок, % по сумме")}
    STATS_FORMATS = [None, "#,##0", "#,##0.00", "#,##0", "#,##0.00", "0.0%", "0.0", "#,##0"]
    STATS_WIDTHS = [34, 11, 16, 11, 16, 10, 16, 14]
    IN_TIME_COLORS_HINT = "Цвет: от 90% - зеленый, 70-90% - желтый, 50-70% - оранжевый, меньше 50% - красный"
    IN_TIME_HINT = f"Доля платежей по количеству, оплаченных в срок или раньше.\n{IN_TIME_COLORS_HINT}"
    IN_TIME_AMOUNT_HINT = f"Доля суммы платежей, оплаченных в срок или раньше, от суммы всех оплаченных.\n{IN_TIME_COLORS_HINT}"
    AVERAGE_HINT = "Среднее только по опоздавшим платежам"
    HEADER_HINTS = {"В срок, % по кол-ву": IN_TIME_HINT, "В срок, % по сумме": IN_TIME_AMOUNT_HINT, "Средняя задержка, дн.": AVERAGE_HINT}
    PERIOD_HINT = ("Учитываются только полностью оплаченные платежи. Срок оплаты сравнивается с датой последней оплаты, "
                   "по ней же отбираются платежи за период")
    CATEGORIES_HINT = "Если ничего не выбрано - учитываются все категории"
    OVERDUE_HINT = ("Состояние на сегодня, период отчета не учитывается. Фильтры по категориям и получателю действуют")
    BUCKET_HINT = "Щелчок по столбцу графика фильтрует таблицы по задержке, повторный щелчок снимает фильтр"
    CLOSED_HEADERS = [("Получатель", "Получатель"), ("Платеж", "Платеж"), ("Категория", "Категория"),
                      ("Срок оплаты", "Срок оплаты"), ("Оплачен", "Дата последней оплаты"), ("Сумма", "Сумма"),
                      ("Задержка,\nдн.", "Задержка, дн.")]
    CLOSED_FORMATS = [None, None, None, "date", "date", "#,##0.00", "#,##0"]
    CLOSED_WIDTHS = [30, 40, 36, 13, 13, 15, 10]
    OVERDUE_HEADERS = [("Получатель", "Получатель"), ("Платеж", "Платеж"), ("Категория", "Категория"),
                       ("Срок оплаты", "Срок оплаты"), ("Остаток", "Остаток"), ("Дн. просрочки", "Дней просрочки")]
    OVERDUE_FORMATS = [None, None, None, "date", "#,##0.00", "#,##0"]
    OVERDUE_WIDTHS = [30, 40, 36, 13, 15, 12]
    GROUP_CATEGORY = LiabilityCategory.TOP_CURRENT
    GROUP_NAME = "Текущая деятельность (все)"
    CHART_SIZES = [260, 400]
    SCREEN_MARGIN = 40

    def __init__(self, start_date: QDate, end_date: QDate, parent: QDialog | None = None,
                 settings_handler: SettingsHandler | None = None) -> None:
        super(DisciplineDialog, self).__init__(parent)
        self.ui = Ui_DisciplineDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "12-planfact.html")

        self.settings_handler: SettingsHandler | None = settings_handler
        self.events = DebtRepository().load()
        self.bucket: DelayBucket | None = None
        self.total: DisciplineStats = DisciplineStats()
        self.overdue: list[OverduePayment] = []
        self.overdue_remain: Decimal = Decimal(0)
        self.group_item: QListWidgetItem | None = None
        self.group_children: list[QListWidgetItem] = []
        self.group_was_selected: bool = False

        self.start_date: QDate = start_date
        self.end_date: QDate = end_date
        self.ui.label_period.setText(f"Период: {start_date.toString('dd.MM.yyyy')} - {end_date.toString('dd.MM.yyyy')}")
        self.ui.label_period.setToolTip(self.PERIOD_HINT)
        self.ui.lw_categories.setToolTip(self.CATEGORIES_HINT)
        self.ui.lb_bucket.setToolTip(self.BUCKET_HINT)
        self.ui.lb_overdue.setToolTip(self.OVERDUE_HINT)
        self.fill_categories()
        self.keep_selection_color()
        self.setup_kpi_tiles()
        self.setup_charts()
        self.setup_tables()
        self.ui.pb_export.setEnabled(settings_handler is not None)
        self.ui.spl_report.setStretchFactor(0, 0)
        self.ui.spl_report.setStretchFactor(1, 1)
        self.ui.spl_report.setSizes(self.CHART_SIZES)
        self.fit_to_screen()
        self.clear_category_cursor()

        self.rebuild()

        self.ui.lw_categories.itemSelectionChanged.connect(self.on_categories_changed)
        self.ui.le_receiver.textChanged.connect(self.rebuild)
        self.ui.rb_amount.toggled.connect(self.rebuild)
        self.ui.pb_reset.clicked.connect(self.reset_filters)
        self.ui.pb_export.clicked.connect(self.export_to_excel)
        self.chart.bucketClicked.connect(self.on_bucket_clicked)

    def fill_categories(self) -> None:
        group_section = category_section(self.GROUP_CATEGORY)
        for category, full_name in CATEGORY_NAMES.items():
            is_group = category == self.GROUP_CATEGORY
            short_name = self.GROUP_NAME if is_group else CategoryFilterListWidget.ITEMS[category][0]
            new_item = QListWidgetItem(short_name)
            new_item.setData(Qt.ItemDataRole.UserRole, int(category))
            new_item.setToolTip(" ".join(full_name.split()))
            self.ui.lw_categories.addItem(new_item)
            if is_group:
                self.group_item = new_item
                bold_font = QFont(new_item.font())
                bold_font.setBold(True)
                new_item.setFont(bold_font)
            elif category_section(category) == group_section:
                self.group_children.append(new_item)

    def keep_selection_color(self) -> None:
        palette = self.ui.lw_categories.palette()
        background = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight).name()
        text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText).name()
        self.ui.lw_categories.setStyleSheet(f"QListWidget::item:selected {{background: {background}; color: {text};}}")

    def setup_kpi_tiles(self) -> None:
        for number in range(1, 5):
            frame = getattr(self.ui, f"fr_kpi{number}")
            frame.setStyleSheet(f"QFrame#{frame.objectName()} {{background: palette(base); border: 1px solid #c8c8c8; "
                                f"border-radius: 4px;}}")
            getattr(self.ui, f"lb_kpi{number}_caption").setStyleSheet("color: #555555;")

    def setup_charts(self) -> None:
        background = self.palette().color(QPalette.ColorRole.Window)
        chart_layout = QVBoxLayout()
        self.ui.wdg_chart.setLayout(chart_layout)
        self.chart = DelayChartWidget(background)
        chart_layout.addWidget(self.chart)

        trend_layout = QVBoxLayout()
        trend_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.wdg_trend.setLayout(trend_layout)
        self.trend = MonthTrendWidget(background)
        trend_layout.addWidget(self.trend)

    def setup_tables(self) -> None:
        for table in (self.ui.tbl_receivers, self.ui.tbl_categories, self.ui.tbl_months, self.ui.tbl_closed, self.ui.tbl_overdue):
            table.setWordWrap(False)

    def fit_to_screen(self) -> None:
        screen = self.screen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.resize(min(self.width(), available.width() - self.SCREEN_MARGIN),
                    min(self.height(), available.height() - self.SCREEN_MARGIN))

    def on_categories_changed(self) -> None:
        group_selected = self.group_item.isSelected()
        self.ui.lw_categories.blockSignals(True)
        if group_selected != self.group_was_selected:
            for child in self.group_children:
                child.setSelected(group_selected)
        else:
            group_selected = all(child.isSelected() for child in self.group_children)
            self.group_item.setSelected(group_selected)
        self.ui.lw_categories.blockSignals(False)
        self.group_was_selected = group_selected
        self.clear_category_cursor()
        self.rebuild()

    def clear_category_cursor(self) -> None:
        if not self.ui.lw_categories.selectedItems():
            self.ui.lw_categories.selectionModel().setCurrentIndex(QModelIndex(), QItemSelectionModel.SelectionFlag.NoUpdate)

    def reset_filters(self) -> None:
        self.ui.le_receiver.blockSignals(True)
        self.ui.lw_categories.blockSignals(True)
        self.ui.le_receiver.clear()
        self.ui.lw_categories.clearSelection()
        self.ui.le_receiver.blockSignals(False)
        self.ui.lw_categories.blockSignals(False)
        self.group_was_selected = False
        self.bucket = None
        self.clear_category_cursor()
        self.rebuild()

    def on_bucket_clicked(self, index: int) -> None:
        if index == DelayChartWidget.OVERDUE_INDEX:
            self.ui.tw_report.setCurrentWidget(self.ui.tab_overdue)
            return
        bucket = DelayBucket(index)
        self.bucket = None if self.bucket == bucket else bucket
        self.rebuild()

    def rebuild(self) -> None:
        categories = {item.data(Qt.ItemDataRole.UserRole) for item in self.ui.lw_categories.selectedItems()}
        receiver = self.ui.le_receiver.text()
        events = filter_events(self.events, categories, receiver)
        closed = find_closed(events, self.start_date.toPython(), self.end_date.toPython())
        self.overdue = find_overdue(events, date.today())
        self.overdue_remain = sum((item.remain for item in self.overdue), Decimal(0))
        self.total = total_stats(closed)
        if self.bucket is not None and not self.total.buckets[self.bucket]:
            self.bucket = None
        shown = closed if self.bucket is None else [item for item in closed if item.bucket == self.bucket]

        self.fill_kpi_tiles()
        self.ui.lb_bucket.setText(self.bucket_text())
        self.update_chart()

        by_receiver = collect_stats(shown, lambda item: item.event.receiver)
        self.fill_stats_table(self.ui.tbl_receivers, "Получатель",
                              [(QTableWidgetItem(key or "(не указан)"), stats) for key, stats in by_receiver.items()], 4)

        by_category = collect_stats(shown, lambda item: item.event.category)
        self.fill_stats_table(self.ui.tbl_categories, "Категория",
                              [(NumberItem(CATEGORY_NAMES.get(key, "Без категории"), key), stats) for key, stats in by_category.items()], 0,
                              Qt.SortOrder.AscendingOrder)

        by_month = collect_stats(shown, lambda item: (item.paid_date.year, item.paid_date.month))
        self.fill_stats_table(self.ui.tbl_months, "Месяц оплаты",
                              [(NumberItem(f"{MONTHS_RU[month - 1]} {year}", year * 12 + month), stats) for (year, month), stats in by_month.items()], 0,
                              Qt.SortOrder.AscendingOrder)
        self.trend.setMonths([(year * 12 + month, f"{MONTHS_RU[month - 1][:3]} {year % 100:02d}", self.in_time_share(stats))
                              for (year, month), stats in sorted(by_month.items())])

        self.fill_closed_table(shown)
        self.fill_overdue_table(self.overdue)

    def in_time_share(self, stats: DisciplineStats) -> float:
        return float(stats.in_time_amount_share if self.ui.rb_amount.isChecked() else stats.in_time_share)

    def fill_kpi_tiles(self) -> None:
        total = self.total
        if total.count:
            average = float_strcomma(total.average_late_delay)
            tiles = [
                (float_strpercentage(self.in_time_share(total)), self.in_time_caption(total)),
                (f"{int_strspace(total.late_count)} из {int_strspace(total.count)}",
                 f"Опоздало ({float_strpercentage(float(total.late_count_share))}), в среднем на {average} дн., "
                 f"максимум на {total.max_delay} дн."),
                (dec_strcommaspace(total.late_amount, add_rub=True),
                 f"Сумма опозданий ({float_strpercentage(float(total.late_amount_share))} от оплаченной суммы)"),
            ]
        else:
            tiles = [("-", "Оплачено в срок или раньше"), ("-", "Опоздало"), ("-", "Сумма опозданий")]
        tiles.append((int_strspace(len(self.overdue)),
                      f"Неоплаченных просроченных на {dec_strcommaspace(self.overdue_remain, add_rub=True)}"))
        for number, (value, caption) in enumerate(tiles, start=1):
            getattr(self.ui, f"lb_kpi{number}_value").setText(value)
            getattr(self.ui, f"lb_kpi{number}_caption").setText(caption)

    def in_time_caption(self, total: DisciplineStats) -> str:
        if self.ui.rb_amount.isChecked():
            in_time_amount = dec_strcommaspace(total.bucket_amounts[DelayBucket.IN_TIME])
            return f"Оплачено в срок или раньше: {in_time_amount} из {dec_strcommaspace(total.amount, add_rub=True)}"
        return f"Оплачено в срок или раньше: {int_strspace(total.buckets[DelayBucket.IN_TIME])} из {int_strspace(total.count)}"

    def update_chart(self) -> None:
        self.chart.setStats(self.total, len(self.overdue), self.overdue_remain, self.ui.rb_amount.isChecked(), self.bucket)

    def bucket_text(self) -> str:
        return "" if self.bucket is None else f"Фильтр по задержке: «{BUCKET_NAMES[self.bucket]}»"

    @staticmethod
    def share_color(share: float) -> QColor:
        if share >= 0.9:
            return DelayChartWidget.tint(DelayBucket.IN_TIME)
        if share >= 0.7:
            return DelayChartWidget.tint(DelayBucket.WEEK)
        if share >= 0.5:
            return DelayChartWidget.tint(DelayBucket.MONTH)
        return DelayChartWidget.tint(DelayBucket.LONG)

    def fill_stats_table(self, table: QTableWidget, first_header: str, rows: list[tuple[QTableWidgetItem, DisciplineStats]],
                         sort_column: int, sort_order: Qt.SortOrder = Qt.SortOrder.DescendingOrder) -> None:
        table.setSortingEnabled(False)
        headers = [(first_header, first_header)] + self.STATS_HEADERS
        headers[5] = self.IN_TIME_HEADERS[self.ui.rb_amount.isChecked()]
        self.set_headers(table, headers)
        table.setRowCount(len(rows))
        for row, (label, stats) in enumerate(rows):
            in_time_share = self.in_time_share(stats)
            average_text = float_strcomma(stats.average_late_delay) if stats.late_count else "—"
            values = [
                (int_strspace(stats.count), stats.count),
                (dec_strcommaspace(stats.amount), stats.amount),
                (int_strspace(stats.late_count), stats.late_count),
                (dec_strcommaspace(stats.late_amount), stats.late_amount),
                (float_strpercentage(in_time_share), in_time_share),
                (average_text, stats.average_late_delay),
                (int_strspace(stats.max_delay), stats.max_delay),
            ]
            label.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, label)
            for column, (text, value) in enumerate(values, start=1):
                number_item = NumberItem(text, value)
                if column == 5:
                    number_item.setBackground(self.share_color(in_time_share))
                    number_item.setForeground(QColor(DelayChartWidget.TEXT_COLOR))
                table.setItem(row, column, number_item)
        table.setSortingEnabled(True)
        table.sortByColumn(sort_column, sort_order)
        self.adjust_columns(table)

    def set_headers(self, table: QTableWidget, headers: list[tuple[str, str]]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels([short_name for short_name, _ in headers])
        for column, (short_name, full_name) in enumerate(headers):
            header_item = table.horizontalHeaderItem(column)
            header_item.setData(Qt.ItemDataRole.UserRole, full_name)
            if full_name in self.HEADER_HINTS:
                header_item.setToolTip(f"{full_name}\n{self.HEADER_HINTS[full_name]}")
            elif short_name.replace("\n", " ") != full_name:
                header_item.setToolTip(full_name)

    @staticmethod
    def fill_event_columns(table: QTableWidget, row: int, event) -> None:
        for column, text in ((0, event.receiver), (1, event.name)):
            text_item = QTableWidgetItem(text)
            text_item.setToolTip(text)
            table.setItem(row, column, text_item)
        category_item = NumberItem(CATEGORY_NAMES.get(event.category, "Без категории"), event.category)
        category_item.setToolTip(category_item.text())
        category_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, 2, category_item)
        table.setItem(row, 3, NumberItem(f"{event.due:%d.%m.%Y}", event.due.toordinal()))

    def fill_closed_table(self, closed: list[ClosedPayment]) -> None:
        table = self.ui.tbl_closed
        table.setSortingEnabled(False)
        self.set_headers(table, self.CLOSED_HEADERS)
        table.setRowCount(len(closed))
        for row, item in enumerate(closed):
            self.fill_event_columns(table, row, item.event)
            table.setItem(row, 4, NumberItem(f"{item.paid_date:%d.%m.%Y}", item.paid_date.toordinal()))
            table.setItem(row, 5, NumberItem(dec_strcommaspace(item.event.amount), item.event.amount))
            delay_item = NumberItem(int_strspace(item.delay), item.delay)
            delay_item.setBackground(DelayChartWidget.tint(item.bucket))
            delay_item.setForeground(QColor(DelayChartWidget.TEXT_COLOR))
            table.setItem(row, 6, delay_item)
        table.setSortingEnabled(True)
        table.sortByColumn(6, Qt.SortOrder.DescendingOrder)
        self.adjust_columns(table, (0, 1, 2))
        self.ui.tw_report.setTabText(self.ui.tw_report.indexOf(self.ui.tab_closed), f"Оплаченные платежи ({len(closed)})")

    def fill_overdue_table(self, overdue: list[OverduePayment]) -> None:
        table = self.ui.tbl_overdue
        table.setSortingEnabled(False)
        self.set_headers(table, self.OVERDUE_HEADERS)
        table.setRowCount(len(overdue))
        for row, item in enumerate(overdue):
            self.fill_event_columns(table, row, item.event)
            table.setItem(row, 4, NumberItem(dec_strcommaspace(item.remain), item.remain))
            table.setItem(row, 5, NumberItem(int_strspace(item.days), item.days))
        table.setSortingEnabled(True)
        table.sortByColumn(5, Qt.SortOrder.DescendingOrder)
        self.adjust_columns(table, (0, 1, 2))

        self.ui.tw_report.setTabText(self.ui.tw_report.indexOf(self.ui.tab_overdue), f"Неоплаченные просроченные ({len(overdue)})")
        self.ui.lb_overdue.setText(f"Всего: <b>{len(overdue)}</b>, остаток: <b>{dec_strcommaspace(self.overdue_remain, add_rub=True)}</b>")

    @staticmethod
    def adjust_columns(table: QTableWidget, stretch_columns: tuple[int, ...] = (0,)) -> None:
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.resizeColumnsToContents()
        for column in stretch_columns:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)

    def export_to_excel(self) -> None:
        writer = DisciplineXlsWriter(self.settings_handler)
        if writer.write(self.report_sheets(), self.start_date, self.end_date, self):
            ExportSuccessDialog(writer.last_path, self).exec()

    def report_sheets(self) -> list[ExportSheet]:
        return [
            self.summary_sheet(),
            self.distribution_sheet(),
            self.table_sheet("По получателям", self.ui.tbl_receivers, self.STATS_FORMATS, self.STATS_WIDTHS),
            self.table_sheet("По категориям", self.ui.tbl_categories, self.STATS_FORMATS, self.STATS_WIDTHS),
            self.table_sheet("По месяцам", self.ui.tbl_months, self.STATS_FORMATS, self.STATS_WIDTHS),
            self.table_sheet("Оплаченные платежи", self.ui.tbl_closed, self.CLOSED_FORMATS, self.CLOSED_WIDTHS),
            self.table_sheet("Неоплаченные просроченные", self.ui.tbl_overdue, self.OVERDUE_FORMATS, self.OVERDUE_WIDTHS),
        ]

    def summary_sheet(self) -> ExportSheet:
        total = self.total
        start_date, end_date = self.start_date, self.end_date
        categories = [item.text() for item in self.ui.lw_categories.selectedItems()]
        rows = [
            ["Период (по дате последней оплаты)", f"{start_date.toString('dd.MM.yyyy')} - {end_date.toString('dd.MM.yyyy')}"],
            ["Категории", ", ".join(categories) or "Все"],
            ["Получатель (часть названия)", self.ui.le_receiver.text().strip() or "Любой"],
            ["Фильтр таблиц по задержке", BUCKET_NAMES[self.bucket] if self.bucket is not None else "Нет"],
        ]
        if total.count:
            rows += [
                ["Полностью оплачено", f"{int_strspace(total.count)} на {dec_strcommaspace(total.amount, add_rub=True)}"],
                ["В срок или раньше", f"{float_strpercentage(float(total.in_time_share))} по количеству "
                                      f"({int_strspace(total.buckets[DelayBucket.IN_TIME])} шт.), "
                                      f"{float_strpercentage(float(total.in_time_amount_share))} по сумме"],
                ["Опоздало", f"{int_strspace(total.late_count)} шт. ({float_strpercentage(float(total.late_count_share))}) "
                             f"на {dec_strcommaspace(total.late_amount, add_rub=True)} "
                             f"({float_strpercentage(float(total.late_amount_share))} от суммы)"],
                ["Средняя задержка опоздавших, дн.", float_strcomma(total.average_late_delay)],
                ["Максимальная задержка, дн.", str(total.max_delay)],
            ]
        else:
            rows.append(["Полностью оплачено", "нет платежей"])
        rows.append(["Неоплаченных просроченных (на сегодня)",
                     f"{int_strspace(len(self.overdue))} на {dec_strcommaspace(self.overdue_remain, add_rub=True)}"])
        return ExportSheet("Сводка", ["Показатель", "Значение"], rows, [None, None], [44, 90])

    def distribution_sheet(self) -> ExportSheet:
        total = self.total
        rows = [[BUCKET_NAMES[bucket], total.buckets[bucket],
                 total.buckets[bucket] / total.count if total.count else None,
                 total.bucket_amounts[bucket],
                 total.bucket_amounts[bucket] / total.amount if total.amount else None] for bucket in DelayBucket]
        rows.append([DelayChartWidget.COLUMN_NAMES[DelayChartWidget.OVERDUE_INDEX], len(self.overdue), None, self.overdue_remain, None])
        return ExportSheet("Распределение", ["Задержка оплаты", "Платежей", "Доля по\nколичеству", "Сумма", "Доля по\nсумме"], rows,
                           [None, "#,##0", "0.0%", "#,##0.00", "0.0%"], [30, 12, 14, 16, 14])

    @staticmethod
    def table_sheet(name: str, table: QTableWidget, formats: list[str | None], widths: list[float]) -> ExportSheet:
        headers = [table.horizontalHeaderItem(column).data(Qt.ItemDataRole.UserRole) for column in range(table.columnCount())]
        rows = []
        for row in range(table.rowCount()):
            values = []
            for column, number_format in enumerate(formats):
                item = table.item(row, column)
                if number_format is None:
                    values.append(item.text())
                elif number_format == "date":
                    values.append(date.fromordinal(item.data(Qt.ItemDataRole.UserRole)))
                else:
                    values.append(item.data(Qt.ItemDataRole.UserRole))
            rows.append(values)
        return ExportSheet(name, headers, rows, formats, widths)
