from decimal import Decimal
from enum import Enum, auto

from PySide6.QtCore import QAbstractTableModel, QDate, QEvent, QModelIndex, QPointF, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen
from PySide6.QtWidgets import QHeaderView, QLabel, QMenu, QStyle, QStyledItemDelegate, QTableWidgetItem, QWidget

from base.date import MONTHS_RU, first_date_of_month
from base.dbhandler import DBHandler
from base.formatting import COLOR_CALENDAR, dec_strcommaspace
from base.liability import Col, FilterFlags, STORED_INDEX
from base.liabilitystore import CalendarDay, LiabilityStore
from base.workcalendar import WEEKDAY_ABBR, is_working_day
from gui.ui.calendarwidget_ui import Ui_CalendarWidget

DAYS_IN_WEEK = 7
WEEKS_SHOWN = 6


class DayStatus(Enum):
    OPEN = auto()
    OVERDUE = auto()
    PAID = auto()
    REFUND = auto()


MONTHS_GENITIVE = ("января", "февраля", "марта", "апреля", "мая", "июня",
                   "июля", "августа", "сентября", "октября", "ноября", "декабря")

STATUS_TEXT = {DayStatus.OPEN: "Ожидает оплаты", DayStatus.OVERDUE: "Просрочено",
               DayStatus.PAID: "Оплачено", DayStatus.REFUND: "Возврат"}


def day_status(date: QDate, day: CalendarDay | None, today: QDate) -> DayStatus | None:
    if day is None:
        return None
    if day.remain <= 0:
        return DayStatus.REFUND if day.total < 0 else DayStatus.PAID
    return DayStatus.OVERDUE if date < today else DayStatus.OPEN


def day_amount(day: CalendarDay, status: DayStatus) -> Decimal:
    return day.total if status in (DayStatus.PAID, DayStatus.REFUND) else day.remain


def day_count_text(day: CalendarDay) -> str:
    count = len(day.event_ids)
    if 0 < day.unpaid < count:
        return f"{day.unpaid} из {count}"
    return f"{count} пл."


def day_title(date: QDate, day: CalendarDay | None, status: DayStatus | None) -> str:
    title = f"{date.day()} {MONTHS_GENITIVE[date.month() - 1]} {date.year()}, {WEEKDAY_ABBR[date.dayOfWeek()]}"
    if day is None:
        return title
    label = "сумма" if status in (DayStatus.PAID, DayStatus.REFUND) else "остаток"
    return f"{title} · платежей: {len(day.event_ids)} · {label}: {dec_strcommaspace(day_amount(day, status))}"


def day_tooltip(date: QDate, day: CalendarDay, status: DayStatus) -> str:
    count = len(day.event_ids)
    lines = [f"{date.toString('dd.MM.yyyy')}: {STATUS_TEXT[status]}"]
    lines.append(f"Платежей: {count}" + (f", не оплачено: {day.unpaid}" if 0 < day.unpaid < count else ""))
    label = "Сумма" if status in (DayStatus.PAID, DayStatus.REFUND) else "Остаток"
    lines.append(f"{label}: {dec_strcommaspace(day_amount(day, status))}")
    return "\n".join(lines)


