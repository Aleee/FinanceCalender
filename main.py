import os
import sys
import cProfile
import lovely_logger as log
import PySide6
from PySide6.QtCore import QLockFile, Qt, QTranslator
from PySide6.QtNetwork import QNetworkProxyFactory

from PySide6.QtWidgets import QApplication, QMessageBox

from base.edition import is_viewer
from base.paths import data_dir, logs_dir
from base.updater import UpdateChecker
from base.version import APP_VERSION
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.commonwidgets.neutralarrowstyle import NeutralArrowStyle
from gui.mainwindow import MainWindow
from gui.updatedialog import UpdateController


class App(QApplication):

    # def __init__(self, pr):
    def __init__(self):
        super().__init__(sys.argv)

        self.qt_translator: QTranslator = QTranslator(self)
        if self.qt_translator.load("qtbase_ru", os.path.join(os.path.dirname(PySide6.__file__), "translations")):
            self.installTranslator(self.qt_translator)

        QNetworkProxyFactory.setUseSystemConfiguration(True)
        self.styleHints().setColorScheme(Qt.ColorScheme.Light)

        self.app_version = APP_VERSION

        self.setStyle(NeutralArrowStyle())

        self.window: MainWindow = MainWindow()
        self.window.show()

        self.update_checker: UpdateChecker = UpdateChecker(self)
        self.update_controller: UpdateController = UpdateController(self.window, self.window.settings_handler,
                                                                    self.window.db_handler, self)
        self.update_checker.update_available.connect(self.update_controller.offer_update)
        self.update_checker.check_finished.connect(
            lambda: self.window.set_update_status(self.update_checker.last_check_status))
        self.update_checker.check()

def close(pr):
    pr.disable()
    pr.dump_stats('profile_results.pstat')

def trim_log_file(path: str, max_bytes: int = 1024 * 1024, keep_bytes: int = 256 * 1024) -> None:
    try:
        if os.path.getsize(path) <= max_bytes:
            return
        with open(path, "rb") as file:
            file.seek(-keep_bytes, os.SEEK_END)
            tail = file.read()
        tail = tail[tail.find(b"\n") + 1:]
        with open(path, "wb") as file:
            file.write(tail)
    except OSError:
        pass


def install_error_window_hook() -> None:
    logging_hook = sys.excepthook
    is_window_shown: list[bool] = [False]

    def show_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
        logging_hook(exc_type, exc_value, exc_traceback)
        if not issubclass(exc_type, Exception) or is_window_shown[0] or QApplication.instance() is None:
            return
        is_window_shown[0] = True
        try:
            ErrorInfoMessageBox("Произошла непредвиденная ошибка (подробности в логе).").exec()
        finally:
            is_window_shown[0] = False

    sys.excepthook = show_uncaught_exception


def main():
    # pr = cProfile.Profile()
    # pr.enable()

    #TEMP
    if sys.platform == 'win32' and not getattr(sys, 'frozen', False):
        os.environ['PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openssl') + os.pathsep + \
                             os.environ['PATH']

    try:
        logs_folder = logs_dir()
    except OSError as e:
        QApplication(sys.argv)
        QMessageBox.critical(None, "Платежный календарь",
                             f"Не удалось создать папку с данными программы:\n{e}\n\n"
                             f"Проверьте права на запись в эту папку.")
        sys.exit(1)
    if sys.stderr is None or sys.stderr.name == '<stderr>':
        errors_path = os.path.join(logs_folder, "sys_errors.log")
        trim_log_file(errors_path)
        sys.stderr = open(errors_path, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None or sys.stdout.name == '<stdout>':
        output_path = os.path.join(logs_folder, "sys_output.log")
        trim_log_file(output_path)
        sys.stdout = open(output_path, "a", encoding="utf-8", buffering=1)
    log.init(os.path.join(logs_folder, "log.log"), to_console=False, level=log.DEBUG, max_kb=2048, max_files=2)
    install_error_window_hook()

    lock_file: QLockFile = QLockFile(os.path.join(data_dir(), ".lock"))
    if not is_viewer() and not lock_file.tryLock(0):
        QApplication(sys.argv)
        QMessageBox.warning(None, "Платежный календарь", "Программа уже запущена. Закройте другое окно программы и повторите запуск.")
        sys.exit(1)

    # application: App = App(pr)
    # application.aboutToQuit.connect(lambda: close(pr))

    application: App = App()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
