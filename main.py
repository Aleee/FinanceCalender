import os
import sys
import cProfile
import lovely_logger as log
import faulthandler
from PySide6.QtGui import QCloseEvent

from PySide6.QtWidgets import QApplication

from gui.mainwindow import MainWindow


class App(QApplication):

    # def __init__(self, pr):
    def __init__(self):
        super().__init__(sys.argv)

        self.setStyle('fusion')

        self.window: MainWindow = MainWindow()
        self.window.show()
        # self.window.settings_handler.apply_settings()
        # self.window.allow_proxymodels_sortfliter(True)
        # if not self.window.settings_handler.settings.value("Autosave/interval"):
        #     self.window.open_settings_dialog(reject_possible=False)



def close(pr):
    pr.disable()
    pr.dump_stats('profile_results.pstat')

def main():
    # faulthandler.enable(sys.stderr, all_threads=True)
    # pr = cProfile.Profile()
    # pr.enable()

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Безопасно перенаправляем системный stderr в отдельный файл крашей ядра
    if sys.stderr is None or sys.stderr.name == '<stderr>':
        # Режим 'a' дописывает файл, buffering=1 сразу сохраняет текст на диск
        sys.stderr = open(os.path.join(base_dir, "sys_errors.log"), "a", encoding="utf-8", buffering=1)

    if sys.stdout is None or sys.stdout.name == '<stdout>':
        sys.stdout = open(os.path.join(base_dir, "sys_output.log"), "a", encoding="utf-8", buffering=1)

    log.init("log.log", level=log.DEBUG)

    # application: App = App(pr)
    # application.aboutToQuit.connect(lambda: close(pr))

    application: App = App()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
