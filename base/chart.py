from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

from datetime import date, timedelta
from decimal import Decimal

from base.discipline import BUCKET_NAMES, DelayBucket, DisciplineStats
from base.formatting import dec_strcommaspace, int_strspace

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
