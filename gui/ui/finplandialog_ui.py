# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'finplandialog.ui'
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
    QHBoxLayout, QHeaderView, QPushButton, QSizePolicy,
    QSpacerItem, QTableView, QWidget)

class Ui_FinPlanDialog(object):
    def setupUi(self, FinPlanDialog):
        if not FinPlanDialog.objectName():
            FinPlanDialog.setObjectName(u"FinPlanDialog")
        FinPlanDialog.resize(1109, 685)
        self.gridLayout = QGridLayout(FinPlanDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.line = QFrame(FinPlanDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 1, 0, 1, 2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton_2 = QPushButton(FinPlanDialog)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(FinPlanDialog)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout.addWidget(self.pushButton)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 2)

        self.tv_finplan = QTableView(FinPlanDialog)
        self.tv_finplan.setObjectName(u"tv_finplan")

        self.gridLayout.addWidget(self.tv_finplan, 0, 0, 1, 2)


        self.retranslateUi(FinPlanDialog)

        QMetaObject.connectSlotsByName(FinPlanDialog)
    # setupUi

    def retranslateUi(self, FinPlanDialog):
        FinPlanDialog.setWindowTitle(QCoreApplication.translate("FinPlanDialog", u"Dialog", None))
        self.pushButton_2.setText(QCoreApplication.translate("FinPlanDialog", u" \u041e\u0442\u043c\u0435\u043d\u0430 ", None))
        self.pushButton.setText(QCoreApplication.translate("FinPlanDialog", u" \u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c ", None))
    # retranslateUi

