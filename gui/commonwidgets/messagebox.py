from PySide6.QtWidgets import QPushButton, QMessageBox


class YesNoMessagebox(QMessageBox):

    YES_RETURN_VALUE = 2
    NO_RETURN_VALUE = 3

    def __init__(self, text, parent=None):
        super(YesNoMessagebox, self).__init__(parent)

        self.setWindowTitle("Подтверждение")
        self.setText(text)
        self.setIcon(QMessageBox.Icon.Question)

        self.yes_button = QPushButton("Да", self)
        self.cancel_button = QPushButton("Отмена", self)

        self.addButton(self.yes_button, QMessageBox.ButtonRole.AcceptRole)
        self.addButton(self.cancel_button, QMessageBox.ButtonRole.RejectRole)


class ErrorInfoMessageBox(QMessageBox):

    def __init__(self, text, is_info: bool = False, parent=None):
        super(ErrorInfoMessageBox, self).__init__(parent)
        self.setWindowTitle("Информация" if is_info else "Ошибка")
        self.setText(text)
        self.setIcon(QMessageBox.Icon.Information if is_info else QMessageBox.Icon.Warning)

        self.ok_button = QPushButton("OK", self)
        self.addButton(self.ok_button, QMessageBox.ButtonRole.AcceptRole)
