from pathlib import Path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QCheckBox, QLineEdit, QPushButton, QHBoxLayout, QSpinBox,
                               QDialogButtonBox, QFileDialog, QWidget)

from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler


class SyncSettingsDialog(QDialog):
    def __init__(self, settings_handler: SettingsHandler, parent: QWidget | None = None):
        super().__init__(parent)

        self.settings_handler: SettingsHandler = settings_handler

        self.setWindowTitle("Синхронизация")
        layout: QVBoxLayout = QVBoxLayout(self)
        form: QFormLayout = QFormLayout()
        layout.addLayout(form)

        self.chb_enabled: QCheckBox = QCheckBox("Включить синхронизацию")
        form.addRow(self.chb_enabled)

        self.le_folder: QLineEdit = QLineEdit(settings_handler.sync_folder())
        self.pb_folder: QPushButton = QPushButton("Выбрать")
        folder_layout: QHBoxLayout = QHBoxLayout()
        folder_layout.addWidget(self.le_folder)
        folder_layout.addWidget(self.pb_folder)
        form.addRow("Папка обмена:", folder_layout)

        self.le_author: QLineEdit = QLineEdit(settings_handler.sync_author())
        form.addRow("Имя пользователя:", self.le_author)

        self.spb_interval: QSpinBox = QSpinBox()
        self.spb_interval.setRange(1, 60)
        self.spb_interval.setSuffix(" мин")
        form.addRow("Проверять мастер каждые:", self.spb_interval)

        self.spb_keepdays: QSpinBox = QSpinBox()
        self.spb_keepdays.setRange(1, 365)
        self.spb_keepdays.setSuffix(" дн")
        form.addRow("Хранить копии мастера:", self.spb_keepdays)

        self.chb_enabled.setChecked(settings_handler.sync_enabled())
        self.spb_interval.setValue(settings_handler.sync_interval_minutes())
        self.spb_keepdays.setValue(settings_handler.sync_backup_keep_days())

        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        layout.addWidget(buttons)

        self.pb_folder.clicked.connect(self.choose_folder)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)

    def choose_folder(self) -> None:
        path: str = QFileDialog.getExistingDirectory(self, "Выберите папку", self.le_folder.text())
        if path:
            self.le_folder.setText(path)

    def save_and_accept(self) -> None:
        if self.chb_enabled.isChecked():
            if not Path(self.le_folder.text()).is_dir():
                ErrorInfoMessageBox("Папка обмена не указана или не существует", parent=self).exec()
                return
            if not self.le_author.text().strip():
                ErrorInfoMessageBox("Укажите имя пользователя: оно записывается при отправке изменений", parent=self).exec()
                return
        settings = self.settings_handler.settings
        settings.setValue("Sync/enabled", int(self.chb_enabled.isChecked()))
        self.settings_handler.set_sync_folder(self.le_folder.text())
        settings.setValue("Sync/author", self.le_author.text().strip())
        settings.setValue("Sync/interval", self.spb_interval.value())
        settings.setValue("Sync/backupkeepdays", self.spb_keepdays.value())
        self.accept()
