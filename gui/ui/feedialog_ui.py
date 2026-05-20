# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'feedialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QPushButton,
    QSizePolicy, QTextEdit, QWidget)

class Ui_feedialog(object):
    def setupUi(self, feedialog):
        if not feedialog.objectName():
            feedialog.setObjectName(u"feedialog")
        feedialog.resize(518, 225)
        self.gridLayout = QGridLayout(feedialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pb_opencsv = QPushButton(feedialog)
        self.pb_opencsv.setObjectName(u"pb_opencsv")

        self.gridLayout.addWidget(self.pb_opencsv, 0, 1, 1, 1)

        self.te_info = QTextEdit(feedialog)
        self.te_info.setObjectName(u"te_info")
        self.te_info.setReadOnly(True)

        self.gridLayout.addWidget(self.te_info, 1, 1, 1, 1)

        self.pb_createfeeliabilities = QPushButton(feedialog)
        self.pb_createfeeliabilities.setObjectName(u"pb_createfeeliabilities")
        self.pb_createfeeliabilities.setEnabled(False)

        self.gridLayout.addWidget(self.pb_createfeeliabilities, 2, 1, 1, 1)


        self.retranslateUi(feedialog)

        QMetaObject.connectSlotsByName(feedialog)
    # setupUi

    def retranslateUi(self, feedialog):
        feedialog.setWindowTitle(QCoreApplication.translate("feedialog", u"\u0423\u0447\u0435\u0442 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0439", None))
        self.pb_opencsv.setText(QCoreApplication.translate("feedialog", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443 (CSV-\u0444\u0430\u0439\u043b)", None))
        self.pb_createfeeliabilities.setText(QCoreApplication.translate("feedialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
    # retranslateUi

