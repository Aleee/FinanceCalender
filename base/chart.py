from PySide6 import QtCore
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


from datetime import date

class MoneyAxis(pg.AxisItem):

    def tickStrings(self, values, scale, spacing):
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

    def __init__(self, *args, first_day=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_day = first_day

    def tickStrings(self, values, scale, spacing):

        from datetime import timedelta

        if self.first_day is None:
            return [str(int(v)) for v in values]

        return [
            (self.first_day + timedelta(days=int(v))).strftime("%d.%m")
            for v in values
        ]

class DebtChartWidget(QWidget):

    def __init__(self, bg_color, parent=None):
        super().__init__(parent)

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
        vb.wheelEvent = lambda ev: ev.ignore()

        layout.addWidget(self.plot)

        self.right_vb = pg.ViewBox()
        self.right_axis.linkToView(self.right_vb)
        self.plot.scene().addItem(self.right_vb)
        self.plot.getViewBox().sigResized.connect(self.updateViews)
        self.right_vb.setXLink(self.plot.getViewBox())
        #self.plot.getPlotItem().layout.addItem(self.right_vb, 2, 2)

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

        self.vLine = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#666", width=1)
        )

        self.plot.addItem(self.vLine)

        # self.plot.setAxisItems({
        #     "left": self.plot.getAxis("left"),
        #     "bottom": self.plot.getAxis("bottom"),
        #     "right": self.right_axis
        # })

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
        self.plot.getPlotItem().hideButtons()
        vb.wheelEvent = lambda ev: ev.accept()
        vb.setMouseMode(pg.ViewBox.PanMode)



    def buildSeries(self, smoothing: int = 10):

        x = list(range(len(self.timeline)))

        total = [float(d.total) for d in self.timeline]
        overdue = [float(d.overdue) for d in self.timeline]
        share = [(o / t * 100) if t else 0 for t, o in zip(total, overdue)]

        smooth_total = self.moving_average_centered(total, smoothing)
        smooth_overdue = self.moving_average_centered(overdue, smoothing)

        smooth_share_scaled = self.moving_average_centered(share, smoothing)

        return x, total, overdue, smooth_share_scaled, smooth_total, smooth_overdue

    def setTimeline(self, timeline, smoothing: int = 10):

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

        all_values = [
                         float(d.total) for d in self.timeline
                     ] + [
                         float(d.overdue) for d in self.timeline
                     ]

        y_max = max(all_values)

        # чтобы при всех нулях был нормальный масштаб
        if y_max <= 0:
            y_max = 1000

        self.plot.setYRange(0, y_max * 1.05, padding=0)

        self.right_vb.setYRange(0, 100, padding=0)
        self.right_vb.enableAutoRange(y=False)


    def onMouseMoved(self, pos):

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

        # данные
        total = f"{float(item.total):,.2f}"
        overdue = f"{float(item.overdue):,.2f}"

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
    def moving_average_centered(values, window=10):
        result = []

        n = len(values)

        for i in range(n):
            start = max(0, i - window)
            end = min(n, i + window + 1)

            window_vals = values[start:end]

            result.append(sum(window_vals) / len(window_vals))

        return result

    def updateViews(self):
        self.right_vb.setGeometry(self.plot.getViewBox().sceneBoundingRect())

    def eventFilter(self, obj, event):

        if event.type() == QtCore.QEvent.GraphicsSceneHoverMove:
            self.onMouseMoved(event.scenePos())
            return False

        if event.type() == QtCore.QEvent.GraphicsSceneLeave:
            self.hideHover()
            return False

        return super().eventFilter(obj, event)

    def hideHover(self):
        self.tooltip.hide()
        self.vLine.hide()
        self.activePoint.hide()
        self.overduePoint.hide()