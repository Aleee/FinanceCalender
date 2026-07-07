# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'debtchartdialog.ui'
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
    QHBoxLayout, QLabel, QLayout, QListWidget,
    QListWidgetItem, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_DebtChartDialog(object):
    def setupUi(self, DebtChartDialog):
        if not DebtChartDialog.objectName():
            DebtChartDialog.setObjectName(u"DebtChartDialog")
        DebtChartDialog.resize(861, 462)
        self.gridLayout = QGridLayout(DebtChartDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.widget = QWidget(DebtChartDialog)
        self.widget.setObjectName(u"widget")

        self.gridLayout.addWidget(self.widget, 2, 4, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.label = QLabel(DebtChartDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.lw_categories = QListWidget(DebtChartDialog)
        self.lw_categories.setObjectName(u"lw_categories")
        self.lw_categories.setMaximumSize(QSize(200, 16777215))
        self.lw_categories.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        self.verticalLayout.addWidget(self.lw_categories)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(DebtChartDialog)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.spb_smooth = QSpinBox(DebtChartDialog)
        self.spb_smooth.setObjectName(u"spb_smooth")
        self.spb_smooth.setMinimumSize(QSize(50, 0))
        self.spb_smooth.setMaximumSize(QSize(50, 16777215))
        self.spb_smooth.setMinimum(1)
        self.spb_smooth.setMaximum(90)
        self.spb_smooth.setValue(10)

        self.horizontalLayout.addWidget(self.spb_smooth)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.gridLayout.addLayout(self.verticalLayout, 2, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 5, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 2, 1, 1, 1)


        self.retranslateUi(DebtChartDialog)

        QMetaObject.connectSlotsByName(DebtChartDialog)
    # setupUi

    def retranslateUi(self, DebtChartDialog):
        DebtChartDialog.setWindowTitle(QCoreApplication.translate("DebtChartDialog", u"\u0413\u0440\u0430\u0444\u0438\u043a - \u0417\u0430\u0434\u043e\u043b\u0436\u0435\u043d\u043d\u043e\u0441\u0442\u044c", None))
        self.label.setText(QCoreApplication.translate("DebtChartDialog", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:", None))
        self.label_2.setText(QCoreApplication.translate("DebtChartDialog", u"\u0421\u0433\u043b\u0430\u0436\u0438\u0432\u0430\u043d\u0438\u0435 (\u0434\u043d\u0438): ", None))
    # retranslateUi

