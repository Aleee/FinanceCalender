# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'exportsuccessdialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)

class Ui_ExportSuccessDialog(object):
    def setupUi(self, ExportSuccessDialog):
        if not ExportSuccessDialog.objectName():
            ExportSuccessDialog.setObjectName(u"ExportSuccessDialog")
        ExportSuccessDialog.resize(519, 103)
        self.gridLayout = QGridLayout(ExportSuccessDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(ExportSuccessDialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.line = QFrame(ExportSuccessDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 2, 0, 1, 1)

        self.le_path = QLineEdit(ExportSuccessDialog)
        self.le_path.setObjectName(u"le_path")
        self.le_path.setReadOnly(True)

        self.gridLayout.addWidget(self.le_path, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pb_openfile = QPushButton(ExportSuccessDialog)
        self.pb_openfile.setObjectName(u"pb_openfile")
        self.pb_openfile.setMinimumSize(QSize(120, 0))
        self.pb_openfile.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout.addWidget(self.pb_openfile)

        self.pb_opendir = QPushButton(ExportSuccessDialog)
        self.pb_opendir.setObjectName(u"pb_opendir")
        self.pb_opendir.setMinimumSize(QSize(120, 0))
        self.pb_opendir.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout.addWidget(self.pb_opendir)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_continue = QPushButton(ExportSuccessDialog)
        self.pb_continue.setObjectName(u"pb_continue")
        self.pb_continue.setMinimumSize(QSize(120, 0))
        self.pb_continue.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout.addWidget(self.pb_continue)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)


        self.retranslateUi(ExportSuccessDialog)

        QMetaObject.connectSlotsByName(ExportSuccessDialog)
    # setupUi

    def retranslateUi(self, ExportSuccessDialog):
        ExportSuccessDialog.setWindowTitle(QCoreApplication.translate("ExportSuccessDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d", None))
        self.label.setText(QCoreApplication.translate("ExportSuccessDialog", u"\u0424\u0430\u0439\u043b \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u044d\u043a\u0441\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d!", None))
        self.le_path.setText("")
        self.pb_openfile.setText(QCoreApplication.translate("ExportSuccessDialog", u" \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0444\u0430\u0439\u043b ", None))
        self.pb_opendir.setText(QCoreApplication.translate("ExportSuccessDialog", u" \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043f\u043a\u0443 ", None))
        self.pb_continue.setText(QCoreApplication.translate("ExportSuccessDialog", u"\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0438\u0442\u044c", None))
    # retranslateUi

