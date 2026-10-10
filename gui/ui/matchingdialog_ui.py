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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QGridLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTableWidget, QTableWidgetItem, QWidget)

class Ui_matchingdialog(object):
    def setupUi(self, matchingdialog):
        if not matchingdialog.objectName():
            matchingdialog.setObjectName(u"matchingdialog")
        matchingdialog.resize(1100, 560)
        self.gridLayout = QGridLayout(matchingdialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 3, 1, 1, 1)

        self.pb_close = QPushButton(matchingdialog)
        self.pb_close.setObjectName(u"pb_close")
        self.pb_close.setEnabled(True)

        self.gridLayout.addWidget(self.pb_close, 3, 2, 1, 1)

        self.lb_summary = QLabel(matchingdialog)
        self.lb_summary.setObjectName(u"lb_summary")

        self.gridLayout.addWidget(self.lb_summary, 1, 0, 1, 3)

        self.tw_discrepancies = QTableWidget(matchingdialog)
        self.tw_discrepancies.setObjectName(u"tw_discrepancies")
        self.tw_discrepancies.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_discrepancies.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tw_discrepancies.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_discrepancies.setWordWrap(True)
        self.tw_discrepancies.verticalHeader().setVisible(False)

        self.gridLayout.addWidget(self.tw_discrepancies, 2, 0, 1, 3)

        self.pb_opencsv = QPushButton(matchingdialog)
        self.pb_opencsv.setObjectName(u"pb_opencsv")

        self.gridLayout.addWidget(self.pb_opencsv, 0, 0, 1, 3)


        self.retranslateUi(matchingdialog)

        QMetaObject.connectSlotsByName(matchingdialog)
    # setupUi

    def retranslateUi(self, matchingdialog):
        matchingdialog.setWindowTitle(QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u0435\u0440\u043a\u0430 \u0432\u044b\u043f\u0438\u0441\u043a\u0438", None))
        self.pb_close.setText(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
        self.lb_summary.setText("")
        self.pb_opencsv.setText(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443 (CSV-\u0444\u0430\u0439\u043b)", None))
    # retranslateUi

