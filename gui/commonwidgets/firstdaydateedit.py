from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit


class FirstDayDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super(FirstDayDateEdit, self).__init__(parent)
        self.dateChanged.connect(self.force_firstday)

    def force_firstday(self, date: QDate) -> None:
        if date.day() != 1:
            self.blockSignals(True)
            self.setDate(QDate(date.year(), date.month(), 1))
            self.blockSignals(False)
