import time
from collections.abc import Callable
from enum import IntEnum

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QLayout, QProgressBar, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from base.sync import STAGE_CONNECT, STAGE_DOWNLOAD

STAGE_RECONNECT = "Переподключение к общей базе"


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
        self.text = text
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
        self.label.ensurePolished()
        self.label.setMinimumWidth(self.label.fontMetrics().horizontalAdvance(f"{text} (попытка 9/9)"))

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(3)
        self.bar.setStyleSheet("QProgressBar { border: none; border-radius: 1px; background-color: #e3e8ee; }"
                               "QProgressBar::chunk { border-radius: 1px; background-color: #2c5c8a; }")
        self.bar.setVisible(False)

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(self.icons, 0, Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(self.label, 1)
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(SpinnerWidget.SIZE + row_layout.spacing(), 0, 0, 0)
        bar_layout.addWidget(self.bar)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addLayout(row_layout)
        layout.addLayout(bar_layout)
        self.set_state(StageState.PENDING)

    def set_state(self, state: StageState) -> None:
        self.state = state
        self.icons.setCurrentIndex(state)
        self.label.setEnabled(state != StageState.PENDING)
        if state == StageState.ACTIVE:
            self.spinner.start()
        else:
            self.spinner.stop()
        if state != StageState.ACTIVE:
            self.bar.setVisible(False)
            self.layout().invalidate()
        if state == StageState.DONE:
            self.label.setText(self.text)

    def set_attempt(self, attempt: int, total: int) -> None:
        self.label.setText(f"{self.text} (попытка {attempt}/{total})")
        self.label.setMinimumWidth(max(self.label.minimumWidth(), self.label.sizeHint().width()))
        self.bar.setValue(0)

    def set_progress(self, done: int, total: int) -> bool:
        if total <= 0:
            return False
        shown_before: bool = self.bar.isVisible()
        self.bar.setValue(min(done * 100 // total, 100))
        self.bar.setVisible(True)
        self.layout().invalidate()
        return not shown_before


class SyncProgressDialog(QDialog):
    SHOW_DELAY_MS = 350
    QUIET_SHOW_DELAY_MS = 3000
    DONE_PAUSE_MS = 500

    def __init__(self, parent=None, text: str = "Синхронизация…", planned_stages: tuple[str, ...] = (), quiet: bool = False):
        super().__init__(parent)
        self.quiet = quiet
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

        self.cancel_handler: Callable[[], None] | None = None
        self.wait_cursor_released: bool = False
        self.btn_cancel = QPushButton("Отмена", self)
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFlat(True)
        self.btn_cancel.setStyleSheet("QPushButton { border: none; border-radius: 4px; padding: 2px 8px; color: #2c5c8a; font-weight: 600; }"
                                      "QPushButton:hover { background-color: #e8f0f8; }"
                                      "QPushButton:pressed { background-color: #d5e3f2; }"
                                      "QPushButton:disabled { color: #b0b0b0; background-color: transparent; }")
        retain_policy = self.btn_cancel.sizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)
        self.btn_cancel.setSizePolicy(retain_policy)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.lbl_text, 1)
        title_layout.addWidget(self.btn_cancel, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_layout)
        layout.addLayout(self.rows_layout)

        for stage in planned_stages:
            self.add_row(stage)
        self.fit_size()

        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.show_unless_minimized)

    def is_parent_minimized(self) -> bool:
        return self.quiet and self.parent() is not None and self.parent().isMinimized()

    def show_unless_minimized(self) -> None:
        if not self.is_parent_minimized():
            self.show()

    def add_row(self, text: str) -> StageRow:
        row = StageRow(text, self)
        self.rows[text] = row
        self.rows_layout.addWidget(row)
        row.show()
        return row

    def fit_size(self) -> None:
        self.layout().activate()

    def set_stage(self, text: str) -> None:
        if self.current_row is not None and self.current_row.state == StageState.ACTIVE:
            self.current_row.set_state(StageState.DONE)
        row: StageRow | None = self.rows.get(text)
        if row is not None and row.state != StageState.PENDING and text == STAGE_CONNECT:
            text = STAGE_RECONNECT
            row = self.rows.get(text)
        if row is None or row.state != StageState.PENDING:
            row = self.add_row(text)
        row.set_state(StageState.ACTIVE)
        self.current_row = row
        self.fit_size()
        if self.quiet and text == STAGE_DOWNLOAD:
            self.delay_timer.stop()
            self.show_unless_minimized()
        self.repaint()

    def set_attempt(self, attempt: int, total: int) -> None:
        if self.current_row is not None:
            self.current_row.set_attempt(attempt, total)
            self.fit_size()
            self.repaint()

    def set_progress(self, done: int, total: int) -> None:
        if self.current_row is not None and self.current_row.set_progress(done, total):
            self.fit_size()

    def set_cancel_handler(self, handler: Callable[[], None] | None) -> None:
        self.cancel_handler = handler
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setVisible(handler is not None)
        self.fit_size()

    def show_waiting(self, cancellable: bool) -> None:
        if self.quiet and (self.delay_timer.isActive() or self.is_parent_minimized()):
            return
        self.btn_cancel.setEnabled(cancellable)
        self.delay_timer.stop()
        self.show()
        self.repaint()
        if cancellable and not self.wait_cursor_released:
            QApplication.restoreOverrideCursor()
            self.wait_cursor_released = True

    def end_waiting(self) -> None:
        if self.wait_cursor_released:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.wait_cursor_released = False

    def on_cancel_clicked(self) -> None:
        if self.cancel_handler is not None:
            self.btn_cancel.setEnabled(False)
            self.cancel_handler()

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
        self.delay_timer.start(self.QUIET_SHOW_DELAY_MS if self.quiet else self.SHOW_DELAY_MS)

    def hide_for_question(self) -> None:
        self.delay_timer.stop()
        self.hide()

    def finish(self) -> None:
        self.delay_timer.stop()
        self.close()
        self.deleteLater()

    def reject(self) -> None:
        self.btn_cancel.click()
