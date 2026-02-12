from PySide6 import QtCore
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog

from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler


class RecoveryDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, db_handler: DBHandler, text: str = "Ошибка", cancel_available: bool = False, parent=None):
        super().__init__(parent)

        self.settings_handler = settings_handler
        self.db_handler = db_handler
        self.cancel_available = cancel_available

        self.setWindowTitle("Восстановление базы данных")
        layout = QVBoxLayout(self)
        label = QLabel(text)
        layout.addWidget(label)
        self.button = QPushButton("Выбрать")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.try_recover)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

    def try_recover(self):
        path = QFileDialog.getOpenFileName(self, "Выберите файл", self.settings_handler.settings.value("Recovery/path", ""), "SQLite3 Database (*.db)")[0]
        if not path:
            if self.cancel_available:
                self.reject()
            return False
        if self.db_handler.check_db_file_integrity(path):
            if self.db_handler.switch_db_files(path):
                self.accept()
            else:
                msg_box = ErrorInfoMessageBox("При попытке заменить файл базы данных произошла ошибка (для подробностей см. лог)", parent=self)
                msg_box.exec()
                if self.cancel_available:
                    self.reject()
        else:
            msg_box = ErrorInfoMessageBox("При проверке файла базы данных обнаружились ошибки (для подробностей см. лог). Выберите другой файл", parent=self)
            msg_box.exec()
            if self.cancel_available:
                self.reject()
        return False
