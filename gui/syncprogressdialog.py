import time
from enum import IntEnum

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget


class SpinnerWidget(QWidget):
    SIZE = 14
    LINE_WIDTH = 2
    STEP_DEGREES = 12
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


class CheckMarkWidget(QWidget):
    SIZE = 14
    LINE_WIDTH = 2
    COLOR = QColor("#2e9e4f")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.COLOR, self.LINE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline([QPointF(2, 7.5), QPointF(5.5, 11), QPointF(12, 3.5)])


class CrossMarkWidget(QWidget):
    SIZE = 14
    LINE_WIDTH = 2
    COLOR = QColor("#d32f2f")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.COLOR, self.LINE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(3, 3), QPointF(11, 11))
        painter.drawLine(QPointF(11, 3), QPointF(3, 11))


class StageState(IntEnum):
    PENDING = 0
    ACTIVE = 1
    DONE = 2
    FAILED = 3


class StageRow(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.state = StageState.PENDING
        self.spinner = SpinnerWidget()
        self.icons = QStackedWidget(self)
        self.icons.setFixedSize(SpinnerWidget.SIZE, SpinnerWidget.SIZE)
        self.icons.addWidget(QWidget())
        self.icons.addWidget(self.spinner)
        self.icons.addWidget(CheckMarkWidget())
        self.icons.addWidget(CrossMarkWidget())
        self.label = QLabel(text, self)
        font = self.label.font()
        font.setPointSize(max(font.pointSize() - 1, 7))
        self.label.setFont(font)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.icons, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label, 1)
        self.set_state(StageState.PENDING)

    def set_state(self, state: StageState) -> None:
        self.state = state
        self.icons.setCurrentIndex(state)
        self.label.setEnabled(state != StageState.PENDING)
        if state == StageState.ACTIVE:
            self.spinner.start()
        else:
            self.spinner.stop()


class SyncProgressDialog(QDialog):
    SHOW_DELAY_MS = 350
    DONE_PAUSE_MS = 500

    def __init__(self, parent=None, text: str = "Синхронизация…", planned_stages: tuple[str, ...] = ()):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(300)

        self.lbl_text = QLabel(text, self)
        font = self.lbl_text.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        self.lbl_text.setFont(font)

        self.rows: dict[str, StageRow] = {}
        self.current_row: StageRow | None = None
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)
        layout.addWidget(self.lbl_text)
        layout.addLayout(self.rows_layout)

        for stage in planned_stages:
            self.add_row(stage)
        self.fit_size()

        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.show)

    def add_row(self, text: str) -> StageRow:
        row = StageRow(text, self)
        self.rows[text] = row
        self.rows_layout.addWidget(row)
        row.show()
        return row

    def fit_size(self) -> None:
        self.setFixedSize(self.sizeHint().expandedTo(self.minimumSize()))

    def set_stage(self, text: str) -> None:
        if self.current_row is not None and self.current_row.state == StageState.ACTIVE:
            self.current_row.set_state(StageState.DONE)
        row: StageRow | None = self.rows.get(text)
        if row is None or row.state != StageState.PENDING:
            row = self.add_row(text)
        row.set_state(StageState.ACTIVE)
        self.current_row = row
        self.layout().activate()
        self.fit_size()
        self.repaint()

    def show_stage_now(self, text: str) -> None:
        self.delay_timer.stop()
        self.set_stage(text)
        self.show()
        self.repaint()

    def complete(self, pause: bool) -> None:
        if self.current_row is not None and self.current_row.state == StageState.ACTIVE:
            self.current_row.set_state(StageState.DONE)
        if pause and self.isVisible():
            self.repaint()
            time.sleep(self.DONE_PAUSE_MS / 1000)

    def fail(self) -> None:
        if self.current_row is not None:
            self.current_row.set_state(StageState.FAILED)
        if self.isVisible():
            self.repaint()
            time.sleep(self.DONE_PAUSE_MS / 1000)

    def start(self) -> None:
        self.delay_timer.start(self.SHOW_DELAY_MS)

    def hide_for_question(self) -> None:
        self.delay_timer.stop()
        self.hide()

    def finish(self) -> None:
        self.delay_timer.stop()
        self.close()
        self.deleteLater()

    def reject(self) -> None:
        pass
