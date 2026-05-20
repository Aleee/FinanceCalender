import sys
import cProfile
import lovely_logger as log

from PySide6.QtWidgets import QApplication

from gui.mainwindow import MainWindow


class App(QApplication):

    def __init__(self, pr):
        super().__init__(sys.argv)

        self.setStyle('fusion')

        self.window: MainWindow = MainWindow()
        self.window.show()
        # self.window.settings_handler.apply_settings()
        # self.window.allow_proxymodels_sortfliter(True)
        # if not self.window.settings_handler.settings.value("Autosave/interval"):
        #     self.window.open_settings_dialog(reject_possible=False)
        # pr.disable()
        # pr.dump_stats('profile_results.pstat')


def main():
    pr = cProfile.Profile()
    # pr.enable()
    log.init("log.log", level=log.DEBUG)
    application: App = App(pr)
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
