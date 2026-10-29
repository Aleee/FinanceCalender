from PySide6 import QtCore
from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent
from PySide6.QtWidgets import QLabel, QToolTip, QWidget, QVBoxLayout
import pyqtgraph as pg

from datetime import date, timedelta
from decimal import Decimal
from html import escape

from base.discipline import BUCKET_NAMES, DelayBucket, DisciplineStats
from base.expenses import StructureRow, change_share
from base.formatting import dec_strcommaspace, float_strpercentage, float_strsignedpercentage, int_strspace

class MoneyAxis(pg.AxisItem):

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
        result = []

        for v in values:
            try:
                # пробелы между тысячами
                s = f"{v:,.0f}".replace(",", " ")
                result.append(s)
            except Exception:
                result.append("")

        return result

class DateAxis(pg.AxisItem):

    def __init__(self, *args, first_day: date | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_day = first_day

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:

        if self.first_day is None:
            return [str(int(v)) for v in values]

        return [
            (self.first_day + timedelta(days=int(v))).strftime("%d.%m")
            for v in values
        ]

class DebtChartWidget(QWidget):

    def __init__(self, bg_color, parent: QWidget | None = None):
        super().__init__(parent)

        # пустой список по умолчанию: если setTimeline ещё не вызывали
        # (или ей передали пустой таймлайн), движение мыши не должно падать
        self.timeline: list = []

        pg.setConfigOptions(antialias=True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pg.setConfigOptions(
            background=bg_color,
            foreground='#2b2b2b'
        )

        self.right_axis = pg.AxisItem("right")
        self.right_axis.setLabel("% просрочки")

        self.plot = pg.PlotWidget(
            axisItems={
                "left": MoneyAxis(orientation="left"),
                "bottom": DateAxis(orientation="bottom"),
                "right": self.right_axis
            }
        )

        self.plot.getPlotItem().hideButtons()

        vb = self.plot.getViewBox()
        vb.setLimits(yMin=0)

        layout.addWidget(self.plot)

        self.right_vb = pg.ViewBox()
        self.right_axis.linkToView(self.right_vb)
        self.plot.scene().addItem(self.right_vb)
        self.plot.getViewBox().sigResized.connect(self.updateViews)
        self.right_vb.setXLink(self.plot.getViewBox())

        self.activePoint = pg.ScatterPlotItem(
            size=12,
            pen=pg.mkPen('w', width=2),
            brush=pg.mkBrush(30, 144, 255)
        )

        self.overduePoint = pg.ScatterPlotItem(
            size=12,
            pen=pg.mkPen('w', width=2),
            brush=pg.mkBrush(220, 20, 60)
        )

        self.plot.addItem(self.activePoint)
        self.plot.addItem(self.overduePoint)

        self.vLine = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#666", width=1)
        )
        self.plot.addItem(self.vLine)

        self.tooltip = pg.TextItem(
            anchor=(0, 1),
            fill=pg.mkBrush(255, 255, 255, 180),
            border=pg.mkPen("#888")
        )
        self.tooltip.setZValue(1000)
        self.plot.addItem(self.tooltip)

        self.plot.showGrid(x=True, y=True, alpha=0.2)

        self.plot.getAxis("left").setStyle(tickFont=pg.QtGui.QFont("Arial", 11))
        self.plot.getAxis("bottom").setStyle(tickFont=pg.QtGui.QFont("Arial", 10))


        self.plot.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.plot.scene().installEventFilter(self)

        self.totalCurve = pg.PlotCurveItem(
            pen=pg.mkPen("#2979FF", width=3)
        )
        self.totalCurve.setFillLevel(0)
        self.totalCurve.setBrush(pg.mkBrush(41, 121, 255, 70))

        self.overdueCurve = pg.PlotCurveItem(
            pen=pg.mkPen("#E53935", width=3)
        )
        self.overdueCurve.setFillLevel(0)
        self.overdueCurve.setBrush(pg.mkBrush(229, 57, 53, 90))

        self.totalSmoothCurve = pg.PlotCurveItem(
            pen=pg.mkPen('#1f77b4', width=2, style=QtCore.Qt.DashLine)
        )
        self.overdueSmoothCurve = pg.PlotCurveItem(
            pen=pg.mkPen('#d62728', width=2, style=QtCore.Qt.DashLine)
        )

        self.shareCurve = pg.PlotCurveItem(
            pen=pg.mkPen('#800080', width=2)
        )

        self.plot.addItem(self.totalCurve)
        self.plot.addItem(self.overdueCurve)
        self.plot.addItem(self.totalSmoothCurve)
        self.plot.addItem(self.overdueSmoothCurve)
        self.right_vb.addItem(self.shareCurve)

        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.enableAutoRange(x=False, y=False)
        vb.wheelEvent = lambda ev: ev.accept()
        vb.setMouseMode(pg.ViewBox.PanMode)

        # скрываем линию/тултип/точки, пока мышь ни разу не наведена на график
        self.hideHover()

    def buildSeries(self, smoothing: int = 10) -> tuple[list[int], list[float], list[float], list[float], list[float], list[float]]:

        x = list(range(len(self.timeline)))

        total = [float(d.total) for d in self.timeline]
        overdue = [float(d.overdue) for d in self.timeline]
        share = [(o / t * 100) if t else 0 for t, o in zip(total, overdue)]

        smooth_total = self.moving_average_centered(total, smoothing)
        smooth_overdue = self.moving_average_centered(overdue, smoothing)

        smooth_share_scaled = self.moving_average_centered(share, smoothing)

        return x, total, overdue, smooth_share_scaled, smooth_total, smooth_overdue

    def setTimeline(self, timeline: list, smoothing: int = 10) -> None:

        if not timeline:
            return

        self.timeline = timeline
        self.first_day = timeline[0].day
        self.plot.getAxis("bottom").first_day = self.first_day

        x, total, overdue, smooth_share_scaled, smooth_total, smooth_overdue = self.buildSeries(smoothing)

        self.totalCurve.setData(x, total)
        self.overdueCurve.setData(x, overdue)
        self.totalSmoothCurve.setData(x, smooth_total)
        self.overdueSmoothCurve.setData(x, smooth_overdue)
        self.shareCurve.setData(x, smooth_share_scaled)

        self.plot.setXRange(0, len(self.timeline) - 1, padding=0.02)

        # total и overdue уже посчитаны в buildSeries, не считаем их заново
        y_max = max(total + overdue)

        # чтобы при всех нулях был нормальный масштаб
        if y_max <= 0:
            y_max = 1000

        self.plot.setYRange(0, y_max * 1.05, padding=0)

        self.right_vb.setYRange(0, 100, padding=0)
        self.right_vb.enableAutoRange(y=False)


    def onMouseMoved(self, pos: QtCore.QPointF) -> None:

        if not self.plot.sceneBoundingRect().contains(pos):
            self.hideHover()
            return

        if not self.timeline:
            return

        self.tooltip.show()
        self.vLine.show()
        self.activePoint.show()
        self.overduePoint.show()

        # перевод в координаты графика
        mousePoint = self.plot.getViewBox().mapSceneToView(pos)

        # snap к ближайшей точке
        x = int(round(mousePoint.x()))

        if x < 0:
            x = 0
        elif x >= len(self.timeline):
            x = len(self.timeline) - 1

        item = self.timeline[x]

        # вертикальная линия
        self.vLine.setPos(x)

        # данные - формат как везде в проекте (пробел между тысячами, запятая вместо точки)
        total = dec_strcommaspace(item.total)
        overdue = dec_strcommaspace(item.overdue)

        # ---- центр Y ----
        vb = self.plot.getViewBox()
        y_min, y_max = vb.viewRange()[1]
        y_center = (y_min + y_max) / 2

        # ---- HTML ----
        self.tooltip.setHtml(f"""
        <div style="
            background: #ffffff;
            border: 1px solid #d0d0d0;
            padding: 8px 10px;
            border-radius: 6px;

            color: #1a1a1a;
            font-size: 10pt;

            /* читаемость */
            font-weight: 500;
            line-height: 1.4;
        ">
            <div style="font-weight: 700; font-size: 11pt; margin-bottom: 3px;">
                {item.day:%d.%m.%Y}</div>
            <div>Общая: <b>{total}</b></div>
            <div style="color:#b00020;">Просрочка: <b>{overdue}</b></div>
            <div style="color:#800080;">Доля: <b>{(item.overdue / item.total) if item.total else 0:.1%}</b></div>
        </div>
        """)

        # ---- координаты ----
        scene_rect = self.plot.sceneBoundingRect()

        # X позиции линии в scene
        line_scene_x = vb.mapViewToScene(pg.Point(x, 0)).x()

        tooltip_rect = self.tooltip.boundingRect()
        tooltip_w = tooltip_rect.width()

        # базово справа
        x_scene = line_scene_x + 20

        # если не помещается → слева
        if x_scene + tooltip_w > scene_rect.right():
            x_scene = line_scene_x - tooltip_w - 20

        # перевод scene → view
        x_view = vb.mapSceneToView(pg.Point(x_scene, 0)).x()

        self.tooltip.setPos(x_view, y_center)

        y = float(item.total)  # можно заменить на overdue или max

        self.activePoint.setData(
            [x],
            [y]
        )
        self.overduePoint.setData(
            [x],
            [float(item.overdue)]
        )

    @staticmethod
    def moving_average_centered(values: list[float], window: int = 10) -> list[float]:
        result = []

        n = len(values)

        for i in range(n):
            start = max(0, i - window)
            end = min(n, i + window + 1)

            window_vals = values[start:end]

            result.append(sum(window_vals) / len(window_vals))

        return result

    def updateViews(self) -> None:
        self.right_vb.setGeometry(self.plot.getViewBox().sceneBoundingRect())

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:

        if event.type() == QtCore.QEvent.GraphicsSceneHoverMove:
            self.onMouseMoved(event.scenePos())
            return False

        if event.type() == QtCore.QEvent.GraphicsSceneLeave:
            self.hideHover()
            return False

        return super().eventFilter(obj, event)

    def hideHover(self) -> None:
        self.tooltip.hide()
        self.vLine.hide()
        self.activePoint.hide()
        self.overduePoint.hide()


class WholeNumberAxis(MoneyAxis):

    LABEL_GAP = 8

    def _updateWidth(self) -> None:
        super()._updateWidth()
        if self.isVisible() and self.fixedWidth is None and self.label.isVisible():
            width = self.maximumWidth() + self.LABEL_GAP
            self.setMaximumWidth(width)
            self.setMinimumWidth(width)

    def tickValues(self, minVal: float, maxVal: float, size: float) -> list:
        levels = super().tickValues(minVal, maxVal, size)
        return [(spacing, [value for value in values if float(value).is_integer()])
                for spacing, values in levels if spacing >= 1]


class DelayChartWidget(QWidget):

    bucketClicked = Signal(int)

    COLORS = ("#66BB6A", "#FDD835", "#F57C00", "#B71C1C", "#757575")
    OVERDUE_INDEX = len(DelayBucket)
    COLUMN_NAMES = (*BUCKET_NAMES.values(), "Не оплачено (просрочено)")
    TEXT_COLOR = "#2b2b2b"
    DIMMED_ALPHA = 90
    TINT_ALPHA = 70

    def __init__(self, bg_color, parent: QWidget | None = None):
        super().__init__(parent)

        self.heights: list[float] = []
        self.hints: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pg.setConfigOptions(
            background=bg_color,
            foreground=self.TEXT_COLOR
        )

        self.plot = pg.PlotWidget(axisItems={"left": WholeNumberAxis(orientation="left")})
        self.plot.getPlotItem().hideButtons()
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(y=True, alpha=0.2)
        self.plot.getAxis("left").setStyle(tickFont=QFont("Arial", 10))
        self.plot.getAxis("bottom").setStyle(tickFont=QFont("Arial", 10))
        self.plot.setTitle("Платежи по задержке оплаты", size="10pt")
        layout.addWidget(self.plot)

        self.plot.scene().sigMouseClicked.connect(self.onMouseClicked)
        self.plot.scene().sigMouseMoved.connect(self.onMouseMoved)

    @classmethod
    def tint(cls, index: int) -> QColor:
        color = QColor(cls.COLORS[index])
        color.setAlpha(cls.TINT_ALPHA)
        return color

    def columnAt(self, x: float) -> int | None:
        index = round(x)
        if abs(x - index) > 0.5 or not 0 <= index < len(self.heights) or self.heights[index] <= 0:
            return None
        return index

    def setStats(self, stats: DisciplineStats, overdue_count: int = 0, overdue_amount: Decimal = Decimal(0),
                 by_amount: bool = False, selected: DelayBucket | None = None) -> None:
        self.plot.clear()
        self.heights = []
        self.hints = []
        self.plot.setLabel("left", "Сумма, руб." if by_amount else "Кол-во платежей")

        if not stats.count and not overdue_count:
            self.plot.getAxis("bottom").setTicks([[]])
            self.plot.setXRange(-0.6, self.OVERDUE_INDEX + 0.6, padding=0)
            self.plot.setYRange(0, 1, padding=0)
            empty_label = pg.TextItem("Нет данных по выбранным условиям", color=self.TEXT_COLOR, anchor=(0.5, 0.5))
            empty_label.setFont(QFont("Arial", 11))
            empty_label.setPos(self.OVERDUE_INDEX / 2, 0.5)
            self.plot.addItem(empty_label)
            return

        total = float(stats.amount) if by_amount else stats.count
        values = [float(stats.bucket_amounts[bucket]) if by_amount else stats.buckets[bucket] for bucket in DelayBucket]
        values.append(float(overdue_amount) if by_amount else overdue_count)
        self.heights = values

        brushes = []
        for index, color in enumerate(self.COLORS):
            fill = QColor(color)
            if selected is not None and index != selected:
                fill.setAlpha(self.DIMMED_ALPHA)
            brushes.append(fill)
        self.plot.addItem(pg.BarGraphItem(x=list(range(len(values))), height=values, width=0.6,
                                          brushes=brushes, pen=pg.mkPen(self.TEXT_COLOR)))

        for index, value in enumerate(values):
            count = overdue_count if index == self.OVERDUE_INDEX else stats.buckets[DelayBucket(index)]
            amount = overdue_amount if index == self.OVERDUE_INDEX else stats.bucket_amounts[DelayBucket(index)]
            self.hints.append(f"{self.COLUMN_NAMES[index]}: {int_strspace(count)} шт. на {dec_strcommaspace(amount, add_rub=True)}")
            if value <= 0:
                continue
            text = f"{value:,.0f}".replace(",", " ") if by_amount else int_strspace(int(value))
            if index != self.OVERDUE_INDEX and total:
                text += f" ({value / total:.0%})"
            label = pg.TextItem(text, color=self.TEXT_COLOR, anchor=(0.5, 1))
            label.setFont(QFont("Arial", 10))
            label.setPos(index, value)
            self.plot.addItem(label)

        self.plot.addItem(pg.InfiniteLine(pos=self.OVERDUE_INDEX - 0.5, angle=90, pen=pg.mkPen("#999", style=Qt.PenStyle.DashLine)))
        self.plot.getAxis("bottom").setTicks([list(enumerate(self.COLUMN_NAMES))])
        self.plot.setXRange(-0.6, self.OVERDUE_INDEX + 0.6, padding=0)
        self.plot.setYRange(0, max(max(values), 1) * 1.2, padding=0)

    def cursorColumn(self, scene_pos) -> int | None:
        view_box = self.plot.getViewBox()
        if not view_box.sceneBoundingRect().contains(scene_pos):
            return None
        return self.columnAt(view_box.mapSceneToView(scene_pos).x())

    def onMouseClicked(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = self.cursorColumn(event.scenePos())
        if index is not None:
            self.bucketClicked.emit(index)

    def onMouseMoved(self, scene_pos) -> None:
        index = self.cursorColumn(scene_pos)
        self.plot.setCursor(Qt.CursorShape.ArrowCursor if index is None else Qt.CursorShape.PointingHandCursor)
        self.plot.setToolTip("" if index is None else self.hints[index])


class MonthTrendWidget(QWidget):

    LINE_COLOR = "#1E88E5"
    TEXT_COLOR = "#2b2b2b"
    MAX_TICKS = 18

    def __init__(self, bg_color, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pg.setConfigOptions(
            background=bg_color,
            foreground=self.TEXT_COLOR
        )

        self.plot = pg.PlotWidget(axisItems={"left": WholeNumberAxis(orientation="left")})
        self.plot.getPlotItem().hideButtons()
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(y=True, alpha=0.2)
        self.plot.getAxis("left").setStyle(tickFont=QFont("Arial", 9))
        self.plot.getAxis("bottom").setStyle(tickFont=QFont("Arial", 9))
        self.plot.setLabel("left", "В срок, %")
        layout.addWidget(self.plot)

    def setMonths(self, months: list[tuple[int, str, float]]) -> None:
        self.plot.clear()
        if not months:
            self.plot.getAxis("bottom").setTicks([[]])
            return

        first, last = months[0][0], months[-1][0]
        shares = dict.fromkeys(range(first, last + 1), float("nan"))
        for position, _, share in months:
            shares[position] = share * 100
        self.plot.addItem(pg.PlotDataItem(list(shares), list(shares.values()), connect="finite",
                                          pen=pg.mkPen(self.LINE_COLOR, width=2), symbol="o", symbolSize=7,
                                          symbolBrush=self.LINE_COLOR, symbolPen=pg.mkPen("w")))
        for position, _, share in months:
            label = pg.TextItem(f"{share:.0%}", color=self.TEXT_COLOR, anchor=(0.5, 1.4))
            label.setFont(QFont("Arial", 9))
            label.setPos(position, share * 100)
            self.plot.addItem(label)

        step = -(-len(months) // self.MAX_TICKS)
        self.plot.getAxis("bottom").setTicks([[(position, name) for position, name, _ in months[::step]]])
        self.plot.setXRange(first - 0.5, last + 0.5, padding=0)
        self.plot.setYRange(0, 115, padding=0)
        self.plot.getAxis("left").setTicks([[(0, "0"), (50, "50"), (100, "100")]])


class ScrollThroughPlot(pg.PlotWidget):

    def wheelEvent(self, event) -> None:
        event.ignore()


class ExpenseBarAxis(MoneyAxis):

    def tickValues(self, minVal, maxVal, size):
        return super().tickValues(minVal, maxVal, size)[:2]


class ExpenseBarWidget(QWidget):

    rowClicked = Signal(int)
    rowRevealed = Signal(int)

    CURRENT_COLOR = "#2a78d6"
    PREVIOUS_COLOR = "#a2a199"
    OTHER_COLOR = "#7f7f7a"
    TEXT_COLOR = "#2b2b2b"
    GROWTH_COLOR = "#c0392b"
    DROP_COLOR = "#1e8a4c"
    DIMMED_ALPHA = 90
    ROW_PIXELS = 26
    COMPARE_ROW_PIXELS = 46
    EXTRA_PIXELS = 70
    PAGE_ROWS = 5

    def __init__(self, bg_color, parent: QWidget | None = None):
        super().__init__(parent)

        self.hints: list[str] = []
        self.cursor_row: int | None = None
        self.cursor_shown = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pg.setConfigOptions(
            background=bg_color,
            foreground=self.TEXT_COLOR
        )

        self.plot = ScrollThroughPlot(axisItems={"top": ExpenseBarAxis(orientation="top")})
        self.plot.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.plot.getPlotItem().hideButtons()
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.invertY(True)
        self.plot.hideAxis("bottom")
        self.plot.showAxis("top")
        self.plot.showGrid(x=True, alpha=0.2)
        self.plot.getAxis("left").setStyle(tickFont=QFont("Arial", 10))
        self.plot.getAxis("top").setStyle(tickFont=QFont("Arial", 10))
        layout.addWidget(self.plot)

        self.cursor_item = pg.BarGraphItem(x0=[], x1=[], y=[], height=1.0, brush=QColor(0, 0, 0, 0),
                                           pen=pg.mkPen(self.CURRENT_COLOR, width=2))

        self.plot.scene().sigMouseClicked.connect(self.onMouseClicked)
        self.plot.scene().sigMouseMoved.connect(self.onMouseMoved)

    def rowAt(self, y: float) -> int | None:
        index = round(y)
        if abs(y - index) > 0.5 or not 0 <= index < len(self.hints):
            return None
        return index

    @staticmethod
    def barColor(color: str, index: int, selected: int | None) -> QColor:
        bar_color = QColor(color)
        if selected is not None and index != selected:
            bar_color.setAlpha(ExpenseBarWidget.DIMMED_ALPHA)
        return bar_color

    def setRows(self, rows: list[StructureRow], labels: list[str], colors: list[str], compare: bool = False,
                selected: int | None = None, details: list[str] | None = None) -> None:
        self.plot.clear()
        self.hints = []
        count = len(rows)
        if self.cursor_row is not None and self.cursor_row >= count:
            self.cursor_row = None
        self.setMinimumHeight(count * (self.COMPARE_ROW_PIXELS if compare else self.ROW_PIXELS) + self.EXTRA_PIXELS)

        if not rows:
            self.plot.getAxis("left").setTicks([[]])
            self.plot.setXRange(0, 1, padding=0)
            self.plot.setYRange(-0.6, 0.6, padding=0)
            empty_label = pg.TextItem("Нет данных по выбранным условиям", color=self.TEXT_COLOR, anchor=(0.5, 0.5))
            empty_label.setFont(QFont("Arial", 11))
            empty_label.setPos(0.5, 0)
            self.plot.addItem(empty_label)
            return

        bar_height = 0.36 if compare else 0.6
        offset = 0.2 if compare else 0
        lows, highs, ys, brushes, values = [], [], [], [], []
        for index, row in enumerate(rows):
            bars = [(float(row.amount), index - offset, self.barColor(colors[index], index, selected))]
            if compare:
                bars.append((float(row.previous), index + offset, QColor(self.PREVIOUS_COLOR)))
            for value, y, brush in bars:
                lows.append(min(value, 0))
                highs.append(max(value, 0))
                ys.append(y)
                brushes.append(brush)
                values.append(value)
            self.hints.append(self.rowHint(row, labels[index], compare, details[index] if details else ""))
        self.plot.addItem(pg.BarGraphItem(x0=lows, x1=highs, y=ys, height=bar_height, brushes=brushes, pen=pg.mkPen(None)))

        for index, row in enumerate(rows):
            text = f"{int_strspace(round(row.amount))} ({float_strpercentage(float(row.share))})"
            change = change_share(row.amount, row.previous) if compare else None
            self.addValueLabel(text, max(float(row.amount), 0), index - offset, change=change)
            if compare and row.previous:
                self.addValueLabel(int_strspace(round(row.previous)), max(float(row.previous), 0), index + offset, dimmed=True)

        self.plot.getAxis("left").setTicks([list(enumerate(labels))])
        self.plot.setXRange(min(min(values), 0) * 1.15, max(max(values), 1) * (1.55 if compare else 1.35), padding=0)
        self.plot.setYRange(-0.6, count - 0.4, padding=0)
        self.plot.addItem(self.cursor_item)
        self.updateCursor()

    def addValueLabel(self, text: str, x: float, y: float, dimmed: bool = False, change: Decimal | None = None) -> None:
        if change is None:
            label = pg.TextItem(text, color="#6b6b66" if dimmed else self.TEXT_COLOR, anchor=(0, 0.5))
        else:
            arrow, color = ("▲", self.GROWTH_COLOR) if change > 0 else ("▼", self.DROP_COLOR) if change < 0 else ("", self.TEXT_COLOR)
            label = pg.TextItem(html=f"<span style='color:{self.TEXT_COLOR}'>{text}</span> "
                                     f"<span style='color:{color}'>{arrow} {float_strsignedpercentage(float(change))}</span>",
                                anchor=(0, 0.5))
        label.setFont(QFont("Arial", 9 if dimmed else 10))
        label.setPos(x, y)
        self.plot.addItem(label)

    @staticmethod
    def rowHint(row: StructureRow, label: str, compare: bool, details: str = "") -> str:
        hint = (f"{label}: {dec_strcommaspace(row.amount, add_rub=True)} ({float_strpercentage(float(row.share))}), "
                f"платежей: {int_strspace(row.count)}")
        if compare:
            hint += f"\nПредыдущий период: {dec_strcommaspace(row.previous, add_rub=True)}"
        if details:
            hint += f"\n{details}"
        return hint

    def cursorRow(self, scene_pos) -> int | None:
        view_box = self.plot.getViewBox()
        if not view_box.sceneBoundingRect().contains(scene_pos):
            return None
        return self.rowAt(view_box.mapSceneToView(scene_pos).y())

    def onMouseClicked(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = self.cursorRow(event.scenePos())
        if index is not None:
            self.cursor_row = index
            self.cursor_shown = False
            self.setFocus()
            self.rowClicked.emit(index)

    def onMouseMoved(self, scene_pos) -> None:
        index = self.cursorRow(scene_pos)
        self.plot.setCursor(Qt.CursorShape.ArrowCursor if index is None else Qt.CursorShape.PointingHandCursor)
        self.plot.setToolTip("" if index is None else self.hints[index])

    def updateCursor(self) -> None:
        if self.cursor_row is None or not self.cursor_shown or not self.hasFocus():
            self.cursor_item.setOpts(x0=[], x1=[], y=[])
            return
        low, high = self.plot.getViewBox().viewRange()[0]
        self.cursor_item.setOpts(x0=[low], x1=[high], y=[self.cursor_row], height=1.0)

    def rowPixel(self, index: int) -> int:
        scene_point = self.plot.getViewBox().mapViewToScene(QPointF(0, index))
        return self.plot.mapTo(self, self.plot.mapFromScene(scene_point)).y()

    def moveCursor(self, index: int) -> None:
        self.cursor_row = index
        self.cursor_shown = True
        self.updateCursor()
        self.rowRevealed.emit(self.rowPixel(index))
        plot_point = self.plot.mapFromScene(self.plot.getViewBox().mapViewToScene(QPointF(0, index)))
        QToolTip.showText(self.plot.mapToGlobal(QPoint(60, plot_point.y())), self.hints[index], self.plot)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        count = len(self.hints)
        key = event.key()
        steps = {Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1, Qt.Key.Key_PageUp: -self.PAGE_ROWS, Qt.Key.Key_PageDown: self.PAGE_ROWS}
        if not count or key not in (*steps, Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            super().keyPressEvent(event)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if self.cursor_row is not None:
                self.rowClicked.emit(self.cursor_row)
        elif self.cursor_row is None or key == Qt.Key.Key_Home:
            self.moveCursor(0)
        elif key == Qt.Key.Key_End:
            self.moveCursor(count - 1)
        else:
            self.moveCursor(min(max(self.cursor_row + steps[key], 0), count - 1))

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.updateCursor()

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.updateCursor()


class ExpenseMonthsWidget(QWidget):

    OTHER_COLOR = ExpenseBarWidget.OTHER_COLOR
    TEXT_COLOR = "#2b2b2b"
    MUTED_COLOR = "#9a9a94"
    MAX_TICKS = 18
    BAR_WIDTH = 0.7
    LEGEND_HINT = "Щелчок по названию скрывает или показывает категорию на графике"

    def __init__(self, bg_color, parent: QWidget | None = None):
        super().__init__(parent)

        self.bg_color = bg_color
        self.months: list[tuple[int, str]] = []
        self.series: list[tuple[str, str, dict[int, Decimal]]] = []
        self.hidden: set[str] = set()
        self.segments: list[list[tuple[str, float, float, float]]] = []
        self.nets: list[float] = []
        self.hover: tuple[int, str | None] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        pg.setConfigOptions(
            background=bg_color,
            foreground=self.TEXT_COLOR
        )

        self.plot = pg.PlotWidget(axisItems={"left": MoneyAxis(orientation="left")})
        self.plot.getPlotItem().hideButtons()
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(y=True, alpha=0.2)
        self.plot.getAxis("left").setStyle(tickFont=QFont("Arial", 9))
        self.plot.getAxis("bottom").setStyle(tickFont=QFont("Arial", 9))
        layout.addWidget(self.plot)

        self.highlight = pg.BarGraphItem(x=[], y0=[], y1=[], width=self.BAR_WIDTH, brush=QColor(0, 0, 0, 0),
                                         pen=pg.mkPen(self.TEXT_COLOR, width=2))

        self.legend = QLabel()
        self.legend.setWordWrap(True)
        self.legend.setToolTip(self.LEGEND_HINT)
        self.legend.linkActivated.connect(self.toggleSeries)
        layout.addWidget(self.legend)

        self.plot.scene().sigMouseMoved.connect(self.onMouseMoved)

    def setSeries(self, months: list[tuple[int, str]], series: list[tuple[str, str, dict[int, Decimal]]]) -> None:
        self.months = months
        self.series = [item for item in series if any(item[2].values())]
        self.redraw()

    def toggleSeries(self, link: str) -> None:
        name = self.series[int(link)][0]
        self.hidden ^= {name}
        self.redraw()

    def legendHtml(self) -> str:
        if len(self.series) < 2:
            return ""
        parts = []
        for position, (name, color, _) in enumerate(self.series):
            hidden = name in self.hidden
            text = f"<s>{escape(name)}</s>" if hidden else escape(name)
            parts.append(f"<a href='{position}' style='color:{self.MUTED_COLOR if hidden else self.TEXT_COLOR}; text-decoration:none'>"
                         f"<span style='color:{self.MUTED_COLOR if hidden else color}'>■</span> {text}</a>")
        return " &nbsp; ".join(parts)

    def redraw(self) -> None:
        self.plot.clear()
        self.segments = []
        self.nets = []
        self.hover = None
        self.plot.setToolTip("")
        self.legend.setText(self.legendHtml())
        if not self.months or not self.series:
            self.plot.getAxis("bottom").setTicks([[]])
            return

        months = self.months
        count = len(months)
        positive, negative = [0.0] * count, [0.0] * count
        self.segments = [[] for _ in range(count)]
        for name, color, values in self.series:
            if name in self.hidden:
                continue
            xs, bottoms, tops = [], [], []
            for index, (month, _) in enumerate(months):
                value = float(values.get(month, 0))
                if not value:
                    continue
                bases = positive if value > 0 else negative
                xs.append(index)
                bottoms.append(bases[index])
                bases[index] += value
                tops.append(bases[index])
                self.segments[index].append((name, min(bottoms[-1], tops[-1]), max(bottoms[-1], tops[-1]), value))
            if xs:
                self.plot.addItem(pg.BarGraphItem(x=xs, y0=bottoms, y1=tops, width=self.BAR_WIDTH, brush=color,
                                                  pen=pg.mkPen(self.bg_color, width=1)))

        self.nets = [positive[index] + negative[index] for index in range(count)]
        if count <= self.MAX_TICKS:
            for index in range(count):
                if positive[index] or negative[index]:
                    label = pg.TextItem(int_strspace(round(self.nets[index])), color=self.TEXT_COLOR, anchor=(0.5, 1))
                    label.setFont(QFont("Arial", 9))
                    label.setPos(index, positive[index])
                    self.plot.addItem(label)
        self.plot.addItem(self.highlight)
        self.highlight.setOpts(x=[], y0=[], y1=[])

        step = -(-count // self.MAX_TICKS)
        self.plot.getAxis("bottom").setTicks([[(index, months[index][1]) for index in range(0, count, step)]])
        self.plot.setXRange(-0.6, count - 0.4, padding=0)
        self.plot.setYRange(min(min(negative), 0) * 1.1, max(max(positive), 1) * 1.3, padding=0)

    def tooltipText(self, index: int, hovered: str | None) -> str:
        lines = [self.months[index][1], f"Итого: {int_strspace(round(self.nets[index]))}"]
        for name, _, _, value in reversed(self.segments[index]):
            lines.append(f"{'▶ ' if name == hovered else ''}{name}: {int_strspace(round(value))}")
        return "\n".join(lines)

    def onMouseMoved(self, scene_pos) -> None:
        view_box = self.plot.getViewBox()
        index = segment = None
        if self.segments and view_box.sceneBoundingRect().contains(scene_pos):
            point = view_box.mapSceneToView(scene_pos)
            if 0 <= round(point.x()) < len(self.segments) and abs(point.x() - round(point.x())) <= 0.5:
                index = round(point.x())
                if abs(point.x() - index) <= self.BAR_WIDTH / 2:
                    segment = next((item for item in self.segments[index] if item[1] <= point.y() <= item[2]), None)
        hover = None if index is None else (index, None if segment is None else segment[0])
        if hover == self.hover:
            return
        self.hover = hover
        if index is None:
            self.plot.setToolTip("")
        else:
            self.plot.setToolTip(self.tooltipText(index, hover[1]))
        if segment is None:
            self.highlight.setOpts(x=[], y0=[], y1=[])
        else:
            self.highlight.setOpts(x=[index], y0=[segment[1]], y1=[segment[2]])
