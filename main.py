import sys
import cProfile
import lovely_logger as log

from PySide6.QtWidgets import QApplication

from gui.loadingdialog import LoadingDialog
from gui.mainwindow import MainWindow


class App(QApplication):

    def __init__(self):
        super().__init__(sys.argv)

        self.setStyle('fusion')

        self.loading_dialog = LoadingDialog()
        self.loading_dialog.show()
        self.window: MainWindow = MainWindow()
        self.loading_dialog.load_completed.connect(self.window.show)
        self.window.settings_handler.apply_settings()
        if not self.window.settings_handler.settings.value("Autosave/interval"):
            print("called")
            self.window.open_settings_dialog(reject_possible=False)


# pr = cProfile.Profile()
# pr.enable()
# log.init("log.log")
# app = App()
# app.exec()
# pr.disable()
# pr.dump_stats('profile_results.pstat')


def main():
    log.init("log.log")
    application: App = App()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
