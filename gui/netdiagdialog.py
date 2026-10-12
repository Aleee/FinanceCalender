from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout, QWidget)

from base.netdiag import DiagConfig, DiagThread


class NetDiagDialog(QDialog):
    PROFILES = (("Быстрая (2–4 минуты)", 0),
                ("С наблюдением (+10 минут)", 600),
                ("Длительная (+30 минут)", 1800),
                ("Очень длительная (+60 минут)", 3600))

    def __init__(self, token: str, disk_folder: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Диагностика сети")
        self.resize(560, 460)
        self.token: str = token
        self.disk_folder: str = disk_folder
        self.thread: DiagThread | None = None
        self.report_path: str = ""

        self.lbl_info = QLabel("Программа проверит связь с серверами Яндекса и сохранит отчёт в архив. "
                               "В отчёте есть внешний IP-адрес и название провайдера, токен скрывается. "
                               "Пришлите архив разработчику.", self)
        self.lbl_info.setWordWrap(True)
        self.cmb_profile = QComboBox(self)
        for text, seconds in self.PROFILES:
            self.cmb_profile.addItem(text, seconds)
        self.chb_send = QCheckBox("Проверить отправку тестовых файлов на Диск (нужен токен)", self)
        self.chb_send.setChecked(bool(token))
        self.chb_send.setEnabled(bool(token))
        self.te_log = QPlainTextEdit(self)
        self.te_log.setReadOnly(True)
        self.pb_start = QPushButton("Запустить", self)
        self.pb_stop = QPushButton("Остановить", self)
        self.pb_stop.setEnabled(False)
        self.pb_folder = QPushButton("Показать отчёт", self)
        self.pb_folder.setEnabled(False)
        self.pb_close = QPushButton("Закрыть", self)

        form = QFormLayout()
        form.addRow("Режим:", self.cmb_profile)
        buttons = QHBoxLayout()
        buttons.addWidget(self.pb_start)
        buttons.addWidget(self.pb_stop)
        buttons.addWidget(self.pb_folder)
        buttons.addStretch()
        buttons.addWidget(self.pb_close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_info)
        layout.addLayout(form)
        layout.addWidget(self.chb_send)
        layout.addWidget(self.te_log)
        layout.addLayout(buttons)

        self.pb_start.clicked.connect(self.start)
        self.pb_stop.clicked.connect(self.stop)
        self.pb_folder.clicked.connect(self.show_report)
        self.pb_close.clicked.connect(self.reject)

    def start(self) -> None:
        config = DiagConfig(self.token, self.disk_folder, self.chb_send.isChecked(), self.cmb_profile.currentData())
        self.report_path = ""
        self.te_log.clear()
        self.set_running(True)
        self.thread = DiagThread(config, self)
        self.thread.progress.connect(self.te_log.appendPlainText)
        self.thread.report_ready.connect(self.on_report_ready)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def stop(self) -> None:
        self.pb_stop.setEnabled(False)
        self.te_log.appendPlainText("Останавливаем, дождитесь завершения текущей проверки…")
        self.thread.requestInterruption()

    def set_running(self, running: bool) -> None:
        self.pb_start.setEnabled(not running)
        self.pb_stop.setEnabled(running)
        self.cmb_profile.setEnabled(not running)
        self.chb_send.setEnabled(not running and bool(self.token))
        self.pb_folder.setEnabled(not running and bool(self.report_path))

    def on_report_ready(self, path: str) -> None:
        self.report_path = path
        self.te_log.appendPlainText(f"Готово. Отчёт сохранён: {path}")

    def on_finished(self) -> None:
        self.set_running(False)

    def show_report(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.report_path).parent)))

    def reject(self) -> None:
        if self.thread is not None and self.thread.isRunning():
            self.stop()
            return
        super().reject()
