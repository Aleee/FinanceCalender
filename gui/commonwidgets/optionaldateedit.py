from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QDateEdit, QLineEdit, QStyle


class OptionalDateEdit(QDateEdit):
    CLEAR_BUTTON_WIDTH = 24

    def __init__(self, parent=None):
        super().__init__(parent)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton)
        self.clear_action = self.lineEdit().addAction(icon, QLineEdit.ActionPosition.TrailingPosition)
        self.clear_action.triggered.connect(self.clear_date)
        self.dateChanged.connect(self.update_clear_action)
        self.update_clear_action()

    def sizeHint(self) -> QSize:
        size = super().sizeHint()
        return QSize(size.width() + self.CLEAR_BUTTON_WIDTH, size.height())

    def minimumSizeHint(self) -> QSize:
        size = super().minimumSizeHint()
        return QSize(size.width() + self.CLEAR_BUTTON_WIDTH, size.height())

    def update_clear_action(self) -> None:
        self.clear_action.setVisible(self.value() is not None)

    def setMinimumDate(self, min_date: QDate) -> None:
        super().setMinimumDate(min_date)
        self.update_clear_action()

    def value(self) -> QDate | None:
        return None if self.date() == self.minimumDate() else self.date()

    def clear_date(self) -> None:
        self.setDate(self.minimumDate())
        self.update_clear_action()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.clear_date()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.value() is None and self.calendarWidget() is not None:
            today = QDate.currentDate()
            self.calendarWidget().setCurrentPage(today.year(), today.month())
