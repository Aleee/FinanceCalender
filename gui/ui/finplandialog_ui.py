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
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QWidget)

from gui.finplanwidget import FinPlanTableView

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
        self.lbl_year = QLabel(FinPlanDialog)
        self.lbl_year.setObjectName(u"lbl_year")

        self.horizontalLayout.addWidget(self.lbl_year)

        self.sb_year = QSpinBox(FinPlanDialog)
        self.sb_year.setObjectName(u"sb_year")
        self.sb_year.setMinimumSize(QSize(80, 0))
        self.sb_year.setMinimum(2025)
        self.sb_year.setMaximum(2099)

        self.horizontalLayout.addWidget(self.sb_year)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(FinPlanDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")
        self.pb_cancel.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_save = QPushButton(FinPlanDialog)
        self.pb_save.setObjectName(u"pb_save")
        self.pb_save.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_save)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 2)

        self.tv_finplan = FinPlanTableView(FinPlanDialog)
        self.tv_finplan.setObjectName(u"tv_finplan")

        self.gridLayout.addWidget(self.tv_finplan, 0, 0, 1, 2)

        QWidget.setTabOrder(self.tv_finplan, self.pb_save)
        QWidget.setTabOrder(self.pb_save, self.pb_cancel)

        self.retranslateUi(FinPlanDialog)

        QMetaObject.connectSlotsByName(FinPlanDialog)
    # setupUi

    def retranslateUi(self, FinPlanDialog):
        FinPlanDialog.setWindowTitle(QCoreApplication.translate("FinPlanDialog", u"\u0424\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u043d", None))
        self.lbl_year.setText(QCoreApplication.translate("FinPlanDialog", u"\u0413\u043e\u0434:", None))
        self.pb_cancel.setText(QCoreApplication.translate("FinPlanDialog", u" \u041e\u0442\u043c\u0435\u043d\u0430 ", None))
        self.pb_save.setText(QCoreApplication.translate("FinPlanDialog", u" \u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c ", None))
    # retranslateUi

