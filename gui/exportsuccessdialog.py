import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QDialog

from gui.ui.exportsuccessdialog_ui import Ui_ExportSuccessDialog


class ExportSuccessDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super(ExportSuccessDialog, self).__init__(parent)
        self.ui = Ui_ExportSuccessDialog()
        self.ui.setupUi(self)

        self.path: Path = Path(path).resolve()
        self.system: str = platform.system()

        self.ui.le_path.setText(str(self.path))
        self.ui.pb_openfile.clicked.connect(self.open_file)
        self.ui.pb_opendir.clicked.connect(self.open_dir)
        self.ui.pb_continue.clicked.connect(lambda: self.accept())

    def open_file(self):
        if self.system == "Windows":
            os.startfile(self.path)
        elif self.system == "Darwin":
            subprocess.run(["open", str(self.path)])
        self.accept()

    def open_dir(self):
        if self.system == "Windows":
            os.startfile(self.path.parent)
        elif self.system == "Darwin":
            subprocess.run(["open", "-R", str(self.path)])
        self.accept()
