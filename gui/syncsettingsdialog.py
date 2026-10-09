from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QFormLayout, QCheckBox, QComboBox, QDateEdit, QLabel,
                               QLineEdit, QPushButton, QHBoxLayout, QSpinBox, QDialogButtonBox, QFileDialog, QWidget)

from base.sync import SyncError
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.syncmanager import create_yandex_channel

TOKEN_HINT = ("Токен выдаётся один раз для общего аккаунта: oauth.yandex.ru, право cloud_api:disk.app_folder. "
              "Дату окончания можно вычислить из expires_in (в секундах) в том же адресе, где выдан токен.")


class SyncSettingsDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, parent: QWidget | None = None):
        super().__init__(parent)

        self.settings_handler: SettingsHandler = settings_handler

        self.setWindowTitle("Синхронизация")
        layout: QVBoxLayout = QVBoxLayout(self)
        self.form: QFormLayout = QFormLayout()
        layout.addLayout(self.form)

        self.chb_enabled: QCheckBox = QCheckBox("Включить синхронизацию")
        self.form.addRow(self.chb_enabled)

        self.cmb_channel: QComboBox = QComboBox()
        self.cmb_channel.addItem("Яндекс.Диск", "yandex")
        self.cmb_channel.addItem("Папка", "folder")
        self.form.addRow("Способ обмена:", self.cmb_channel)

        self.le_token: QLineEdit = QLineEdit(settings_handler.sync_token())
        self.le_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.form.addRow("Токен Яндекса:", self.le_token)

        self.de_tokenexpires: QDateEdit = QDateEdit()
        self.de_tokenexpires.setCalendarPopup(True)
        self.de_tokenexpires.setDisplayFormat("dd.MM.yyyy")
        self.de_tokenexpires.setMinimumDate(QDate(2000, 1, 1))
        self.de_tokenexpires.setSpecialValueText("не указан")
        expires: QDate = QDate.fromString(settings_handler.sync_token_expires(), Qt.DateFormat.ISODate)
        self.de_tokenexpires.setDate(expires if expires.isValid() else self.de_tokenexpires.minimumDate())
        self.form.addRow("Токен действует до:", self.de_tokenexpires)

        self.le_diskfolder: QLineEdit = QLineEdit(settings_handler.sync_disk_folder())
        self.form.addRow("Папка на Диске:", self.le_diskfolder)

        self.pb_check: QPushButton = QPushButton("Проверить подключение")
        self.form.addRow(self.pb_check)

        self.lb_hint: QLabel = QLabel(TOKEN_HINT)
        self.lb_hint.setWordWrap(True)
        self.form.addRow(self.lb_hint)

        self.le_folder: QLineEdit = QLineEdit(settings_handler.sync_folder())
        self.pb_folder: QPushButton = QPushButton("Выбрать")
        self.folder_layout: QHBoxLayout = QHBoxLayout()
        self.folder_layout.addWidget(self.le_folder)
        self.folder_layout.addWidget(self.pb_folder)
        self.form.addRow("Папка обмена:", self.folder_layout)

        self.le_author: QLineEdit = QLineEdit(settings_handler.sync_author())
        self.form.addRow("Имя пользователя:", self.le_author)

        self.spb_interval: QSpinBox = QSpinBox()
        self.spb_interval.setRange(1, 60)
        self.spb_interval.setSuffix(" мин")
        self.form.addRow("Проверять мастер каждые:", self.spb_interval)

        self.spb_keepdays: QSpinBox = QSpinBox()
        self.spb_keepdays.setRange(1, 365)
        self.spb_keepdays.setSuffix(" дн")
        self.form.addRow("Хранить копии мастера:", self.spb_keepdays)

        self.chb_enabled.setChecked(settings_handler.sync_enabled())
        self.cmb_channel.setCurrentIndex(max(self.cmb_channel.findData(settings_handler.sync_channel_type()), 0))
        self.spb_interval.setValue(settings_handler.sync_interval_minutes())
        self.spb_keepdays.setValue(settings_handler.sync_backup_keep_days())

        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        layout.addWidget(buttons)

        self.cmb_channel.currentIndexChanged.connect(self.update_channel_rows)
        self.pb_folder.clicked.connect(self.choose_folder)
        self.pb_check.clicked.connect(self.check_connection)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        self.update_channel_rows()

    def is_yandex_selected(self) -> bool:
        return self.cmb_channel.currentData() == "yandex"

    def update_channel_rows(self) -> None:
        is_yandex: bool = self.is_yandex_selected()
        for row in (self.le_token, self.de_tokenexpires, self.le_diskfolder, self.pb_check, self.lb_hint):
            self.form.setRowVisible(row, is_yandex)
        self.form.setRowVisible(self.folder_layout, not is_yandex)
        self.adjustSize()

    def choose_folder(self) -> None:
        path: str = QFileDialog.getExistingDirectory(self, "Выберите папку", self.le_folder.text())
        if path:
            self.le_folder.setText(path)

    def check_connection(self) -> None:
        token: str = self.le_token.text().strip()
        if not token:
            ErrorInfoMessageBox("Укажите токен", parent=self).exec()
            return
        channel = create_yandex_channel(token, self.le_diskfolder.text())
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
        if self.chb_enabled.isChecked():
            if self.is_yandex_selected():
                if not self.le_token.text().strip():
                    ErrorInfoMessageBox("Укажите токен Яндекса", parent=self).exec()
                    return
            elif not Path(self.le_folder.text()).is_dir():
                ErrorInfoMessageBox("Папка обмена не указана или не существует", parent=self).exec()
                return
            if not self.le_author.text().strip():
                ErrorInfoMessageBox("Укажите имя пользователя: оно записывается при отправке изменений", parent=self).exec()
                return
        settings = self.settings_handler.settings
        settings.setValue("Sync/enabled", int(self.chb_enabled.isChecked()))
        settings.setValue("Sync/channel", self.cmb_channel.currentData())
        settings.setValue("Sync/token", self.le_token.text().strip())
        expires: QDate = self.de_tokenexpires.date()
        settings.setValue("Sync/tokenexpires",
                          "" if expires == self.de_tokenexpires.minimumDate() else expires.toString(Qt.DateFormat.ISODate))
        settings.setValue("Sync/diskfolder", self.le_diskfolder.text().strip() or "app:/")
        self.settings_handler.set_sync_folder(self.le_folder.text())
        settings.setValue("Sync/author", self.le_author.text().strip())
        settings.setValue("Sync/interval", self.spb_interval.value())
        settings.setValue("Sync/backupkeepdays", self.spb_keepdays.value())
        self.accept()
