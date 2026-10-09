from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

SYNC_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>'
    '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>'
)


def create_sync_icon(color: QColor, size: int = 12, scale: int = 2) -> QIcon:
    svg = SYNC_ICON_SVG.format(color=color.name())
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(scale)
    return QIcon(pixmap)
