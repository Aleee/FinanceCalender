# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'contractdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
    QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QWidget)

class Ui_ContractDialog(object):
    def setupUi(self, ContractDialog):
        if not ContractDialog.objectName():
            ContractDialog.setObjectName(u"ContractDialog")
        ContractDialog.resize(532, 573)
        self.gridLayout = QGridLayout(ContractDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.fr_relative = QFrame(ContractDialog)
        self.fr_relative.setObjectName(u"fr_relative")
        self.fr_relative.setFrameShape(QFrame.Shape.StyledPanel)
        self.fr_relative.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_7 = QGridLayout(self.fr_relative)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(-1, 0, -1, 0)
        self.label_7 = QLabel(self.fr_relative)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_7.addWidget(self.label_7, 0, 0, 1, 1)

        self.chb_rel_additional = QCheckBox(self.fr_relative)
        self.chb_rel_additional.setObjectName(u"chb_rel_additional")

        self.gridLayout_7.addWidget(self.chb_rel_additional, 2, 0, 1, 3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.rb_rel_calendar = QRadioButton(self.fr_relative)
        self.rb_rel_calendar.setObjectName(u"rb_rel_calendar")

        self.horizontalLayout_3.addWidget(self.rb_rel_calendar)

        self.rb_rel_banking = QRadioButton(self.fr_relative)
        self.rb_rel_banking.setObjectName(u"rb_rel_banking")

        self.horizontalLayout_3.addWidget(self.rb_rel_banking)

        self.rb_rel_working = QRadioButton(self.fr_relative)
        self.rb_rel_working.setObjectName(u"rb_rel_working")

        self.horizontalLayout_3.addWidget(self.rb_rel_working)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.gridLayout_7.addLayout(self.horizontalLayout_3, 1, 0, 1, 3)

        self.spb_rel_days = QSpinBox(self.fr_relative)
        self.spb_rel_days.setObjectName(u"spb_rel_days")
        self.spb_rel_days.setMaximum(365)

        self.gridLayout_7.addWidget(self.spb_rel_days, 0, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_2, 0, 2, 1, 1)

        self.widget_2 = QWidget(self.fr_relative)
        self.widget_2.setObjectName(u"widget_2")
        self.gridLayout_6 = QGridLayout(self.widget_2)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_7, 0, 2, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.rb_rel_period_curr = QRadioButton(self.widget_2)
        self.rb_rel_period_curr.setObjectName(u"rb_rel_period_curr")

        self.horizontalLayout_6.addWidget(self.rb_rel_period_curr)

        self.rb_rel_period_next = QRadioButton(self.widget_2)
        self.rb_rel_period_next.setObjectName(u"rb_rel_period_next")

        self.horizontalLayout_6.addWidget(self.rb_rel_period_next)

        self.rb_rel_period_prev = QRadioButton(self.widget_2)
        self.rb_rel_period_prev.setObjectName(u"rb_rel_period_prev")

        self.horizontalLayout_6.addWidget(self.rb_rel_period_prev)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_8)


        self.gridLayout_6.addLayout(self.horizontalLayout_6, 2, 0, 1, 3)

        self.spb_rel_dayofmonth = QSpinBox(self.widget_2)
        self.spb_rel_dayofmonth.setObjectName(u"spb_rel_dayofmonth")
        self.spb_rel_dayofmonth.setMinimum(1)
        self.spb_rel_dayofmonth.setMaximum(31)

        self.gridLayout_6.addWidget(self.spb_rel_dayofmonth, 0, 1, 1, 1)

        self.label_10 = QLabel(self.widget_2)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_6.addWidget(self.label_10, 0, 0, 1, 1)


        self.gridLayout_7.addWidget(self.widget_2, 3, 0, 1, 3)


        self.gridLayout.addWidget(self.fr_relative, 6, 2, 1, 2)

        self.rb_fixed = QRadioButton(ContractDialog)
        self.rb_fixed.setObjectName(u"rb_fixed")

        self.gridLayout.addWidget(self.rb_fixed, 7, 2, 1, 1)

        self.rb_termsunknown = QRadioButton(ContractDialog)
        self.rb_termsunknown.setObjectName(u"rb_termsunknown")

        self.gridLayout.addWidget(self.rb_termsunknown, 4, 2, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(-1, 0, -1, 0)
        self.label_4 = QLabel(ContractDialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 1, 2, 1, 1)

        self.de_contractdate = QDateEdit(ContractDialog)
        self.de_contractdate.setObjectName(u"de_contractdate")
        self.de_contractdate.setCalendarPopup(True)

        self.gridLayout_3.addWidget(self.de_contractdate, 1, 3, 1, 1)

        self.le_contractname = QLineEdit(ContractDialog)
        self.le_contractname.setObjectName(u"le_contractname")

        self.gridLayout_3.addWidget(self.le_contractname, 1, 1, 1, 1)

        self.label_2 = QLabel(ContractDialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)

        self.le_contractor = QLineEdit(ContractDialog)
        self.le_contractor.setObjectName(u"le_contractor")
        self.le_contractor.setEnabled(True)
        self.le_contractor.setReadOnly(True)

        self.gridLayout_3.addWidget(self.le_contractor, 0, 1, 1, 3)

        self.label = QLabel(ContractDialog)
        self.label.setObjectName(u"label")

        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_3 = QLabel(ContractDialog)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout.addWidget(self.label_3)

        self.cmb_documenttype = QComboBox(ContractDialog)
        self.cmb_documenttype.setObjectName(u"cmb_documenttype")
        self.cmb_documenttype.setMinimumSize(QSize(250, 0))

        self.horizontalLayout.addWidget(self.cmb_documenttype)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout_3.addLayout(self.horizontalLayout, 2, 0, 1, 4)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_9 = QLabel(ContractDialog)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_7.addWidget(self.label_9)

        self.cmb_responsible = QComboBox(ContractDialog)
        self.cmb_responsible.setObjectName(u"cmb_responsible")
        self.cmb_responsible.setMinimumSize(QSize(250, 0))

        self.horizontalLayout_7.addWidget(self.cmb_responsible)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)


        self.gridLayout_3.addLayout(self.horizontalLayout_7, 4, 0, 1, 3)


        self.gridLayout.addLayout(self.gridLayout_3, 0, 2, 1, 2)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_5 = QLabel(ContractDialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_4.addWidget(self.label_5, 0, 0, 1, 1)

        self.label_6 = QLabel(ContractDialog)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_4.addWidget(self.label_6, 1, 0, 1, 2)

        self.te_description = QPlainTextEdit(ContractDialog)
        self.te_description.setObjectName(u"te_description")
        self.te_description.setMaximumSize(QSize(16777215, 50))

        self.gridLayout_4.addWidget(self.te_description, 2, 0, 1, 2)

        self.le_documentname = QLineEdit(ContractDialog)
        self.le_documentname.setObjectName(u"le_documentname")

        self.gridLayout_4.addWidget(self.le_documentname, 0, 1, 1, 1)


        self.gridLayout.addLayout(self.gridLayout_4, 2, 2, 1, 2)

        self.fr_fixed = QFrame(ContractDialog)
        self.fr_fixed.setObjectName(u"fr_fixed")
        self.fr_fixed.setFrameShape(QFrame.Shape.StyledPanel)
        self.fr_fixed.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_8 = QGridLayout(self.fr_fixed)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(-1, 0, -1, 0)
        self.spb_fixed_dayofmonth = QSpinBox(self.fr_fixed)
        self.spb_fixed_dayofmonth.setObjectName(u"spb_fixed_dayofmonth")
        self.spb_fixed_dayofmonth.setMinimum(1)
        self.spb_fixed_dayofmonth.setMaximum(31)

        self.gridLayout_8.addWidget(self.spb_fixed_dayofmonth, 0, 1, 1, 1)

        self.label_8 = QLabel(self.fr_fixed)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_8.addWidget(self.label_8, 0, 0, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_8.addItem(self.horizontalSpacer_4, 0, 2, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.rb_fixed_period_curr = QRadioButton(self.fr_fixed)
        self.rb_fixed_period_curr.setObjectName(u"rb_fixed_period_curr")

        self.horizontalLayout_4.addWidget(self.rb_fixed_period_curr)

        self.rb_fixed_period_next = QRadioButton(self.fr_fixed)
        self.rb_fixed_period_next.setObjectName(u"rb_fixed_period_next")

        self.horizontalLayout_4.addWidget(self.rb_fixed_period_next)

        self.rb_fixed_period_prev = QRadioButton(self.fr_fixed)
        self.rb_fixed_period_prev.setObjectName(u"rb_fixed_period_prev")

        self.horizontalLayout_4.addWidget(self.rb_fixed_period_prev)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)


        self.gridLayout_8.addLayout(self.horizontalLayout_4, 1, 0, 1, 3)


        self.gridLayout.addWidget(self.fr_fixed, 8, 2, 1, 2)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_6)

        self.pushButton_2 = QPushButton(ContractDialog)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_5.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(ContractDialog)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_5.addWidget(self.pushButton)


        self.gridLayout.addLayout(self.horizontalLayout_5, 15, 2, 1, 2)

        self.line_3 = QFrame(ContractDialog)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_3, 10, 2, 1, 2)

        self.rb_relative = QRadioButton(ContractDialog)
        self.rb_relative.setObjectName(u"rb_relative")

        self.gridLayout.addWidget(self.rb_relative, 5, 2, 1, 1)

        self.line_2 = QFrame(ContractDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 3, 2, 1, 2)

        self.line = QFrame(ContractDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 1, 2, 1, 2)


        self.retranslateUi(ContractDialog)

        QMetaObject.connectSlotsByName(ContractDialog)
    # setupUi

    def retranslateUi(self, ContractDialog):
        ContractDialog.setWindowTitle(QCoreApplication.translate("ContractDialog", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430", None))
        self.label_7.setText(QCoreApplication.translate("ContractDialog", u"\u041a\u043e\u043b-\u0432\u043e \u0434\u043d\u0435\u0439:", None))
        self.chb_rel_additional.setText(QCoreApplication.translate("ContractDialog", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u043d\u043e\u0435 \u0443\u0441\u043b\u043e\u0432\u0438\u0435", None))
        self.rb_rel_calendar.setText(QCoreApplication.translate("ContractDialog", u"\u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u043d\u044b\u0435", None))
        self.rb_rel_banking.setText(QCoreApplication.translate("ContractDialog", u"\u0431\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0435", None))
        self.rb_rel_working.setText(QCoreApplication.translate("ContractDialog", u"\u0440\u0430\u0431\u043e\u0447\u0438\u0435", None))
        self.rb_rel_period_curr.setText(QCoreApplication.translate("ContractDialog", u"\u043e\u0442\u0447\u0435\u0442\u043d\u044b\u0439", None))
        self.rb_rel_period_next.setText(QCoreApplication.translate("ContractDialog", u"\u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439", None))
        self.rb_rel_period_prev.setText(QCoreApplication.translate("ContractDialog", u"\u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439", None))
        self.label_10.setText(QCoreApplication.translate("ContractDialog", u"\u0427\u0438\u0441\u043b\u043e \u043c\u0435\u0441\u044f\u0446\u0430: ", None))
        self.rb_fixed.setText(QCoreApplication.translate("ContractDialog", u"\u0424\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0441\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b (\u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0430 \u043a \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044e)", None))
        self.rb_termsunknown.setText(QCoreApplication.translate("ContractDialog", u"\u041f\u0440\u0435\u0434\u043e\u043f\u043b\u0430\u0442\u0430 / \u0421\u0440\u043e\u043a \u044f\u0432\u043d\u043e \u043d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d", None))
        self.label_4.setText(QCoreApplication.translate("ContractDialog", u"\u0414\u0430\u0442\u0430:", None))
        self.label_2.setText(QCoreApplication.translate("ContractDialog", u"\u041d\u043e\u043c\u0435\u0440:", None))
        self.label.setText(QCoreApplication.translate("ContractDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442:", None))
        self.label_3.setText(QCoreApplication.translate("ContractDialog", u"\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430: ", None))
        self.label_9.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439: ", None))
        self.label_5.setText(QCoreApplication.translate("ContractDialog", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430: ", None))
        self.label_6.setText(QCoreApplication.translate("ContractDialog", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b \u043f\u043e \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0443 (\u0442\u0435\u043a\u0441\u0442):", None))
        self.label_8.setText(QCoreApplication.translate("ContractDialog", u"\u0427\u0438\u0441\u043b\u043e \u043c\u0435\u0441\u044f\u0446\u0430: ", None))
        self.rb_fixed_period_curr.setText(QCoreApplication.translate("ContractDialog", u"\u043e\u0442\u0447\u0435\u0442\u043d\u044b\u0439", None))
        self.rb_fixed_period_next.setText(QCoreApplication.translate("ContractDialog", u"\u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439", None))
        self.rb_fixed_period_prev.setText(QCoreApplication.translate("ContractDialog", u"\u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439", None))
        self.pushButton_2.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pushButton.setText(QCoreApplication.translate("ContractDialog", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", None))
        self.rb_relative.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0441\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b (\u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0430 \u043a \u0441\u043e\u0431\u044b\u0442\u0438\u044e)", None))
    # retranslateUi

