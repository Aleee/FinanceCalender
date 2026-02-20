# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'eventdialog.ui'
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
    QDialog, QDoubleSpinBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPlainTextEdit, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QWidget)

from gui.commonwidgets.completingtextedit import CompletingPlainTextEdit

class Ui_EventDialog(object):
    def setupUi(self, EventDialog):
        if not EventDialog.objectName():
            EventDialog.setObjectName(u"EventDialog")
        EventDialog.resize(599, 420)
        self.gridLayout_2 = QGridLayout(EventDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(8)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_6 = QLabel(EventDialog)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 7, 1, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(8)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_8 = QLabel(EventDialog)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_6.addWidget(self.label_8)

        self.rb_typenormal = QRadioButton(EventDialog)
        self.rb_typenormal.setObjectName(u"rb_typenormal")

        self.horizontalLayout_6.addWidget(self.rb_typenormal)

        self.rb_typeadvance = QRadioButton(EventDialog)
        self.rb_typeadvance.setObjectName(u"rb_typeadvance")

        self.horizontalLayout_6.addWidget(self.rb_typeadvance)

        self.horizontalSpacer_6 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.line = QFrame(EventDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_6.addWidget(self.line)

        self.horizontalSpacer_7 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_7)

        self.label_10 = QLabel(EventDialog)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_6.addWidget(self.label_10)

        self.cmb_nds = QComboBox(EventDialog)
        self.cmb_nds.setObjectName(u"cmb_nds")

        self.horizontalLayout_6.addWidget(self.cmb_nds)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_10)


        self.gridLayout.addLayout(self.horizontalLayout_6, 5, 1, 1, 1)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_5 = QLabel(EventDialog)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_8.addWidget(self.label_5)

        self.cmb_category = QComboBox(EventDialog)
        self.cmb_category.setObjectName(u"cmb_category")
        self.cmb_category.setMinimumSize(QSize(400, 0))

        self.horizontalLayout_8.addWidget(self.cmb_category)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.horizontalLayout_8, 4, 1, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(EventDialog)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.dsb_totalamount = QDoubleSpinBox(EventDialog)
        self.dsb_totalamount.setObjectName(u"dsb_totalamount")
        self.dsb_totalamount.setMinimumSize(QSize(100, 0))
        self.dsb_totalamount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_totalamount.setMaximum(99999999.000000000000000)

        self.horizontalLayout_4.addWidget(self.dsb_totalamount)

        self.horizontalSpacer_5 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)

        self.line_2 = QFrame(EventDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_4.addWidget(self.line_2)

        self.horizontalSpacer_3 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.label_4 = QLabel(EventDialog)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_4.addWidget(self.label_4)

        self.de_duedate = QDateEdit(EventDialog)
        self.de_duedate.setObjectName(u"de_duedate")
        self.de_duedate.setMinimumSize(QSize(80, 0))
        self.de_duedate.setCalendarPopup(True)

        self.horizontalLayout_4.addWidget(self.de_duedate)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.horizontalLayout_4, 1, 1, 1, 1)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(8)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_7 = QLabel(EventDialog)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_7.addWidget(self.label_7)

        self.le_responsible = QLineEdit(EventDialog)
        self.le_responsible.setObjectName(u"le_responsible")
        self.le_responsible.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_7.addWidget(self.le_responsible)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)


        self.gridLayout.addLayout(self.horizontalLayout_7, 6, 1, 1, 1)

        self.te_descr = CompletingPlainTextEdit(EventDialog)
        self.te_descr.setObjectName(u"te_descr")
        self.te_descr.setMinimumSize(QSize(0, 50))
        self.te_descr.setMaximumSize(QSize(16777215, 50))

        self.gridLayout.addWidget(self.te_descr, 8, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")

        self.gridLayout.addLayout(self.horizontalLayout, 5, 4, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setVerticalSpacing(8)
        self.label = QLabel(EventDialog)
        self.label.setObjectName(u"label")

        self.gridLayout_3.addWidget(self.label, 1, 0, 1, 1)

        self.label_2 = QLabel(EventDialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_3.addWidget(self.label_2, 2, 0, 1, 1)

        self.le_receiver = QLineEdit(EventDialog)
        self.le_receiver.setObjectName(u"le_receiver")

        self.gridLayout_3.addWidget(self.le_receiver, 1, 2, 1, 1)

        self.le_name = QLineEdit(EventDialog)
        self.le_name.setObjectName(u"le_name")

        self.gridLayout_3.addWidget(self.le_name, 2, 2, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_4, 2, 1, 1, 1)


        self.horizontalLayout_2.addLayout(self.gridLayout_3)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)

        self.label_9 = QLabel(EventDialog)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 9, 1, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_8)

        self.pb_accept = QPushButton(EventDialog)
        self.pb_accept.setObjectName(u"pb_accept")

        self.horizontalLayout_3.addWidget(self.pb_accept)

        self.pb_cancel = QPushButton(EventDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout_3.addWidget(self.pb_cancel)


        self.gridLayout.addLayout(self.horizontalLayout_3, 11, 1, 1, 1)

        self.te_notes = QPlainTextEdit(EventDialog)
        self.te_notes.setObjectName(u"te_notes")
        self.te_notes.setMinimumSize(QSize(0, 70))
        self.te_notes.setMaximumSize(QSize(16777215, 70))

        self.gridLayout.addWidget(self.te_notes, 10, 1, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        QWidget.setTabOrder(self.le_receiver, self.le_name)
        QWidget.setTabOrder(self.le_name, self.dsb_totalamount)
        QWidget.setTabOrder(self.dsb_totalamount, self.de_duedate)
        QWidget.setTabOrder(self.de_duedate, self.cmb_category)
        QWidget.setTabOrder(self.cmb_category, self.rb_typenormal)
        QWidget.setTabOrder(self.rb_typenormal, self.rb_typeadvance)
        QWidget.setTabOrder(self.rb_typeadvance, self.le_responsible)
        QWidget.setTabOrder(self.le_responsible, self.te_descr)
        QWidget.setTabOrder(self.te_descr, self.pb_cancel)
        QWidget.setTabOrder(self.pb_cancel, self.pb_accept)

        self.retranslateUi(EventDialog)

        QMetaObject.connectSlotsByName(EventDialog)
    # setupUi

    def retranslateUi(self, EventDialog):
        EventDialog.setWindowTitle(QCoreApplication.translate("EventDialog", u"\u041d\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436", None))
        self.label_6.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.label_8.setText(QCoreApplication.translate("EventDialog", u"\u0412\u0438\u0434:", None))
        self.rb_typenormal.setText(QCoreApplication.translate("EventDialog", u"\u043f\u043e \u0444\u0430\u043a\u0442\u0443", None))
        self.rb_typeadvance.setText(QCoreApplication.translate("EventDialog", u"\u043f\u0440\u0435\u0434\u043e\u043f\u043b\u0430\u0442\u0430", None))
        self.label_10.setText(QCoreApplication.translate("EventDialog", u"\u041d\u0414\u0421: ", None))
        self.label_5.setText(QCoreApplication.translate("EventDialog", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", None))
        self.label_3.setText(QCoreApplication.translate("EventDialog", u"\u0421\u0443\u043c\u043c\u0430:", None))
        self.label_4.setText(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430:", None))
        self.label_7.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", None))
        self.label.setText(QCoreApplication.translate("EventDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.label_2.setText(QCoreApplication.translate("EventDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.label_9.setText(QCoreApplication.translate("EventDialog", u"\u0417\u0430\u043c\u0435\u0442\u043a\u0438:", None))
        self.pb_accept.setText(QCoreApplication.translate("EventDialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        self.pb_cancel.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

