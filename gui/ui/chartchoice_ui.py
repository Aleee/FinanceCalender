# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chartchoice.ui'
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
from PySide6.QtWidgets import (QApplication, QDateEdit, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_ChartChoiceDialog(object):
    def setupUi(self, ChartChoiceDialog):
        if not ChartChoiceDialog.objectName():
            ChartChoiceDialog.setObjectName(u"ChartChoiceDialog")
        ChartChoiceDialog.resize(400, 172)
        self.gridLayout = QGridLayout(ChartChoiceDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(ChartChoiceDialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.de_end = QDateEdit(ChartChoiceDialog)
        self.de_end.setObjectName(u"de_end")
        self.de_end.setCalendarPopup(True)

        self.gridLayout.addWidget(self.de_end, 1, 2, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(ChartChoiceDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_continue = QPushButton(ChartChoiceDialog)
        self.pb_continue.setObjectName(u"pb_continue")

        self.horizontalLayout.addWidget(self.pb_continue)


        self.gridLayout.addLayout(self.horizontalLayout, 6, 0, 1, 4)

        self.horizontalSpacer_3 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 0, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 3, 1, 1)

        self.line_2 = QFrame(ChartChoiceDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 5, 0, 1, 4)

        self.label_2 = QLabel(ChartChoiceDialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.line = QFrame(ChartChoiceDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 2, 0, 1, 4)

        self.rb_chart1 = QRadioButton(ChartChoiceDialog)
        self.rb_chart1.setObjectName(u"rb_chart1")
        self.rb_chart1.setChecked(True)

        self.gridLayout.addWidget(self.rb_chart1, 3, 0, 1, 3)

        self.de_start = QDateEdit(ChartChoiceDialog)
        self.de_start.setObjectName(u"de_start")
        self.de_start.setCalendarPopup(True)

        self.gridLayout.addWidget(self.de_start, 0, 2, 1, 1)


        self.retranslateUi(ChartChoiceDialog)

        self.pb_continue.setDefault(True)


        QMetaObject.connectSlotsByName(ChartChoiceDialog)
    # setupUi

    def retranslateUi(self, ChartChoiceDialog):
        ChartChoiceDialog.setWindowTitle(QCoreApplication.translate("ChartChoiceDialog", u"\u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c \u0433\u0440\u0430\u0444\u0438\u043a", None))
        self.label.setText(QCoreApplication.translate("ChartChoiceDialog", u"\u041d\u0430\u0447\u0430\u043b\u043e \u043f\u0435\u0440\u0438\u043e\u0434\u0430:", None))
        self.pb_cancel.setText(QCoreApplication.translate("ChartChoiceDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_continue.setText(QCoreApplication.translate("ChartChoiceDialog", u" \u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c ", None))
        self.label_2.setText(QCoreApplication.translate("ChartChoiceDialog", u"\u041a\u043e\u043d\u0435\u0446 \u043f\u0435\u0440\u0438\u043e\u0434\u0430:", None))
        self.rb_chart1.setText(QCoreApplication.translate("ChartChoiceDialog", u"\u0414\u0438\u043d\u0430\u043c\u0438\u043a\u0430 \u0437\u0430\u0434\u043e\u043b\u0436\u0435\u043d\u043d\u043e\u0441\u0442\u0438", None))
    # retranslateUi

