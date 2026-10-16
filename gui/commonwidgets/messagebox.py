from PySide6.QtWidgets import QPushButton, QMessageBox


class YesNoMessagebox(QMessageBox):

    YES_RETURN_VALUE: int = 2
    NO_RETURN_VALUE: int = 3

    def __init__(self, text: str, parent=None, cancel_by_default: bool = False):
        super(YesNoMessagebox, self).__init__(parent)

        self.setWindowTitle("Подтверждение")
        self.setText(text)
        self.setIcon(QMessageBox.Icon.Question)

        self.yes_button: QPushButton = QPushButton("Да", self)
        self.cancel_button: QPushButton = QPushButton("Отмена", self)

        self.addButton(self.yes_button, QMessageBox.ButtonRole.AcceptRole)
        self.addButton(self.cancel_button, QMessageBox.ButtonRole.RejectRole)
        self.setEscapeButton(self.cancel_button)
        if cancel_by_default:
            self.setDefaultButton(self.cancel_button)


class ErrorInfoMessageBox(QMessageBox):

    def __init__(self, text, is_info: bool = False, parent=None):
        super(ErrorInfoMessageBox, self).__init__(parent)
        self.setWindowTitle("Информация" if is_info else "Ошибка")
        self.setText(text)
        self.setIcon(QMessageBox.Icon.Information if is_info else QMessageBox.Icon.Warning)

        self.ok_button: QPushButton = QPushButton("OK", self)
        self.addButton(self.ok_button, QMessageBox.ButtonRole.AcceptRole)
