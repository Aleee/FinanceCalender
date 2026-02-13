import resources_rc
from PySide6 import QtCore
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel


class LoadingDialog(QDialog):

    load_completed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(260)
        self.setFixedHeight(70)
        self.layout = QHBoxLayout()
        self.label1 = QLabel(self)
        self.movie = QMovie(u":/gif/designer/gif/load.gif")
        self.label1.setMovie(self.movie)
        self.movie.start()
        self.layout.addWidget(self.label1)
        self.label2 = QLabel(self)
        self.layout.addWidget(self.label2)
        self.layout.addStretch()
        self.setLayout(self.layout)

        self.setStyleSheet(f"QWidget {{ font-size: 9pt;}}background-color: rgb(255, 255, 255);")

        QTimer.singleShot(1, lambda: self.label2.setText("  Загрузка базы данных"))
        QTimer.singleShot(1500, lambda: self.label2.setText("  Создание резервной копии"))
        QTimer.singleShot(2000, lambda: self.label2.setText("  Удаление старых резервных копий"))
        QTimer.singleShot(2500, self.accept)
        QTimer.singleShot(2500, self.load_completed.emit)
