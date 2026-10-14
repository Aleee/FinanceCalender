from PySide6.QtWidgets import QMessageBox

import gui.netdiagdialog as dialogmod
from gui.netdiagdialog import NetDiagDialog


class RunningThread:
    def __init__(self):
        self.stop_reason = ""
        self.outcome = "остановлено на 26-й секунде: причина"

    def isRunning(self):
        return True

    def request_stop(self, reason):
        self.stop_reason = reason


def test_start_disabled_options_follow_token(qapp):
    without_token = NetDiagDialog("", "app:/")
    assert not without_token.chb_send.isEnabled()
    assert not without_token.chb_send.isChecked()
    with_token = NetDiagDialog("abc", "app:/")
    assert with_token.chb_send.isChecked()


def test_report_ready_enables_show_button(qapp, tmp_path):
    dialog = NetDiagDialog("abc", "app:/")
    dialog.on_report_ready(str(tmp_path / "netdiag.zip"))
    dialog.on_finished()
    assert dialog.pb_folder.isEnabled()
    assert dialog.pb_start.isEnabled()
    assert not dialog.pb_stop.isEnabled()


def test_closing_running_dialog_asks_before_stopping(qapp, monkeypatch):
    dialog = NetDiagDialog("abc", "app:/")
    dialog.thread = RunningThread()
    monkeypatch.setattr(dialogmod.QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No)
    dialog.reject()
    assert not dialog.thread.stop_reason
    monkeypatch.setattr(dialogmod.QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    dialog.reject()
    assert "закрыто окно" in dialog.thread.stop_reason


def test_finish_shows_outcome(qapp):
    dialog = NetDiagDialog("abc", "app:/")
    dialog.thread = RunningThread()
    dialog.on_finished()
    assert "остановлено на 26-й секунде" in dialog.lbl_status.text()
    assert "остановлено на 26-й секунде" in dialog.te_log.toPlainText()
