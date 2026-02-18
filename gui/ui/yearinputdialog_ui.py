# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'yearinputdialog.ui'
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
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QWidget)

class Ui_YearInputDialog(object):
    def setupUi(self, YearInputDialog):
        if not YearInputDialog.objectName():
            YearInputDialog.setObjectName(u"YearInputDialog")
        YearInputDialog.resize(200, 90)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(YearInputDialog.sizePolicy().hasHeightForWidth())
        YearInputDialog.setSizePolicy(sizePolicy)
        YearInputDialog.setMinimumSize(QSize(200, 90))
        YearInputDialog.setMaximumSize(QSize(200, 90))
        self.gridLayout = QGridLayout(YearInputDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(YearInputDialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.line = QFrame(YearInputDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 1, 0, 1, 3)

        self.spinBox = QSpinBox(YearInputDialog)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setMinimumSize(QSize(80, 0))
        self.spinBox.setMinimum(2025)
        self.spinBox.setMaximum(2099)

        self.gridLayout.addWidget(self.spinBox, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 1, 1)

        self.pushButton = QPushButton(YearInputDialog)
        self.pushButton.setObjectName(u"pushButton")

        self.gridLayout.addWidget(self.pushButton, 3, 0, 1, 3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 2, 0, 1, 1)


        self.retranslateUi(YearInputDialog)

        QMetaObject.connectSlotsByName(YearInputDialog)
    # setupUi

    def retranslateUi(self, YearInputDialog):
        YearInputDialog.setWindowTitle(QCoreApplication.translate("YearInputDialog", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0433\u043e\u0434", None))
        self.label.setText(QCoreApplication.translate("YearInputDialog", u"\u0413\u043e\u0434 :", None))
        self.pushButton.setText(QCoreApplication.translate("YearInputDialog", u"\u0414\u0430\u043b\u0435\u0435", None))
    # retranslateUi

