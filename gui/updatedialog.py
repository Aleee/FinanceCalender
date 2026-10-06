from typing import Optional

import lovely_logger as log
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QPushButton, QWidget

from base.backup import save_backup
from base.dbhandler import DBHandler
from base.updater import UpdateDownloader, UpdateError, UpdateInfo, is_frozen, launch_updater
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.settings import SettingsHandler


class UpdateAvailableMessageBox(QMessageBox):

    def __init__(self, info: UpdateInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Обновление")
        self.setIcon(QMessageBox.Icon.Information)
        self.setText(f"Доступно обновление {info.version}")
        notes: str = info.notes.strip() or "Описание не указано."
        self.setInformativeText(f"Что нового:\n{notes}\n\nПрограмма будет закрыта и запущена снова. "
                                f"Перед обновлением будет создана резервная копия базы данных.")

        self.update_button: QPushButton = QPushButton("Обновить", self)
        self.later_button: QPushButton = QPushButton("Позже", self)
        self.addButton(self.update_button, QMessageBox.ButtonRole.AcceptRole)
        self.addButton(self.later_button, QMessageBox.ButtonRole.RejectRole)
        self.setEscapeButton(self.later_button)


class UpdateController(QObject):

    def __init__(self, window: QWidget, settings_handler: SettingsHandler, db_handler: DBHandler,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.window: QWidget = window
        self.settings_handler: SettingsHandler = settings_handler
        self.db_handler: DBHandler = db_handler
        self.downloader: UpdateDownloader = UpdateDownloader(self)
        self.downloader.progress.connect(self.on_progress)
        self.downloader.ready.connect(self.on_ready)
        self.downloader.failed.connect(self.on_failed)
        self.progress_dialog: Optional[QProgressDialog] = None

    def offer_update(self, info: UpdateInfo) -> None:
        if QApplication.activeModalWidget() is not None:
            log.i(f"Обновление {info.version} не предложено: открыто модальное окно")
            return
        message_box = UpdateAvailableMessageBox(info, self.window)
        message_box.exec()
        if message_box.clickedButton() is message_box.update_button:
            self.install(info)

    def install(self, info: UpdateInfo) -> None:
        if not is_frozen():
            ErrorInfoMessageBox("Обновление работает только в собранной версии программы.", parent=self.window).exec()
            return
        if not save_backup(self.settings_handler, self.db_handler).isValid():
            question = YesNoMessagebox("Не удалось создать резервную копию базы данных. "
                                       "Продолжить обновление без неё?", self.window)
            question.exec()
            if question.clickedButton() is not question.yes_button:
                return
        self.show_progress_dialog()
        self.downloader.start(info)

    def show_progress_dialog(self) -> None:
        self.progress_dialog = QProgressDialog("Скачивание обновления…", "Отмена", 0, 0, self.window)
        self.progress_dialog.setWindowTitle("Обновление")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.canceled.connect(self.downloader.cancel)
        self.progress_dialog.show()

    def hide_progress_dialog(self) -> None:
        if self.progress_dialog is not None:
            self.progress_dialog.canceled.disconnect()
            self.progress_dialog.hide()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

    def on_progress(self, received: int, total: int) -> None:
        if self.progress_dialog is None or total <= 0:
            return
        self.progress_dialog.setMaximum(total)
        self.progress_dialog.setValue(received)
        if received >= total:
            self.progress_dialog.setLabelText("Проверка и распаковка файлов…")
            self.progress_dialog.setCancelButton(None)
            QApplication.processEvents()

    def on_failed(self, message: str) -> None:
        self.hide_progress_dialog()
        ErrorInfoMessageBox(message, parent=self.window).exec()

    def on_ready(self, new_dir: str) -> None:
        self.hide_progress_dialog()
        try:
            launch_updater()
        except UpdateError as e:
            ErrorInfoMessageBox(str(e), parent=self.window).exec()
            return
        self.window.close()
