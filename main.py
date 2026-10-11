import os
import sys
import cProfile
import lovely_logger as log
from PySide6.QtNetwork import QNetworkProxyFactory

from PySide6.QtWidgets import QApplication, QMessageBox

from base.paths import logs_dir
from base.updater import UpdateChecker
from base.version import APP_VERSION
from gui.commonwidgets.neutralarrowstyle import NeutralArrowStyle
from gui.mainwindow import MainWindow
from gui.updatedialog import UpdateController


class App(QApplication):

    # def __init__(self, pr):
    def __init__(self):
        super().__init__(sys.argv)


        QNetworkProxyFactory.setUseSystemConfiguration(True)

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
        sys.stderr = open(os.path.join(logs_folder, "sys_errors.log"), "a", encoding="utf-8", buffering=1)
    if sys.stdout is None or sys.stdout.name == '<stdout>':
        sys.stdout = open(os.path.join(logs_folder, "sys_output.log"), "a", encoding="utf-8", buffering=1)
    log.init(os.path.join(logs_folder, "log.log"), level=log.DEBUG)

    # application: App = App(pr)
    # application.aboutToQuit.connect(lambda: close(pr))

    application: App = App()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
