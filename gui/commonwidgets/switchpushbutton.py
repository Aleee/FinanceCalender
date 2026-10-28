from PySide6.QtCore import QEvent, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QPushButton


class SwitchPushButton(QPushButton):

    DEFAULT_STYLE: str = "border-width: 0px; text-align: left; color: black;"
    HIDDENFILTER_STYLE: str = "border-width: 0px; text-align: left; color: #ff3d3d;"
    INACTIVE_STYLE: str = "border-width: 0px; text-align: left; color: #9a9a9a;"
    DEFAULT_COLOR: str = "black"
    HIDDENFILTER_COLOR: str = "#ff3d3d"
    INACTIVE_COLOR: str = "#9a9a9a"
    switch_status_changed = Signal(bool)

    def __init__(self, parent=None):
        super(SwitchPushButton, self).__init__(parent)
        self.switchstate: bool = True
        self.inactive: bool = False
        self.label_off: str = ""
        self.label_on: str = ""
        self.arrow_color: str = self.DEFAULT_COLOR

        self.clicked.connect(lambda: self.set_switch_state(not self.switchstate))

    def set_button_label(self, label_off: str, label_on: str) -> None:
        self.label_off = label_off
        self.label_on = label_on

    def switch_state(self) -> bool:
        return self.switchstate

    def set_switch_state(self, switch_state: bool) -> None:
        self.switchstate = switch_state
        self.setText(self.label_on if self.switchstate else self.label_off)
        self.update_arrow()
        self.switch_status_changed.emit(switch_state)

    def change_style_on_hiding_activefilter(self, switch_state: bool, filter_active: bool) -> None:
        if self.inactive:
            self.setStyleSheet(self.INACTIVE_STYLE)
            self.arrow_color = self.INACTIVE_COLOR
        elif not switch_state and filter_active:
            self.setStyleSheet(self.HIDDENFILTER_STYLE)
            self.arrow_color = self.HIDDENFILTER_COLOR
        else:
            self.setStyleSheet(self.DEFAULT_STYLE)
            self.arrow_color = self.DEFAULT_COLOR
        self.update_arrow()

    def update_arrow(self) -> None:
        side: int = self.fontMetrics().ascent()
        ratio: float = self.devicePixelRatioF()
        pixmap = QPixmap(round(side * ratio), round(side * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        if self.switchstate:
            points = [(0.1, 0.25), (0.9, 0.25), (0.5, 0.8)]
        else:
            points = [(0.25, 0.1), (0.8, 0.5), (0.25, 0.9)]
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.arrow_color))
        painter.drawPolygon(QPolygonF([QPointF(x * side, y * side) for x, y in points]))
        painter.end()
        self.setIconSize(QSize(side, side))
        self.setIcon(QIcon(pixmap))

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            if self.iconSize().height() != self.fontMetrics().ascent():
                self.update_arrow()
