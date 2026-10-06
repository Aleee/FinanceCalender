import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QStyle

from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.ui.exportsuccessdialog_ui import Ui_ExportSuccessDialog


class ExportSuccessDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExportSuccessDialog()
        self.ui.setupUi(self)

        self.path = Path(path).resolve()
        self.system = platform.system()

        self.ui.lbl_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation).pixmap(32, 32))
        self.ui.le_path.setText(str(self.path))
        self.ui.pb_openfile.clicked.connect(self.open_file)
        self.ui.pb_opendir.clicked.connect(self.open_dir)
        self.ui.pb_continue.clicked.connect(self.accept)
        self.setMaximumHeight(self.sizeHint().height())

    def open_file(self):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.path))):
            ErrorInfoMessageBox("Не удалось открыть файл", parent=self).exec()
            return
        self.accept()

    def open_dir(self):
        try:
            if self.system == "Windows":
                subprocess.Popen(f'explorer /select,"{self.path}"')
            elif self.system == "Darwin":
                subprocess.Popen(["open", "-R", str(self.path)])
            elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.path.parent))):
                raise OSError("нет приложения для открытия папки")
        except OSError as e:
            ErrorInfoMessageBox(f"Не удалось открыть папку:\n{e}", parent=self).exec()
            return
        self.accept()
