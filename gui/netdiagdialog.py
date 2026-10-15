import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox,
                               QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from base.netdiag import DiagConfig, DiagThread
from gui.manualdialog import add_help_shortcut


class NetDiagDialog(QDialog):
    PROFILES = (("Быстрая (2–4 минуты)", 0),
                ("С наблюдением (+10 минут)", 600),
                ("Длительная (+30 минут)", 1800),
                ("Очень длительная (+60 минут)", 3600))

    def __init__(self, token: str, disk_folder: str, parent: QWidget | None = None):
        super().__init__(parent)
        add_help_shortcut(self, "14-sync.html")
        self.setWindowTitle("Диагностика сети")
        self.resize(560, 460)
        self.token: str = token
        self.disk_folder: str = disk_folder
        self.thread: DiagThread | None = None
        self.report_path: str = ""
        self.started: float = 0.0
        self.current_step: str = ""

        self.lbl_info = QLabel("Программа проверит связь с серверами Яндекса и сохранит отчёт в архив. "
                               "В отчёте есть внешний IP-адрес и название провайдера, токен скрывается. "
                               "Окно можно свернуть, проверка продолжится; не закрывайте его и не отправляйте "
                               "компьютер в сон до конца. Пришлите архив разработчику.", self)
        self.lbl_info.setWordWrap(True)
        self.cmb_profile = QComboBox(self)
        for text, seconds in self.PROFILES:
            self.cmb_profile.addItem(text, seconds)
        self.chb_send = QCheckBox("Проверить отправку тестовых файлов на Диск (нужен токен)", self)
        self.chb_send.setChecked(bool(token))
        self.chb_send.setEnabled(bool(token))
        self.lbl_status = QLabel(self)
        self.lbl_status.setWordWrap(True)
        self.te_log = QPlainTextEdit(self)
        self.te_log.setReadOnly(True)
        self.pb_start = QPushButton("Запустить", self)
        self.pb_stop = QPushButton("Остановить", self)
        self.pb_stop.setEnabled(False)
        self.pb_folder = QPushButton("Показать отчёт", self)
        self.pb_folder.setEnabled(False)
        self.pb_close = QPushButton("Закрыть", self)
        for button in (self.pb_start, self.pb_stop, self.pb_folder, self.pb_close):
            button.setAutoDefault(False)

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
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.te_log)
        layout.addLayout(buttons)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_status)
        self.pb_start.clicked.connect(self.start)
        self.pb_stop.clicked.connect(lambda: self.stop("нажата кнопка «Остановить»"))
        self.pb_folder.clicked.connect(self.show_report)
        self.pb_close.clicked.connect(self.reject)

    def start(self) -> None:
        config = DiagConfig(self.token, self.disk_folder, self.chb_send.isChecked(), self.cmb_profile.currentData())
        self.report_path = ""
        self.te_log.clear()
        self.started = time.monotonic()
        self.current_step = ""
        self.set_running(True)
        self.thread = DiagThread(config, self)
        self.thread.progress.connect(self.on_progress)
        self.thread.report_ready.connect(self.on_report_ready)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()
        self.timer.start()
        self.update_status()

    def stop(self, reason: str) -> None:
        self.pb_stop.setEnabled(False)
        self.add_log_line(f"Остановка запрошена ({reason}), дождитесь завершения текущей проверки…")
        self.thread.request_stop(reason)

    def add_log_line(self, text: str) -> None:
        self.te_log.appendPlainText(f"{datetime.now():%H:%M:%S}  {text}")

    def update_status(self) -> None:
        elapsed = int(time.monotonic() - self.started)
        self.lbl_status.setText(f"Идёт {elapsed // 60}:{elapsed % 60:02d}. Сейчас: {self.current_step or 'запуск'}")

    def set_running(self, running: bool) -> None:
        self.pb_start.setEnabled(not running)
        self.pb_stop.setEnabled(running)
        self.cmb_profile.setEnabled(not running)
        self.chb_send.setEnabled(not running and bool(self.token))
        self.pb_folder.setEnabled(not running and bool(self.report_path))

    def on_progress(self, text: str) -> None:
        self.current_step = text
        self.add_log_line(text)

    def on_report_ready(self, path: str) -> None:
        self.report_path = path
        self.add_log_line(f"Готово. Отчёт сохранён: {path}")

    def on_finished(self) -> None:
        self.timer.stop()
        self.set_running(False)
        if self.thread is not None:
            self.lbl_status.setText(f"Завершено: {self.thread.outcome}")
            self.add_log_line(f"Завершено: {self.thread.outcome}")

    def show_report(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.report_path).parent)))

    def reject(self) -> None:
        if self.thread is not None and self.thread.isRunning():
            if not self.thread.stop_reason and QMessageBox.question(
                    self, "Диагностика сети",
                    "Диагностика ещё идёт. Остановить её и сохранить отчёт на этом месте?"
            ) == QMessageBox.StandardButton.Yes:
                self.stop("закрыто окно (Esc, крестик или «Закрыть»)")
            return
        super().reject()
