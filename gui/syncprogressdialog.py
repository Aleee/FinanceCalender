from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class SpinnerWidget(QWidget):
    SIZE = 36
    LINE_WIDTH = 4
    STEP_DEGREES = 10
    INTERVAL_MS = 25
    ARC_SPAN_DEGREES = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle: int = 0
        self.setFixedSize(self.SIZE, self.SIZE)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)

    def start(self) -> None:
        self.timer.start(self.INTERVAL_MS)

    def stop(self) -> None:
        self.timer.stop()

    def rotate(self) -> None:
        self.angle = (self.angle - self.STEP_DEGREES) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        half: float = self.LINE_WIDTH / 2
        rect = QRectF(half, half, self.SIZE - self.LINE_WIDTH, self.SIZE - self.LINE_WIDTH)
        accent: QColor = self.palette().highlight().color()
        track = QColor(accent)
        track.setAlpha(45)
        pen = QPen(track, self.LINE_WIDTH)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        pen.setColor(accent)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, self.angle * 16, self.ARC_SPAN_DEGREES * 16)


class SyncProgressDialog(QDialog):
    SHOW_DELAY_MS = 350

    def __init__(self, parent=None, text: str = "Синхронизация…", details: str = "Обмен данными с мастером"):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(300)

        self.spinner = SpinnerWidget(self)
        self.lbl_text = QLabel(text, self)
        font = self.lbl_text.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        self.lbl_text.setFont(font)
        self.lbl_details = QLabel(details, self)
        self.lbl_details.setEnabled(False)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(self.lbl_text)
        text_layout.addWidget(self.lbl_details)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)
        layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(text_layout, 1)

        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.show)

    def start(self) -> None:
        self.delay_timer.start(self.SHOW_DELAY_MS)

    def finish(self) -> None:
        self.delay_timer.stop()
        self.close()
        self.deleteLater()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.spinner.start()

    def hideEvent(self, event) -> None:
        self.spinner.stop()
        super().hideEvent(event)

    def reject(self) -> None:
        pass
