from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCalendarWidget, QDialog, QDialogButtonBox, QVBoxLayout


class DatePickerDialog(QDialog):

    def __init__(self, initial_date: QDate, min_date: QDate, max_date: QDate, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Выбор даты")

        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(min_date)
        self.calendar.setMaximumDate(max_date)
        self.calendar.setSelectedDate(initial_date)
        layout.addWidget(self.calendar)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_date(self) -> QDate:
        return self.calendar.selectedDate()
