import shutil
from pathlib import Path

import lovely_logger as log
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QWidget

from gui.manualdialog import add_help_shortcut
from base.dbhandler import DBHandler
from base.paths import db_path, backup_dir
from base.sync import SyncError, fetch_master
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.syncmanager import create_sync_channel
from gui.syncsettingsdialog import SyncSettingsDialog


class RecoveryDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, db_handler: DBHandler, text: str = "Ошибка", cancel_available: bool = False,
                 offer_sync: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        add_help_shortcut(self, "P2-startup-data.html")

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
        if offer_sync:
            self.sync_button: QPushButton = QPushButton("Загрузить с сервера синхронизации")
            layout.addWidget(self.sync_button)
            self.sync_button.clicked.connect(self.try_fetch_from_server)
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
        if not self._save_corrupt_copy():
            Path(migrated_path).unlink(missing_ok=True)
            self._fail("Не удалось сохранить копию текущего файла базы данных перед заменой (для подробностей см. лог). "
                       "Файл не заменён")
            return
        switched: bool = self.db_handler.switch_db_files(migrated_path, close_current_connection=True)
        Path(migrated_path).unlink(missing_ok=True)
        if switched:
            self.accept()
        else:
            self._fail("При попытке заменить файл базы данных произошла ошибка (для подробностей см. лог)")

    @staticmethod
    def _save_corrupt_copy() -> bool:
        if not Path(db_path()).is_file():
            return True
        copy_path: Path = Path(backup_dir()) / ("db_corrupt_" + QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss") + ".db")
        try:
            copy_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(db_path(), copy_path)
        except OSError as e:
            log.x(f"Не удалось сохранить копию текущей базы данных в {copy_path}: {e}")
            return False
        return True

    def try_fetch_from_server(self) -> None:
        if SyncSettingsDialog(self.settings_handler, self).exec() != QDialog.DialogCode.Accepted:
            return
        if not self.settings_handler.sync_enabled():
            self._fail("Включите синхронизацию в настройках, чтобы загрузить базу с сервера")
            return
        channel = create_sync_channel(self.settings_handler)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            fetch_master(self.db_handler, channel)
        except SyncError as e:
            error: str = str(e)
        else:
            error = ""
        finally:
            QApplication.restoreOverrideCursor()
        if error:
            self._fail(f"Не удалось загрузить базу данных с сервера: {error}")
            return
        self.accept()

    def _fail(self, message: str) -> None:
        msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox(message, parent=self)
        msg_box.exec()
