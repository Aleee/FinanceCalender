from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QLayout, QWidget

from base.sync import SyncError
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.syncmanager import create_yandex_channel
from gui.ui.syncsettingsdialog_ui import Ui_SyncSettingsDialog


class SyncSettingsDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, parent: QWidget | None = None):
        super().__init__(parent)
        self.ui = Ui_SyncSettingsDialog()
        self.ui.setupUi(self)
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.settings_handler: SettingsHandler = settings_handler

        self.ui.cmb_channel.setItemData(0, "yandex")
        self.ui.cmb_channel.setItemData(1, "folder")

        self.ui.le_token.setText(settings_handler.sync_token())
        expires: QDate = QDate.fromString(settings_handler.sync_token_expires(), Qt.DateFormat.ISODate)
        self.ui.de_tokenexpires.setDate(expires if expires.isValid() else self.ui.de_tokenexpires.minimumDate())
        self.ui.le_diskfolder.setText(settings_handler.sync_disk_folder())
        self.ui.le_folder.setText(settings_handler.sync_folder())
        self.ui.le_author.setText(settings_handler.sync_author())
        self.ui.chb_enabled.setChecked(settings_handler.sync_enabled())
        self.ui.cmb_channel.setCurrentIndex(max(self.ui.cmb_channel.findData(settings_handler.sync_channel_type()), 0))
        self.ui.spb_interval.setValue(settings_handler.sync_interval_minutes())
        self.ui.spb_keepdays.setValue(settings_handler.sync_backup_keep_days())

        self.ui.chb_enabled.toggled.connect(self.update_enabled_state)
        self.ui.cmb_channel.currentIndexChanged.connect(self.update_channel_rows)
        self.ui.pb_folder.clicked.connect(self.choose_folder)
        self.ui.pb_check.clicked.connect(self.check_connection)
        self.ui.pb_ok.clicked.connect(self.save_and_accept)
        self.ui.pb_cancel.clicked.connect(self.reject)
        self.update_channel_rows()
        self.update_enabled_state()

    def is_yandex_selected(self) -> bool:
        return self.ui.cmb_channel.currentData() == "yandex"

    def update_channel_rows(self) -> None:
        is_yandex: bool = self.is_yandex_selected()
        for row in (self.ui.le_token, self.ui.de_tokenexpires, self.ui.le_diskfolder, self.ui.pb_check):
            self.ui.fl_main.setRowVisible(row, is_yandex)
        self.ui.fl_main.setRowVisible(self.ui.hl_folder, not is_yandex)
        self.adjustSize()

    def update_enabled_state(self) -> None:
        enabled: bool = self.ui.chb_enabled.isChecked()
        for index in range(self.ui.fl_main.count()):
            widget = self.ui.fl_main.itemAt(index).widget()
            if widget is not None and widget is not self.ui.chb_enabled:
                widget.setEnabled(enabled)
        for widget in (self.ui.le_folder, self.ui.pb_folder):
            widget.setEnabled(enabled)

    def choose_folder(self) -> None:
        path: str = QFileDialog.getExistingDirectory(self, "Выберите папку", self.ui.le_folder.text())
        if path:
            self.ui.le_folder.setText(path)

    def check_connection(self) -> None:
        token: str = self.ui.le_token.text().strip()
        if not token:
            ErrorInfoMessageBox("Укажите токен", parent=self).exec()
            return
        channel = create_yandex_channel(token, self.ui.le_diskfolder.text())
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            channel.check_connection()
        except SyncError as e:
            error: str = str(e)
        else:
            error = ""
        finally:
            QApplication.restoreOverrideCursor()
        if error:
            ErrorInfoMessageBox(f"Подключиться не удалось: {error}", parent=self).exec()
        else:
            ErrorInfoMessageBox("Подключение работает", is_info=True, parent=self).exec()

    def save_and_accept(self) -> None:
        if self.ui.chb_enabled.isChecked():
            if self.is_yandex_selected():
                if not self.ui.le_token.text().strip():
                    ErrorInfoMessageBox("Укажите токен Яндекса", parent=self).exec()
                    return
            elif not Path(self.ui.le_folder.text()).is_dir():
                ErrorInfoMessageBox("Папка обмена не указана или не существует", parent=self).exec()
                return
            if not self.ui.le_author.text().strip():
                ErrorInfoMessageBox("Укажите имя пользователя: оно записывается при отправке изменений", parent=self).exec()
                return
        settings = self.settings_handler.settings
        settings.setValue("Sync/enabled", int(self.ui.chb_enabled.isChecked()))
        settings.setValue("Sync/channel", self.ui.cmb_channel.currentData())
        settings.setValue("Sync/token", self.ui.le_token.text().strip())
        expires: QDate = self.ui.de_tokenexpires.date()
        settings.setValue("Sync/tokenexpires",
                          "" if expires == self.ui.de_tokenexpires.minimumDate() else expires.toString(Qt.DateFormat.ISODate))
        settings.setValue("Sync/diskfolder", self.ui.le_diskfolder.text().strip() or "app:/")
        self.settings_handler.set_sync_folder(self.ui.le_folder.text())
        settings.setValue("Sync/author", self.ui.le_author.text().strip())
        settings.setValue("Sync/interval", self.ui.spb_interval.value())
        settings.setValue("Sync/backupkeepdays", self.ui.spb_keepdays.value())
        self.accept()