class MonthGridModel(QAbstractTableModel):

    DateRole = Qt.ItemDataRole.UserRole
    DayRole = Qt.ItemDataRole.UserRole + 1
    NonWorkingRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, db_handler: DBHandler, parent=None):
        super().__init__(parent)
        self.db_handler = db_handler
        self.today: QDate = QDate.currentDate()
        self.days: dict[QDate, CalendarDay] = {}
        self.non_working: set[QDate] = set()
        self.month: QDate = QDate()
        self.first_cell: QDate = QDate()
        self.set_month(self.today)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else WEEKS_SHOWN

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else DAYS_IN_WEEK

    def set_month(self, month: QDate) -> None:
        self.beginResetModel()
        self.month = first_date_of_month(month)
        self.first_cell = self.month.addDays(1 - self.month.dayOfWeek())
        cells = (self.first_cell.addDays(offset) for offset in range(WEEKS_SHOWN * DAYS_IN_WEEK))
        self.non_working = {date for date in cells if not is_working_day(self.db_handler, date)}
        self.endResetModel()

    def set_days(self, days: dict[QDate, CalendarDay], today: QDate) -> None:
        self.beginResetModel()
        self.days = days
        self.today = today
        self.endResetModel()

    def date_at(self, index: QModelIndex) -> QDate:
        return self.first_cell.addDays(index.row() * DAYS_IN_WEEK + index.column())

    def index_of(self, date: QDate) -> QModelIndex:
        offset = self.first_cell.daysTo(date)
        if not 0 <= offset < WEEKS_SHOWN * DAYS_IN_WEEK:
            return QModelIndex()
        return self.index(offset // DAYS_IN_WEEK, offset % DAYS_IN_WEEK)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return WEEKDAY_ABBR[section + 1]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        date = self.date_at(index)
        if role == self.DateRole:
            return date
        if role == self.DayRole:
            return self.days.get(date)
        if role == self.NonWorkingRole:
            return date in self.non_working
        if role == Qt.ItemDataRole.ToolTipRole:
            day = self.days.get(date)
            return None if day is None else day_tooltip(date, day, day_status(date, day, self.today))
        return None


class DayCellDelegate(QStyledItemDelegate):

    PADDING = 3
    NUMBER_SIZE_EXTRA = 1
    BACKCOLOR = {DayStatus.OVERDUE: QColor("#fbeeec"), DayStatus.PAID: QColor("#e4f1e7")}
    AMOUNT_COLOR = {DayStatus.OPEN: QColor("#202124"), DayStatus.OVERDUE: QColor("#d00000"),
                    DayStatus.PAID: QColor("#276a2b"), DayStatus.REFUND: QColor("#202124")}
    ICON_SIZE = 11
    HOVER_COLOR = QColor(0, 0, 0, 20)
    NON_WORKING_BACKCOLOR = QColor("#f1f2f4")
    MUTED_TEXT_COLOR = QColor("#5f6368")

    def sizeHint(self, option, index) -> QSize:
        return QSize(100, 70)

    def draw_status_icon(self, painter, rect: QRect, status: DayStatus) -> None:
        if status not in (DayStatus.PAID, DayStatus.OVERDUE):
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.AMOUNT_COLOR[status])
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor("#ffffff"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        x, y, size = rect.x(), rect.y(), rect.width()
        if status == DayStatus.PAID:
            painter.drawPolyline([QPointF(x + size * 0.27, y + size * 0.52), QPointF(x + size * 0.43, y + size * 0.69),
                                  QPointF(x + size * 0.74, y + size * 0.31)])
        else:
            painter.drawLine(QPointF(x + size / 2, y + size * 0.22), QPointF(x + size / 2, y + size * 0.55))
            painter.drawPoint(QPointF(x + size / 2, y + size * 0.77))
        painter.restore()

    def paint(self, painter, option, index) -> None:
        model = index.model()
        date: QDate = index.data(MonthGridModel.DateRole)
        day: CalendarDay | None = index.data(MonthGridModel.DayRole)
        non_working: bool = index.data(MonthGridModel.NonWorkingRole)
        status = day_status(date, day, model.today)
        is_today = date == model.today
        rect = option.rect

        painter.save()
        if status in self.BACKCOLOR:
            painter.fillRect(rect, self.BACKCOLOR[status])
        elif non_working:
            painter.fillRect(rect, self.NON_WORKING_BACKCOLOR)
        else:
            painter.fillRect(rect, option.palette.base())
        muted = non_working or date.month() != model.month.month()

        inner = rect.adjusted(self.PADDING, self.PADDING, -self.PADDING, -self.PADDING)
        font = QFont(option.font)
        number_font = QFont(font)
        number_font.setBold(True)
        number_font.setPointSizeF(font.pointSizeF() + self.NUMBER_SIZE_EXTRA)
        painter.setFont(number_font)
        metrics = painter.fontMetrics()
        number = str(date.day())
        number_rect = QRect(inner.left(), inner.top(), metrics.horizontalAdvance(number) + 6, metrics.height())
        if is_today:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLOR_CALENDAR))
            painter.drawRoundedRect(number_rect, 3, 3)
            painter.setPen(QColor("#ffffff"))
        else:
            painter.setPen(self.MUTED_TEXT_COLOR if muted else option.palette.text().color())
        painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, number)

        painter.setFont(font)
        metrics = painter.fontMetrics()
        if day is not None:
            painter.setPen(self.MUTED_TEXT_COLOR)
            count_text = day_count_text(day)
            count_rect = QRect(number_rect.right() + 1, inner.top(), inner.right() - number_rect.right(), metrics.height())
            painter.drawText(count_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, count_text)
            icon_left = number_rect.right() + 4
            if icon_left + self.ICON_SIZE < inner.right() - metrics.horizontalAdvance(count_text) - 2:
                icon_top = inner.top() + (metrics.height() - self.ICON_SIZE) // 2
                self.draw_status_icon(painter, QRect(icon_left, icon_top, self.ICON_SIZE, self.ICON_SIZE), status)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(self.AMOUNT_COLOR[status])
            amount_text = dec_strcommaspace(day_amount(day, status))
            amount_rect = QRect(inner.left(), inner.bottom() - metrics.height(), inner.width(), metrics.height())
            painter.drawText(amount_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             painter.fontMetrics().elidedText(amount_text, Qt.TextElideMode.ElideRight, inner.width()))
        painter.restore()

        if option.state & QStyle.StateFlag.State_MouseOver and not option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, self.HOVER_COLOR)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.setPen(QPen(QColor(COLOR_CALENDAR), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()


class EventRowDelegate(QStyledItemDelegate):

    SELECTION_COLOR = QColor("#dae8f5")

    def initStyleOption(self, option, index) -> None:
        super().initStyleOption(option, index)
        option.state &= ~QStyle.StateFlag.State_HasFocus
        foreground = index.data(Qt.ItemDataRole.ForegroundRole)
        option.palette.setColor(QPalette.ColorRole.Highlight, self.SELECTION_COLOR)
        option.palette.setBrush(QPalette.ColorRole.HighlightedText,
                                foreground if foreground is not None else option.palette.text())


class CalendarWidget(QWidget):

    EVENT_HEADERS = ("Получатель", "Остаток", "Название")
    REMAIN_COLUMN = 1
    OVERDUE_REMAIN_COLOR = QColor("#d00000")
    UNDATED_MENU_LIMIT = 30
    PAID_ROW_COLOR = QColor("#5f6368")

    eventSelected = Signal(int)
    eventActivated = Signal()
    eventCleared = Signal()

    def __init__(self, store: LiabilityStore, db_handler: DBHandler, parent=None):
        super().__init__(parent)
        self.ui = Ui_CalendarWidget()
        self.ui.setupUi(self)

        self.store = store
        self.selected: QDate = store.current_date
        self.current_event_id: int | None = None
        self.overdue_dates: list[QDate] = []
        self.dirty = False
        self.reload_timer = QTimer(self)
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.reload)
        self.model = MonthGridModel(db_handler, self)
        self.model.set_month(self.selected)

        table = self.ui.tv_calendar
        table.setModel(self.model)
        table.setItemDelegate(DayCellDelegate(table))
        table.setMouseTracking(True)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(70)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.verticalHeader().hide()
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        events = self.ui.tbl_events
        events.setColumnCount(len(self.EVENT_HEADERS))
        events.setHorizontalHeaderLabels(self.EVENT_HEADERS)
        events.setItemDelegate(EventRowDelegate(events))
        events.setWordWrap(False)
        self.empty_label = QLabel("В этот день платежей нет", events.viewport())
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #5f6368;")
        self.empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        events.viewport().installEventFilter(self)
        events_header = events.horizontalHeader()
        events_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        events_header.setSectionResizeMode(self.REMAIN_COLUMN, QHeaderView.ResizeMode.ResizeToContents)
        events_header.setHighlightSections(False)

        self.ui.spl_calendar.setStretchFactor(0, 3)
        self.ui.spl_calendar.setStretchFactor(1, 2)

        self.ui.tb_prev.clicked.connect(lambda: self.change_month(-1))
        self.ui.tb_next.clicked.connect(lambda: self.change_month(1))
        self.ui.pb_today.clicked.connect(lambda: self.show_date(self.store.current_date))
        self.ui.pb_overdue.clicked.connect(self.go_to_overdue)
        self.ui.pb_undated.clicked.connect(self.show_undated_menu)
        self.ui.pb_month.clicked.connect(self.show_month_menu)
        table.selectionModel().currentChanged.connect(self.on_current_changed)
        table.activated.connect(self.open_day_event)
        events.currentCellChanged.connect(self.on_event_row_changed)
        events.activated.connect(self.open_current_event)

        self.reload()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.ui.tbl_events.viewport() and event.type() == QEvent.Type.Resize:
            self.empty_label.setGeometry(watched.rect())
        return super().eventFilter(watched, event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.dirty:
            self.reload()

    def schedule_reload(self) -> None:
        if self.isVisible():
            self.reload_timer.start()
        else:
            self.dirty = True

    def change_month(self, step: int) -> None:
        month = self.model.month.addMonths(step)
        self.show_date(QDate(month.year(), month.month(), min(self.selected.day(), month.daysInMonth())))

    def show_date(self, date: QDate) -> None:
        self.selected = date
        self.model.set_month(date)
        self.reload()

    def select_event(self, event_id: int | None) -> None:
        due_date = None if event_id is None else self.store.due_dates.get(event_id)
        if due_date is None or not due_date.isValid() or event_id == self.current_event_id:
            return
        self.current_event_id = event_id
        self.show_date(due_date)

    def reload(self) -> None:
        self.dirty = False
        self.reload_timer.stop()
        days, undated = self.store.calendar_days()
        self.model.set_days(days, self.store.current_date)
        self.ui.pb_month.setText(f"{MONTHS_RU[self.model.month.month() - 1]} {self.model.month.year()}")
        self.ui.pb_undated.setText(f"Без срока: {undated}")
        self.ui.pb_undated.setVisible(undated > 0)
        self.update_overdue_button()
        self.ui.tv_calendar.setCurrentIndex(self.model.index_of(self.selected))
        self.fill_events()

    def update_overdue_button(self) -> None:
        overdue = self.store.overdue_days()
        self.overdue_dates = sorted(overdue)
        count = sum(len(day.event_ids) for day in overdue.values())
        total = sum((day.remain for day in overdue.values()), Decimal(0))
        self.ui.pb_overdue.setVisible(count > 0)
        self.ui.pb_overdue.setText(f"Просрочено: {count} на {dec_strcommaspace(total)}")

    def show_undated_menu(self) -> None:
        event_ids = self.store.undated_event_ids()
        menu = QMenu(self)
        for event_id in event_ids[:self.UNDATED_MENU_LIMIT]:
            values = self.store.event_values(event_id)
            receiver, name = (str(values[STORED_INDEX[column]] or "") for column in (Col.RECEIVER, Col.NAME))
            remain = dec_strcommaspace(self.store.row_by_id(event_id).remain)
            action = menu.addAction(f"{receiver} — {name} ({remain})")
            action.triggered.connect(lambda checked=False, event_id=event_id: self.open_undated_event(event_id))
        if len(event_ids) > self.UNDATED_MENU_LIMIT:
            menu.addSeparator()
            menu.addAction(f"…и ещё {len(event_ids) - self.UNDATED_MENU_LIMIT}").setEnabled(False)
        menu.exec(self.ui.pb_undated.mapToGlobal(self.ui.pb_undated.rect().bottomLeft()))

    def open_undated_event(self, event_id: int) -> None:
        self.eventSelected.emit(event_id)
        self.eventActivated.emit()

    def show_month_menu(self) -> None:
        menu = QMenu(self)
        month = self.model.month
        for number, name in enumerate(MONTHS_RU, 1):
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(number == month.month())
            action.triggered.connect(lambda checked=False, number=number: self.change_month(number - month.month()))
        menu.addSeparator()
        menu.addAction(f"{month.year() - 1} год").triggered.connect(lambda: self.change_month(-12))
        menu.addAction(f"{month.year() + 1} год").triggered.connect(lambda: self.change_month(12))
        menu.exec(self.ui.pb_month.mapToGlobal(self.ui.pb_month.rect().bottomLeft()))

    def go_to_overdue(self) -> None:
        later = [date for date in self.overdue_dates if date > self.selected]
        self.show_date(later[0] if later else self.overdue_dates[0])

    def on_current_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        if current.isValid():
            self.selected = self.model.date_at(current)
            if self.selected.month() != self.model.month.month():
                date = self.selected
                QTimer.singleShot(0, lambda: self.show_date(date))
                return
            self.fill_events()

    def fill_events(self) -> None:
        day = self.model.days.get(self.selected)
        event_ids = day.event_ids if day is not None else ()
        self.ui.la_day.setText(day_title(self.selected, day, day_status(self.selected, day, self.model.today)))
        self.empty_label.setVisible(not event_ids)
        table = self.ui.tbl_events
        table.blockSignals(True)
        table.setRowCount(len(event_ids))
        for row, event_id in enumerate(event_ids):
            values = self.store.event_values(event_id)
            liability = self.store.row_by_id(event_id)
            texts = (str(values[STORED_INDEX[Col.RECEIVER]] or ""), dec_strcommaspace(liability.remain),
                     str(values[STORED_INDEX[Col.NAME]] or ""))
            for column, text in enumerate(texts):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, event_id)
                item.setToolTip(text)
                if liability.remain <= 0:
                    item.setForeground(self.PAID_ROW_COLOR)
                if column == self.REMAIN_COLUMN:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    if FilterFlags.DUE in liability.filter_flags and liability.remain > 0:
                        item.setForeground(self.OVERDUE_REMAIN_COLOR)
                table.setItem(row, column, item)
        table.blockSignals(False)

        if not event_ids:
            was_selected = self.current_event_id is not None
            self.current_event_id = None
            if was_selected:
                self.eventCleared.emit()
            return
        chosen = self.current_event_id if self.current_event_id in event_ids else event_ids[0]
        table.selectRow(event_ids.index(chosen))
        self.set_current_event(chosen)

    def set_current_event(self, event_id: int) -> None:
        if event_id != self.current_event_id:
            self.current_event_id = event_id
            self.eventSelected.emit(event_id)

    def on_event_row_changed(self, row: int, column: int, previous_row: int, previous_column: int) -> None:
        item = self.ui.tbl_events.item(row, 0)
        if item is not None:
            self.set_current_event(item.data(Qt.ItemDataRole.UserRole))

    def open_day_event(self, index: QModelIndex) -> None:
        day = self.model.days.get(self.model.date_at(index))
        if day is None:
            return
        if len(day.event_ids) == 1:
            self.eventActivated.emit()
        else:
            self.ui.tbl_events.setFocus()

    def open_current_event(self) -> None:
        if self.current_event_id is not None:
            self.eventActivated.emit()
