from decimal import Decimal
from typing import Callable

from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QDateEdit, QDialog, QHeaderView, QListWidgetItem, QSizePolicy, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from base.chart import ExpenseBarWidget, ExpenseMonthsWidget
from base.date import MONTHS_RU
from base.expenses import (ExpensePayment, ExpenseRepository, ExpenseStats, StructureRow, build_structure, change_share,
                           collect_stats, filter_payments, in_period, month_index, month_range, monthly_average,
                           peak_month, previous_period, rank_categories, share_of, stack_months, total_stats)
from base.formatting import dec_strcommaspace, float_strpercentage, float_strsignedpercentage, int_strspace
from base.liability import CATEGORY_NAMES, LiabilityCategory, category_section
from base.xlswriter import ExpensesXlsWriter, ExportSheet
from gui.disciplinedialog import DisciplineDialog, NumberItem
from gui.exportsuccessdialog import ExportSuccessDialog
from gui.filterwidget import CategoryFilterListWidget
from gui.manualdialog import add_help_shortcut
from gui.settings import SettingsHandler
from gui.ui.expensesdialog_ui import Ui_ExpensesDialog


class ChangeItem(NumberItem):

    def __lt__(self, other: QTableWidgetItem) -> bool:
        mine, theirs = self.data(Qt.ItemDataRole.UserRole), other.data(Qt.ItemDataRole.UserRole)
        return (mine is not None, mine or 0) < (theirs is not None, theirs or 0)


class CategoryItem(QTableWidgetItem):

    def __lt__(self, other: QTableWidgetItem) -> bool:
        def sort_key(item: QTableWidgetItem) -> tuple[bool, int]:
            category = item.data(Qt.ItemDataRole.UserRole)
            return category not in CATEGORY_NAMES, category
        return sort_key(self) < sort_key(other)


