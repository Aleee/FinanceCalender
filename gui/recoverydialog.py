from pathlib import Path

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QWidget

from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler


class RecoveryDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, db_handler: DBHandler, text: str = "Ошибка", cancel_available: bool = False,
                 parent: QWidget | None = None):
        super().__init__(parent)

        self.settings_handler: SettingsHandler = settings_handler
        self.db_handler: DBHandler = db_handler
        self.cancel_available: bool = cancel_available

        self.setWindowTitle("Восстановление базы данных")
        layout: QVBoxLayout = QVBoxLayout(self)
        label: QLabel = QLabel(text)
        layout.addWidget(label)
        self.button: QPushButton = QPushButton("Выбрать")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.try_recover)
        if not cancel_available:
            self.exit_button: QPushButton = QPushButton("Выйти")
            layout.addWidget(self.exit_button)
            self.exit_button.clicked.connect(self.reject)

    def try_recover(self) -> None:
        path: str = QFileDialog.getOpenFileName(self, "Выберите файл", self.settings_handler.settings.value("Recovery/path", ""),
                                                "SQLite3 Database (*.db)")[0]
        if not path:
            return
        migrated_path: str | None = self.db_handler.make_migrated_copy(path)
        if migrated_path is None:
            self._fail("При проверке файла базы данных обнаружились ошибки (для подробностей см. лог). Выберите другой файл")
            return
        switched: bool = self.db_handler.switch_db_files(migrated_path, close_current_connection=True)
        Path(migrated_path).unlink(missing_ok=True)
        if switched:
            self.accept()
        else:
            self._fail("При попытке заменить файл базы данных произошла ошибка (для подробностей см. лог)")

    def _fail(self, message: str) -> None:
        msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox(message, parent=self)
        msg_box.exec()
