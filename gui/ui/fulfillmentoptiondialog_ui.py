# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fulfillmentoptiondialog.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QComboBox, QDateEdit,
    QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QStackedWidget, QWidget)

from gui.commonwidgets.autoselectwidgets import AutoSelectSpinbox
from gui.commonwidgets.firstdaydateedit import FirstDayDateEdit

class Ui_FulfillmentOptionDialog(object):
    def setupUi(self, FulfillmentOptionDialog):
        if not FulfillmentOptionDialog.objectName():
            FulfillmentOptionDialog.setObjectName(u"FulfillmentOptionDialog")
        FulfillmentOptionDialog.resize(348, 257)
        self.gridLayout = QGridLayout(FulfillmentOptionDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 3, -1, -1)
        self.pb_continue = QPushButton(FulfillmentOptionDialog)
        self.pb_continue.setObjectName(u"pb_continue")

        self.gridLayout.addWidget(self.pb_continue, 16, 2, 1, 1)

        self.stackedWidget = QStackedWidget(FulfillmentOptionDialog)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.gridLayout_2 = QGridLayout(self.page)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.rb_customperiod = QRadioButton(self.page)
        self.rb_customperiod.setObjectName(u"rb_customperiod")
        font = QFont()
        font.setBold(False)
        self.rb_customperiod.setFont(font)

        self.horizontalLayout.addWidget(self.rb_customperiod)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label = QLabel(self.page)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.de_customperiod_begin = FirstDayDateEdit(self.page)
        self.de_customperiod_begin.setObjectName(u"de_customperiod_begin")
        self.de_customperiod_begin.setCalendarPopup(True)

        self.horizontalLayout.addWidget(self.de_customperiod_begin)

        self.label_2 = QLabel(self.page)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.de_customperiod_end = QDateEdit(self.page)
        self.de_customperiod_end.setObjectName(u"de_customperiod_end")
        self.de_customperiod_end.setCalendarPopup(True)

        self.horizontalLayout.addWidget(self.de_customperiod_end)


        self.gridLayout_2.addLayout(self.horizontalLayout, 6, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.widget_3 = QWidget(self.page)
        self.widget_3.setObjectName(u"widget_3")
        self.widget_3.setMinimumSize(QSize(30, 0))
        self.widget_3.setMaximumSize(QSize(30, 16777215))
        self.horizontalLayout_8 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.widget_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(25, 0))
        self.label_4.setMaximumSize(QSize(25, 16777215))
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_4)


        self.horizontalLayout_4.addWidget(self.widget_3)

        self.cmb_severalmonths_end = QComboBox(self.page)
        self.cmb_severalmonths_end.setObjectName(u"cmb_severalmonths_end")

        self.horizontalLayout_4.addWidget(self.cmb_severalmonths_end)

        self.spb_severalmonths_year_end = QSpinBox(self.page)
        self.spb_severalmonths_year_end.setObjectName(u"spb_severalmonths_year_end")
        self.spb_severalmonths_year_end.setMinimumSize(QSize(70, 0))
        self.spb_severalmonths_year_end.setMaximumSize(QSize(70, 16777215))
        self.spb_severalmonths_year_end.setMinimum(2026)
        self.spb_severalmonths_year_end.setMaximum(2099)

        self.horizontalLayout_4.addWidget(self.spb_severalmonths_year_end)


        self.gridLayout_2.addLayout(self.horizontalLayout_4, 4, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_2, 5, 0, 1, 1)

        self.rb_severalmonths = QRadioButton(self.page)
        self.rb_severalmonths.setObjectName(u"rb_severalmonths")
        self.rb_severalmonths.setFont(font)

        self.gridLayout_2.addWidget(self.rb_severalmonths, 2, 0, 1, 1)

        self.rb_onemonth = QRadioButton(self.page)
        self.rb_onemonth.setObjectName(u"rb_onemonth")
        self.rb_onemonth.setFont(font)

        self.gridLayout_2.addWidget(self.rb_onemonth, 0, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.widget_2 = QWidget(self.page)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setMinimumSize(QSize(30, 0))
        self.widget_2.setMaximumSize(QSize(30, 16777215))
        self.horizontalLayout_7 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.widget_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(25, 0))
        self.label_3.setMaximumSize(QSize(25, 16777215))
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.label_3)


        self.horizontalLayout_3.addWidget(self.widget_2)

        self.cmb_severalmonths_begin = QComboBox(self.page)
        self.cmb_severalmonths_begin.setObjectName(u"cmb_severalmonths_begin")

        self.horizontalLayout_3.addWidget(self.cmb_severalmonths_begin)

        self.horizontalSpacer = QSpacerItem(70, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.widget = QWidget(self.page)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(30, 0))
        self.widget.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout_5.addWidget(self.widget)

        self.cmb_onemonth = QComboBox(self.page)
        self.cmb_onemonth.setObjectName(u"cmb_onemonth")

        self.horizontalLayout_5.addWidget(self.cmb_onemonth)

        self.spb_onemonth_year = QSpinBox(self.page)
        self.spb_onemonth_year.setObjectName(u"spb_onemonth_year")
        self.spb_onemonth_year.setMinimumSize(QSize(70, 0))
        self.spb_onemonth_year.setMaximumSize(QSize(70, 16777215))
        self.spb_onemonth_year.setMinimum(2026)
        self.spb_onemonth_year.setMaximum(2099)

        self.horizontalLayout_5.addWidget(self.spb_onemonth_year)


        self.gridLayout_2.addLayout(self.horizontalLayout_5, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer, 7, 0, 1, 1)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.gridLayout_3 = QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_10 = QLabel(self.page_2)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_3.addWidget(self.label_10, 1, 0, 1, 1)

        self.label_7 = QLabel(self.page_2)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_3.addWidget(self.label_7, 5, 0, 1, 1)

        self.spb_21000 = AutoSelectSpinbox(self.page_2)
        self.spb_21000.setObjectName(u"spb_21000")
        self.spb_21000.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spb_21000.setProperty(u"showGroupSeparator", True)
        self.spb_21000.setMinimum(-999999999)
        self.spb_21000.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.spb_21000, 4, 1, 1, 1)

        self.label_5 = QLabel(self.page_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_3.addWidget(self.label_5, 3, 0, 1, 1)

        self.spb_10000 = AutoSelectSpinbox(self.page_2)
        self.spb_10000.setObjectName(u"spb_10000")
        self.spb_10000.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spb_10000.setProperty(u"showGroupSeparator", True)
        self.spb_10000.setMinimum(-999999999)
        self.spb_10000.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.spb_10000, 3, 1, 1, 1)

        self.label_8 = QLabel(self.page_2)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_3.addWidget(self.label_8, 6, 0, 1, 1)

        self.label_6 = QLabel(self.page_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_3.addWidget(self.label_6, 4, 0, 1, 1)

        self.spb_22000 = AutoSelectSpinbox(self.page_2)
        self.spb_22000.setObjectName(u"spb_22000")
        self.spb_22000.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spb_22000.setProperty(u"showGroupSeparator", True)
        self.spb_22000.setMinimum(-999999999)
        self.spb_22000.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.spb_22000, 5, 1, 1, 1)

        self.spb_23200 = AutoSelectSpinbox(self.page_2)
        self.spb_23200.setObjectName(u"spb_23200")
        self.spb_23200.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spb_23200.setProperty(u"showGroupSeparator", True)
        self.spb_23200.setMinimum(-999999999)
        self.spb_23200.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.spb_23200, 7, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_3, 8, 0, 1, 1)

        self.label_9 = QLabel(self.page_2)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_3.addWidget(self.label_9, 7, 0, 1, 1)

        self.spb_23100 = AutoSelectSpinbox(self.page_2)
        self.spb_23100.setObjectName(u"spb_23100")
        self.spb_23100.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spb_23100.setProperty(u"showGroupSeparator", True)
        self.spb_23100.setMinimum(-999999999)
        self.spb_23100.setMaximum(999999999)

        self.gridLayout_3.addWidget(self.spb_23100, 6, 1, 1, 1)

        self.line_2 = QFrame(self.page_2)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_2, 2, 0, 1, 2)

        self.stackedWidget.addWidget(self.page_2)

        self.gridLayout.addWidget(self.stackedWidget, 9, 0, 1, 3)

        self.line = QFrame(FulfillmentOptionDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 10, 0, 1, 3)

        self.pb_cancel = QPushButton(FulfillmentOptionDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.gridLayout.addWidget(self.pb_cancel, 16, 1, 1, 1)


        self.retranslateUi(FulfillmentOptionDialog)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(FulfillmentOptionDialog)
    # setupUi

    def retranslateUi(self, FulfillmentOptionDialog):
        FulfillmentOptionDialog.setWindowTitle(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0418\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0433\u043e \u043f\u043b\u0430\u043d\u0430", None))
        self.pb_continue.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0414\u0430\u043b\u0435\u0435", None))
        self.rb_customperiod.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0417\u0430 \u043f\u0435\u0440\u0438\u043e\u0434:", None))
        self.label.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0441", None))
        self.label_2.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u043f\u043e", None))
        self.label_4.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u043f\u043e", None))
        self.rb_severalmonths.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0417\u0430 \u043c\u0435\u0441\u044f\u0446\u044b:", None))
        self.rb_onemonth.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0417\u0430 \u043c\u0435\u0441\u044f\u0446:", None))
        self.label_3.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0441", None))
        self.label_10.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u0421\u0432\u0435\u0434\u0435\u043d\u0438\u044f \u043e \u043f\u043e\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u044f\u0445:", None))
        self.label_7.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"2.2. \u041f\u0440\u043e\u0447\u0438\u0435 \u0434\u043e\u0445\u043e\u0434\u044b:", None))
        self.label_5.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"1. \u041e\u0441\u0442\u0430\u0442\u043e\u043a \u0441\u0440\u0435\u0434\u0441\u0442\u0432 \u043d\u0430 \u043d\u0430\u0447\u0430\u043b\u043e \u043f\u0435\u0440\u0438\u043e\u0434\u0430:  ", None))
        self.label_8.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"2.3.1. \u041e\u0432\u0435\u0440\u0434\u0440\u0430\u0444\u0442:", None))
        self.label_6.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"2.1. \u0412\u044b\u0440\u0443\u0447\u043a\u0430 \u043e\u0442 \u0440\u0435\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0438 \u0443\u0441\u043b\u0443\u0433: ", None))
        self.label_9.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"2.3.2. \u041a\u0440\u0435\u0434\u0438\u0442:", None))
        self.pb_cancel.setText(QCoreApplication.translate("FulfillmentOptionDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