class ExpensesDialog(QDialog):

    STATS_HEADERS = [("Платежей", "Платежей"), ("Возвраты", "Возвраты"), ("Сумма", "Сумма"), ("Доля", "Доля от всех расходов")]
    COMPARE_HEADERS = [("Пред. период", "Предыдущий период"), ("Изменение", "Изменение к предыдущему периоду")]
    STATS_FORMATS = [None, "#,##0", "#,##0.00", "#,##0.00", "0.0%", "#,##0.00", "0.0%"]
    STATS_WIDTHS = [40, 11, 14, 16, 10, 16, 12]
    PAYMENT_HEADERS = [("Дата", "Дата оплаты"), ("Получатель", "Получатель"), ("Платеж", "Платеж"),
                       ("Категория", "Категория"), ("Сумма", "Сумма")]
    PAYMENT_FORMATS = ["date", None, None, None, "#,##0.00"]
    PAYMENT_WIDTHS = [13, 30, 40, 36, 15]
    PERIOD_NOTE = "Оплаты по дате оплаты, возвраты вычитаются из сумм своих категорий"
    CATEGORIES_HINT = "Если ничего не выбрано - учитываются все категории"
    PAYMENTS_HINT = "Двойной щелчок по строке открывает платеж"
    OTHER_NAME = "Прочее"
    REST_NAME = "Остальные категории"
    ALL_NAME = "Все расходы"
    MERGE_BELOW = Decimal("0.02")
    TOP_COLORS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7")
    TOTAL_COLOR = "#4f6d8f"
    STACK_LIMIT = 4
    MUTED_STYLE = "color: #555555;"
    SECTION_HEADERS = {LiabilityCategory.TOP_CURRENT: "Текущая деятельность", LiabilityCategory.TOP_FINANCES: "Финансы и инвестиции"}
    SCREEN_MARGIN = 40
    CHART_SIZES = [420, 300]
    MONTHS_SIZES = [650, 450]
    RECEIVER_DELAY = 250
    REVEAL_MARGIN = 40
    KPI_CAPTION_LINES = 2
    SORT_ARROW_PADDING = 36

    def __init__(self, start_date: QDate, end_date: QDate, parent: QDialog | None = None,
                 settings_handler: SettingsHandler | None = None,
                 open_event: Callable[[int, QWidget], bool] | None = None) -> None:
        super(ExpensesDialog, self).__init__(parent)
        self.ui = Ui_ExpensesDialog()
        self.ui.setupUi(self)
        add_help_shortcut(self, "12-planfact.html")

        self.settings_handler: SettingsHandler | None = settings_handler
        self.open_event: Callable[[int, QWidget], bool] | None = open_event
        self.start_date: QDate = start_date
        self.end_date: QDate = end_date
        self.start, self.end = start_date.toPython(), end_date.toPython()
        self.previous_start, self.previous_end = previous_period(self.start, self.end)
        self.payments: list[ExpensePayment] = []
        self.top_categories: list[int] = []
        self.load_payments()
        self.rows: list[StructureRow] = []
        self.focus: tuple[int, ...] | None = None
        self.total: ExpenseStats = ExpenseStats()
        self.change_text: str = "-"
        self.shown: list[ExpensePayment] = []
        self.receiver_timer = QTimer(self)
        self.receiver_timer.setSingleShot(True)
        self.receiver_timer.setInterval(self.RECEIVER_DELAY)

        self.ui.label_period.setText(f"Период: {start_date.toString('dd.MM.yyyy')} - {end_date.toString('dd.MM.yyyy')}")
        self.ui.label_period.setToolTip(self.PERIOD_NOTE)
        self.ui.lw_categories.setToolTip(self.CATEGORIES_HINT)
        self.ui.cb_merge_small.setToolTip(f"Категории с долей меньше {float_strpercentage(float(self.MERGE_BELOW))} "
                                          f"объединяются в один столбец «{self.OTHER_NAME}»")
        for date_edit, day in ((self.ui.de_prev_start, self.previous_start), (self.ui.de_prev_end, self.previous_end)):
            date_edit.setDate(QDate(day.year, day.month, day.day))
        self.fill_categories()
        self.keep_selection_color()
        self.setup_kpi_tiles()
        self.setup_charts()
        for table in (self.ui.tbl_categories, self.ui.tbl_receivers, self.ui.tbl_months, self.ui.tbl_payments):
            table.setWordWrap(False)
        if open_event is not None:
            self.ui.tw_report.setTabToolTip(self.ui.tw_report.indexOf(self.ui.tab_payments), self.PAYMENTS_HINT)
        self.ui.pb_export.setEnabled(settings_handler is not None)
        self.ui.tw_report.setTabVisible(self.ui.tw_report.indexOf(self.ui.tab_categories), False)
        self.ui.tw_report.setCurrentWidget(self.ui.tab_receivers)
        self.ui.spl_report.setStretchFactor(0, 0)
        self.ui.spl_report.setStretchFactor(1, 1)
        self.ui.spl_report.setSizes(self.CHART_SIZES)
        self.ui.spl_months.setSizes(self.MONTHS_SIZES)
        self.fit_to_screen()

        self.rebuild()

        self.ui.lw_categories.itemSelectionChanged.connect(self.rebuild)
        self.ui.le_receiver.textChanged.connect(self.receiver_timer.start)
        self.receiver_timer.timeout.connect(self.rebuild)
        for check_box in (self.ui.cb_skip_finance, self.ui.cb_skip_investment, self.ui.cb_merge_small, self.ui.cb_compare):
            check_box.toggled.connect(self.rebuild)
        self.ui.cb_compare.toggled.connect(self.ui.de_prev_start.setEnabled)
        self.ui.cb_compare.toggled.connect(self.ui.de_prev_end.setEnabled)
        self.ui.de_prev_start.dateChanged.connect(self.on_previous_start_changed)
        self.ui.de_prev_end.dateChanged.connect(self.on_previous_end_changed)
        self.ui.pb_reset.clicked.connect(self.reset_filters)
        self.ui.pb_export.clicked.connect(self.export_to_excel)
        self.chart.rowClicked.connect(self.on_row_clicked)
        self.chart.rowRevealed.connect(self.reveal_chart_row)
        self.ui.tbl_payments.cellDoubleClicked.connect(self.on_payment_activated)

    def load_payments(self) -> None:
        self.payments = ExpenseRepository().load(min(self.previous_start, self.start), max(self.previous_end, self.end))
        self.top_categories = rank_categories(in_period(self.payments, self.start, self.end), len(self.TOP_COLORS))

    @staticmethod
    def category_label(category: int) -> str:
        return CategoryFilterListWidget.ITEMS[category][0] if category in CategoryFilterListWidget.ITEMS else "Без категории"

    def row_label(self, row: StructureRow) -> str:
        if len(row.categories) > 1:
            return f"{self.OTHER_NAME} ({len(row.categories)})"
        return self.category_label(row.categories[0])

    def row_color(self, row: StructureRow) -> str:
        if len(row.categories) == 1 and row.categories[0] in self.top_categories:
            return self.TOP_COLORS[self.top_categories.index(row.categories[0])]
        return ExpenseBarWidget.OTHER_COLOR

    def row_details(self, row: StructureRow) -> str:
        if len(row.categories) < 2:
            return ""
        return "Входят:\n" + "\n".join(f"• {self.category_label(category)}" for category in row.categories)

    def fill_categories(self) -> None:
        for category, full_name in CATEGORY_NAMES.items():
            if category in self.SECTION_HEADERS:
                header_item = QListWidgetItem(self.SECTION_HEADERS[category])
                header_item.setFlags(Qt.ItemFlag.NoItemFlags)
                font = header_item.font()
                font.setBold(True)
                header_item.setFont(font)
                header_item.setForeground(self.palette().color(QPalette.ColorRole.WindowText))
                self.ui.lw_categories.addItem(header_item)
            if category == LiabilityCategory.TOP_CURRENT:
                continue
            new_item = QListWidgetItem(self.category_label(category))
            new_item.setData(Qt.ItemDataRole.UserRole, int(category))
            new_item.setToolTip(" ".join(full_name.split()))
            self.ui.lw_categories.addItem(new_item)

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
            value_label = getattr(self.ui, f"lb_kpi{number}_value")
            value_label.setWordWrap(False)
            value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            caption_label = getattr(self.ui, f"lb_kpi{number}_caption")
            caption_label.setStyleSheet(self.MUTED_STYLE)
            caption_label.setMinimumHeight(caption_label.fontMetrics().lineSpacing() * self.KPI_CAPTION_LINES)

    def setup_charts(self) -> None:
        background = self.palette().color(QPalette.ColorRole.Window)
        self.chart = ExpenseBarWidget(background)
        self.ui.sa_chart.setWidget(self.chart)
        self.ui.sa_chart.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        QWidget.setTabOrder(self.ui.pb_export, self.chart)
        QWidget.setTabOrder(self.chart, self.ui.tw_report)

        months_layout = QVBoxLayout()
        months_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.wdg_months.setLayout(months_layout)
        self.months_chart = ExpenseMonthsWidget(background)
        months_layout.addWidget(self.months_chart)

    def fit_to_screen(self) -> None:
        screen = self.screen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.resize(min(self.width(), available.width() - self.SCREEN_MARGIN),
                    min(self.height(), available.height() - self.SCREEN_MARGIN))

    def reset_filters(self) -> None:
        widgets = (self.ui.le_receiver, self.ui.lw_categories, self.ui.cb_skip_finance, self.ui.cb_skip_investment)
        for widget in widgets:
            widget.blockSignals(True)
        self.receiver_timer.stop()
        self.ui.le_receiver.clear()
        self.ui.lw_categories.clearSelection()
        self.ui.cb_skip_finance.setChecked(False)
        self.ui.cb_skip_investment.setChecked(False)
        for widget in widgets:
            widget.blockSignals(False)
        self.focus = None
        self.rebuild()

    def on_previous_start_changed(self, new_date: QDate) -> None:
        if new_date > self.ui.de_prev_end.date():
            self.set_date_silently(self.ui.de_prev_end, new_date)
        self.apply_previous_period()

    def on_previous_end_changed(self, new_date: QDate) -> None:
        if new_date < self.ui.de_prev_start.date():
            self.set_date_silently(self.ui.de_prev_start, new_date)
        self.apply_previous_period()

    @staticmethod
    def set_date_silently(date_edit: QDateEdit, new_date: QDate) -> None:
        date_edit.blockSignals(True)
        date_edit.setDate(new_date)
        date_edit.blockSignals(False)

    def apply_previous_period(self) -> None:
        self.previous_start = self.ui.de_prev_start.date().toPython()
        self.previous_end = self.ui.de_prev_end.date().toPython()
        self.load_payments()
        self.rebuild()

    def on_row_clicked(self, index: int) -> None:
        categories = self.rows[index].categories
        self.focus = None if self.focus == categories else categories
        if self.focus is not None:
            self.ui.tw_report.setCurrentWidget(self.ui.tab_receivers)
        self.rebuild()

    def reveal_chart_row(self, y: int) -> None:
        self.ui.sa_chart.ensureVisible(0, y, 0, self.REVEAL_MARGIN)

    def on_payment_activated(self, row: int, column: int) -> None:
        event_id = self.ui.tbl_payments.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if self.open_event is not None and event_id and self.open_event(event_id, self):
            self.load_payments()
            self.rebuild()

    def skip_sections(self) -> set[int]:
        sections = set()
        if self.ui.cb_skip_finance.isChecked():
            sections.add(category_section(LiabilityCategory.TOP_FINANCES))
        if self.ui.cb_skip_investment.isChecked():
            sections.add(category_section(LiabilityCategory.TOP_INVESTMENT))
        return sections

    def rebuild(self) -> None:
        self.receiver_timer.stop()
        categories = {item.data(Qt.ItemDataRole.UserRole) for item in self.ui.lw_categories.selectedItems()}
        compare = self.ui.cb_compare.isChecked()
        filtered = filter_payments(self.payments, categories, self.ui.le_receiver.text(), self.skip_sections())
        current = in_period(filtered, self.start, self.end)
        previous = in_period(filtered, self.previous_start, self.previous_end)
        self.total = total_stats(current)
        previous_total = total_stats(previous)

        by_category = collect_stats(current, lambda payment: payment.category)
        previous_by_category = collect_stats(previous, lambda payment: payment.category)
        merge_below = self.MERGE_BELOW if self.ui.cb_merge_small.isChecked() else None
        self.rows = build_structure(by_category, previous_by_category if compare else {}, merge_below)
        if self.focus not in [row.categories for row in self.rows]:
            self.focus = None

        in_focus = (lambda payment: True) if self.focus is None else (lambda payment: payment.category in self.focus)
        self.shown = [payment for payment in current if in_focus(payment)]
        shown_previous = [payment for payment in previous if in_focus(payment)]
        shown_total = total_stats(self.shown)

        self.fill_kpi_tiles(current, by_category, previous_total)
        self.chart.setRows(self.rows, [self.row_label(row) for row in self.rows], [self.row_color(row) for row in self.rows],
                           compare, next((index for index, row in enumerate(self.rows) if row.categories == self.focus), None),
                           [self.row_details(row) for row in self.rows])

        self.fill_stats_table(self.ui.tbl_categories, "Категория",
                              self.stats_items(by_category, previous_by_category, compare, self.category_label, CategoryItem),
                              self.total.amount, compare)
        by_receiver = collect_stats(self.shown, lambda payment: payment.receiver)
        previous_by_receiver = collect_stats(shown_previous, lambda payment: payment.receiver)
        self.fill_stats_table(self.ui.tbl_receivers, "Получатель",
                              self.stats_items(by_receiver, previous_by_receiver, compare, lambda receiver: receiver or "(не указан)"),
                              shown_total.amount, compare)
        by_month = collect_stats(self.shown, lambda payment: month_index(payment.day))
        self.fill_stats_table(self.ui.tbl_months, "Месяц оплаты",
                              [(NumberItem(self.month_name(month), month), stats, None) for month, stats in by_month.items()],
                              shown_total.amount, False, 0, Qt.SortOrder.AscendingOrder)
        self.fill_months_chart()
        self.fill_payments_table()

    @staticmethod
    def month_name(month: int, short: bool = False) -> str:
        year, month_number = divmod(month - 1, 12)
        if short:
            return f"{MONTHS_RU[month_number][:3]} {year % 100:02d}"
        return f"{MONTHS_RU[month_number]} {year}"

    def stats_items(self, current: dict, previous: dict, compare: bool, label,
                    item_type: type[QTableWidgetItem] = QTableWidgetItem) -> list[tuple[QTableWidgetItem, ExpenseStats, Decimal | None]]:
        keys = current.keys() | previous.keys() if compare else current.keys()
        items = []
        for key in keys:
            label_item = item_type(label(key))
            label_item.setData(Qt.ItemDataRole.UserRole, key)
            items.append((label_item, current.get(key, ExpenseStats()),
                          previous[key].amount if compare and key in previous else Decimal(0) if compare else None))
        return items

    def focus_text(self) -> str:
        if self.focus is None:
            return ""
        label = self.OTHER_NAME if len(self.focus) > 1 else self.category_label(self.focus[0])
        return f"Фильтр таблиц по категории: «{label}»"

    def fill_kpi_tiles(self, current: list[ExpensePayment], by_category: dict, previous_total: ExpenseStats) -> None:
        total = self.total
        previous_text = f"{self.previous_start:%d.%m.%Y} - {self.previous_end:%d.%m.%Y}"
        if total.count:
            top_category, top_stats = max(by_category.items(), key=lambda item: item[1].amount)
            top_share = float_strpercentage(float(share_of(top_stats.amount, total.amount)))
            peak_month_index, peak_amount = peak_month(current)
            expenses_caption = f"Расходы за период, оплат: {int_strspace(total.count)}"
            if total.refunds:
                expenses_caption += f", возвраты: {dec_strcommaspace(total.refunds, add_rub=True)}"
            tiles = [
                (dec_strcommaspace(total.amount, add_rub=True), expenses_caption,
                 f"Сумма оплат за период с учетом возвратов. Возвраты: {dec_strcommaspace(total.refunds, add_rub=True)}"),
                (dec_strcommaspace(monthly_average(total.amount, self.start, self.end), add_rub=True),
                 f"В среднем за месяц, пик: {self.month_name(peak_month_index)}",
                 f"Расходы за период в пересчете на месяц. Самый затратный месяц: {self.month_name(peak_month_index)} - "
                 f"{dec_strcommaspace(peak_amount, add_rub=True)}"),
                (self.category_label(top_category), f"Крупнейшая: {dec_strcommaspace(top_stats.amount, add_rub=True)} ({top_share})",
                 f"Крупнейшая категория: {dec_strcommaspace(top_stats.amount, add_rub=True)} ({top_share} всех расходов)"),
            ]
        else:
            tiles = [("-", "Расходы за период", ""), ("-", "Средний расход в месяц", ""), ("-", "Крупнейшая категория", "")]
        change = change_share(total.amount, previous_total.amount) if total.count else None
        self.change_text = "-"
        color = ""
        if change is None:
            tiles.append(("-", "Оплат в прошлом периоде нет" if not previous_total.count else "Изменение к прошлому периоду",
                          f"Предыдущий период: {previous_text}"))
        else:
            self.change_text = float_strsignedpercentage(float(change))
            arrow = "▲ " if change > 0 else "▼ " if change < 0 else ""
            color = ExpenseBarWidget.GROWTH_COLOR if change > 0 else ExpenseBarWidget.DROP_COLOR if change < 0 else ""
            tiles.append((f"{arrow}{self.change_text}", f"К прошлому периоду: {dec_strcommaspace(previous_total.amount, add_rub=True)}",
                          f"Предыдущий период: {previous_text}"))
        for number, (value, caption, tooltip) in enumerate(tiles, start=1):
            getattr(self.ui, f"lb_kpi{number}_value").setText(value)
            getattr(self.ui, f"lb_kpi{number}_caption").setText(caption)
            getattr(self.ui, f"fr_kpi{number}").setToolTip(tooltip)
        self.ui.lb_kpi4_value.setStyleSheet(f"color: {color};" if color else "")

    @staticmethod
    def table_view_state(table: QTableWidget, column_count: int, sort_column: int,
                         sort_order: Qt.SortOrder) -> tuple[int, Qt.SortOrder, bool]:
        if table.columnCount() == column_count and table.rowCount() > 0:
            header = table.horizontalHeader()
            return header.sortIndicatorSection(), header.sortIndicatorOrder(), True
        return sort_column, sort_order, False

    def fill_stats_table(self, table: QTableWidget, first_header: str,
                         items: list[tuple[QTableWidgetItem, ExpenseStats, Decimal | None]], total: Decimal, compare: bool,
                         sort_column: int = 3, sort_order: Qt.SortOrder = Qt.SortOrder.DescendingOrder) -> None:
        headers = [(first_header, first_header)] + self.STATS_HEADERS + (self.COMPARE_HEADERS if compare else [])
        sort_column, sort_order, keep_view = self.table_view_state(table, len(headers), sort_column, sort_order)
        scroll_position = table.verticalScrollBar().value()
        table.setSortingEnabled(False)
        self.set_headers(table, headers)
        table.setRowCount(len(items))
        for row, (label, stats, previous_amount) in enumerate(items):
            label.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setToolTip(label.text())
            table.setItem(row, 0, label)
            values = [
                NumberItem(int_strspace(stats.count), stats.count),
                NumberItem(dec_strcommaspace(stats.refunds), stats.refunds),
                NumberItem(dec_strcommaspace(stats.amount), stats.amount),
                NumberItem(float_strpercentage(float(share_of(stats.amount, total))), float(share_of(stats.amount, total))),
            ]
            if compare:
                change = change_share(stats.amount, previous_amount)
                values.append(NumberItem(dec_strcommaspace(previous_amount), previous_amount))
                values.append(ChangeItem("—" if change is None else float_strsignedpercentage(float(change)),
                                         None if change is None else float(change)))
            for column, number_item in enumerate(values, start=1):
                table.setItem(row, column, number_item)
        table.setSortingEnabled(True)
        table.sortByColumn(sort_column, sort_order)
        if keep_view:
            table.verticalScrollBar().setValue(scroll_position)
        else:
            self.adjust_columns(table, keep_width=table is self.ui.tbl_months)

    @staticmethod
    def set_headers(table: QTableWidget, headers: list[tuple[str, str]]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels([short_name for short_name, _ in headers])
        for column, (short_name, full_name) in enumerate(headers):
            header_item = table.horizontalHeaderItem(column)
            header_item.setData(Qt.ItemDataRole.UserRole, full_name)
            if short_name.replace("\n", " ") != full_name:
                header_item.setToolTip(full_name)

    def fill_months_chart(self) -> None:
        stacked = len({payment.category for payment in self.shown}) <= self.STACK_LIMIT
        top = self.top_categories if stacked else []
        series_by_category = stack_months(self.shown, top)
        months = [(month, self.month_name(month, short=True)) for month in month_range(self.start, self.end)]
        series = [(self.category_label(category), self.TOP_COLORS[index], series_by_category[category])
                  for index, category in enumerate(top) if category in series_by_category]
        if None in series_by_category:
            if not series:
                series.append((self.ALL_NAME, self.TOTAL_COLOR, series_by_category[None]))
            else:
                series.append((self.REST_NAME, ExpenseMonthsWidget.OTHER_COLOR, series_by_category[None]))
        self.months_chart.setSeries(months, series)

    def fill_payments_table(self) -> None:
        table = self.ui.tbl_payments
        sort_column, sort_order, keep_view = self.table_view_state(table, len(self.PAYMENT_HEADERS), 0, Qt.SortOrder.DescendingOrder)
        scroll_position = table.verticalScrollBar().value()
        table.setSortingEnabled(False)
        self.set_headers(table, self.PAYMENT_HEADERS)
        table.setRowCount(len(self.shown))
        for row, payment in enumerate(self.shown):
            table.setItem(row, 0, NumberItem(f"{payment.day:%d.%m.%Y}", payment.day.toordinal()))
            for column, text in ((1, payment.receiver), (2, payment.name), (3, CATEGORY_NAMES.get(payment.category, "Без категории"))):
                text_item = CategoryItem(" ".join(text.split())) if column == 3 else QTableWidgetItem(" ".join(text.split()))
                text_item.setToolTip(text_item.text())
                table.setItem(row, column, text_item)
            table.item(row, 3).setData(Qt.ItemDataRole.UserRole, payment.category)
            table.item(row, 1).setData(Qt.ItemDataRole.UserRole, payment.eventid)
            table.setItem(row, 4, NumberItem(dec_strcommaspace(payment.amount), payment.amount))
        table.setSortingEnabled(True)
        table.sortByColumn(sort_column, sort_order)
        if keep_view:
            table.verticalScrollBar().setValue(scroll_position)
        else:
            self.adjust_columns(table, (1, 2, 3))
        self.ui.tw_report.setTabText(self.ui.tw_report.indexOf(self.ui.tab_payments), f"Оплаты ({len(self.shown)})")

    @staticmethod
    def adjust_columns(table: QTableWidget, stretch_columns: tuple[int, ...] = (0,), keep_width: bool = False) -> None:
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.resizeColumnsToContents()
        metrics = header.fontMetrics()
        for column in range(table.columnCount()):
            title_width = metrics.horizontalAdvance(table.horizontalHeaderItem(column).text()) + ExpensesDialog.SORT_ARROW_PADDING
            header.resizeSection(column, max(header.sectionSize(column), title_width))
        if keep_width:
            table.setMinimumWidth(header.length() + table.verticalScrollBar().sizeHint().width() + table.frameWidth() * 2)
        for column in stretch_columns:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)

    def export_to_excel(self) -> None:
        if self.receiver_timer.isActive():
            self.rebuild()
        writer = ExpensesXlsWriter(self.settings_handler)
        if writer.write(self.report_sheets(), self.start_date, self.end_date, self):
            ExportSuccessDialog(writer.last_path, self).exec()

    def report_sheets(self) -> list[ExportSheet]:
        def table_sheet(name: str, table: QTableWidget) -> ExportSheet:
            count = table.columnCount()
            return DisciplineDialog.table_sheet(name, table, self.STATS_FORMATS[:count], self.STATS_WIDTHS[:count])

        return [
            self.summary_sheet(),
            table_sheet("По категориям", self.ui.tbl_categories),
            table_sheet("По получателям", self.ui.tbl_receivers),
            table_sheet("По месяцам", self.ui.tbl_months),
            DisciplineDialog.table_sheet("Оплаты", self.ui.tbl_payments, self.PAYMENT_FORMATS, self.PAYMENT_WIDTHS),
        ]

    def summary_sheet(self) -> ExportSheet:
        total = self.total
        categories = [item.text() for item in self.ui.lw_categories.selectedItems()]
        skipped = [text for check_box, text in ((self.ui.cb_skip_finance, "финансовая"), (self.ui.cb_skip_investment, "инвестиционная"))
                   if check_box.isChecked()]
        rows = [
            ["Период (по дате оплаты)", f"{self.start_date.toString('dd.MM.yyyy')} - {self.end_date.toString('dd.MM.yyyy')}"],
            ["Предыдущий период", f"{self.previous_start:%d.%m.%Y} - {self.previous_end:%d.%m.%Y}"],
            ["Категории", ", ".join(categories) or "Все"],
            ["Исключено", ", ".join(skipped) + " деятельность" if skipped else "Нет"],
            ["Получатель (часть названия)", self.ui.le_receiver.text().strip() or "Любой"],
            ["Фильтр таблиц по категории", self.focus_text().split(": ", 1)[-1] if self.focus else "Нет"],
            ["Оплат", int_strspace(total.count)],
            ["Расходы (с учетом возвратов)", dec_strcommaspace(total.amount, add_rub=True)],
            ["Возвраты", dec_strcommaspace(total.refunds, add_rub=True)],
            ["Изменение к предыдущему периоду", self.change_text],
        ]
        return ExportSheet("Сводка", ["Показатель", "Значение"], rows, [None, None], [44, 90])
