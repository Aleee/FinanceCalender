import re
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMainWindow, QPushButton, QMessageBox, QWidget

from base.netdiagreport import read_tail
from base.paths import logs_dir

LOG_TAIL_BYTES = 16384
LOG_TAIL_LINES = 30


def show_status_message(widget: QWidget, text: str, timeout_ms: int = 5000) -> None:
    parent = widget
    while parent is not None and not isinstance(parent, QMainWindow):
        parent = parent.parentWidget()
    if parent is None:
        ErrorInfoMessageBox(text, is_info=True, parent=widget).exec()
        return
    parent.statusBar().showMessage(text, timeout_ms)


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


def read_log_tail() -> str:
    text = read_tail(Path(logs_dir()) / "log.log", LOG_TAIL_BYTES)
    return "\n".join(text.splitlines()[-LOG_TAIL_LINES:])


class ErrorInfoMessageBox(QMessageBox):

    LOG_MENTION = re.compile(r"\bлог[еа]?\b", re.IGNORECASE)
    FAILURE_MENTION = re.compile(r"не удалось|ошибк", re.IGNORECASE)

    def __init__(self, text, is_info: bool = False, parent=None, details: str | None = None):
        super(ErrorInfoMessageBox, self).__init__(parent)
        has_log_mention: bool = bool(self.LOG_MENTION.search(text))
        is_failure: bool = has_log_mention or bool(self.FAILURE_MENTION.search(text))
        self.setWindowTitle("Информация" if is_info else "Ошибка")
        self.setText(text)
        if is_info:
            self.setIcon(QMessageBox.Icon.Information)
        else:
            self.setIcon(QMessageBox.Icon.Critical if is_failure else QMessageBox.Icon.Warning)

        self.ok_button: QPushButton = QPushButton("OK", self)
        self.addButton(self.ok_button, QMessageBox.ButtonRole.AcceptRole)

        if not is_info and has_log_mention:
            self.logs_button: QPushButton = QPushButton("Открыть папку логов", self)
            self.addButton(self.logs_button, QMessageBox.ButtonRole.ActionRole)
            self.logs_button.clicked.connect(self.open_logs_folder)
            details = details or read_log_tail()
        if details:
            self.setDetailedText(details)

    @staticmethod
    def open_logs_folder() -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(logs_dir()))
