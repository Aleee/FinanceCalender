# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'matchingdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QWidget)

class Ui_matchingdialog(object):
    def setupUi(self, matchingdialog):
        if not matchingdialog.objectName():
            matchingdialog.setObjectName(u"matchingdialog")
        matchingdialog.resize(518, 294)
        self.gridLayout = QGridLayout(matchingdialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 1, 1, 1)

        self.pb_close = QPushButton(matchingdialog)
        self.pb_close.setObjectName(u"pb_close")
        self.pb_close.setEnabled(True)

        self.gridLayout.addWidget(self.pb_close, 2, 2, 1, 1)

        self.chb_fullreport = QCheckBox(matchingdialog)
        self.chb_fullreport.setObjectName(u"chb_fullreport")

        self.gridLayout.addWidget(self.chb_fullreport, 2, 0, 1, 1)

        self.te_info = QTextEdit(matchingdialog)
        self.te_info.setObjectName(u"te_info")
        self.te_info.setReadOnly(True)

        self.gridLayout.addWidget(self.te_info, 1, 0, 1, 3)

        self.pb_opencsv = QPushButton(matchingdialog)
        self.pb_opencsv.setObjectName(u"pb_opencsv")

        self.gridLayout.addWidget(self.pb_opencsv, 0, 0, 1, 3)


        self.retranslateUi(matchingdialog)

        QMetaObject.connectSlotsByName(matchingdialog)
    # setupUi

    def retranslateUi(self, matchingdialog):
        matchingdialog.setWindowTitle(QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u0435\u0440\u043a\u0430 \u0432\u044b\u043f\u0438\u0441\u043a\u0438", None))
        self.pb_close.setText(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
        self.chb_fullreport.setText(QCoreApplication.translate("matchingdialog", u"\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u044b\u0439 \u043e\u0442\u0447\u0435\u0442", None))
        self.pb_opencsv.setText(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443 (CSV-\u0444\u0430\u0439\u043b)", None))
    # retranslateUi

