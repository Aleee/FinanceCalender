from PySide6.QtCore import QByteArray, QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QStyle, QStyleOptionToolButton, QToolButton

SYNC_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-0.1 1.9 24.2 20.2" fill="none" stroke="{color}" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>'
    '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>'
)


def sync_icon_width(height: int) -> int:
    return round(height * 24.2 / 20.2)


def create_sync_icon(color: QColor, height: int = 36, scale: int = 3) -> QIcon:
    svg = SYNC_ICON_SVG.format(color=color.name())
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    image = QImage(sync_icon_width(height) * scale, height * scale, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(scale)
    return QIcon(pixmap)


class SyncToolButton(QToolButton):
    ICON_HEIGHT: int = 24
    ICON_MARGIN: int = 4
    ICON_GAP: int = 10

    TEXT_MARGIN: int = 4
    MIN_WIDTH_SAMPLE: str = "есть неотправленные ⚠"

    def text_offset(self) -> int:
        return self.ICON_MARGIN + sync_icon_width(self.ICON_HEIGHT) + self.ICON_GAP

    def sizeHint(self) -> QSize:
        metrics = self.fontMetrics()
        text_width: int = max(metrics.boundingRect(QRect(0, 0, 10000, 10000), Qt.AlignmentFlag.AlignLeft, self.text()).width(),
                              metrics.horizontalAdvance(self.MIN_WIDTH_SAMPLE))
        arrow_width: int = self.style().pixelMetric(QStyle.PixelMetric.PM_MenuButtonIndicator, None, self)
        return QSize(self.text_offset() + text_width + self.TEXT_MARGIN + arrow_width, super().sizeHint().height())

    def paintEvent(self, event) -> None:
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        option.text = ""
        option.icon = QIcon()
        painter = QPainter(self)
        self.style().drawComplexControl(QStyle.ComplexControl.CC_ToolButton, option, painter, self)
        menu_rect: QRect = self.style().subControlRect(QStyle.ComplexControl.CC_ToolButton, option, QStyle.SubControl.SC_ToolButtonMenu, self)
        pixmap: QPixmap = self.icon().pixmap(QSize(sync_icon_width(self.ICON_HEIGHT), self.ICON_HEIGHT))
        painter.drawPixmap(self.ICON_MARGIN, (self.height() - pixmap.height()) // 2, pixmap)
        painter.setPen(self.palette().buttonText().color())
        text_rect = QRect(self.text_offset(), 0, menu_rect.left() - self.text_offset(), self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
