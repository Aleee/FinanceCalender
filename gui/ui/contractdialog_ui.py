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
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_ContractDialog(object):
    def setupUi(self, ContractDialog):
        if not ContractDialog.objectName():
            ContractDialog.setObjectName(u"ContractDialog")
        ContractDialog.resize(540, 566)
        self.verticalLayout = QVBoxLayout(ContractDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gb_contract = QGroupBox(ContractDialog)
        self.gb_contract.setObjectName(u"gb_contract")
        self.gb_contract.setStyleSheet(u"QLineEdit, QDateEdit { background: palette(window); }")
        self.formLayout = QFormLayout(self.gb_contract)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.gb_contract)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.le_contractor = QLineEdit(self.gb_contract)
        self.le_contractor.setObjectName(u"le_contractor")
        self.le_contractor.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.le_contractor)

        self.label_2 = QLabel(self.gb_contract)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.le_contractname = QLineEdit(self.gb_contract)
        self.le_contractname.setObjectName(u"le_contractname")
        self.le_contractname.setReadOnly(True)

        self.horizontalLayout.addWidget(self.le_contractname)

        self.label_4 = QLabel(self.gb_contract)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.de_contractdate = QDateEdit(self.gb_contract)
        self.de_contractdate.setObjectName(u"de_contractdate")
        self.de_contractdate.setReadOnly(True)
        self.de_contractdate.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.horizontalLayout.addWidget(self.de_contractdate)


        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)


        self.verticalLayout.addWidget(self.gb_contract)

        self.gb_document = QGroupBox(ContractDialog)
        self.gb_document.setObjectName(u"gb_document")
        self.formLayout_2 = QFormLayout(self.gb_document)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_5 = QLabel(self.gb_document)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.le_documentname = QLineEdit(self.gb_document)
        self.le_documentname.setObjectName(u"le_documentname")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.le_documentname)

        self.label_3 = QLabel(self.gb_document)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.cmb_documenttype = QComboBox(self.gb_document)
        self.cmb_documenttype.setObjectName(u"cmb_documenttype")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cmb_documenttype)

        self.label_9 = QLabel(self.gb_document)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.cmb_responsible = QComboBox(self.gb_document)
        self.cmb_responsible.setObjectName(u"cmb_responsible")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cmb_responsible)


        self.verticalLayout.addWidget(self.gb_document)

        self.gb_terms = QGroupBox(ContractDialog)
        self.gb_terms.setObjectName(u"gb_terms")
        self.verticalLayout_2 = QVBoxLayout(self.gb_terms)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_6 = QLabel(self.gb_terms)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_2.addWidget(self.label_6)

        self.te_description = QPlainTextEdit(self.gb_terms)
        self.te_description.setObjectName(u"te_description")
        self.te_description.setMaximumSize(QSize(16777215, 80))

        self.verticalLayout_2.addWidget(self.te_description)

        self.rb_termsunknown = QRadioButton(self.gb_terms)
        self.rb_termsunknown.setObjectName(u"rb_termsunknown")

        self.verticalLayout_2.addWidget(self.rb_termsunknown)

        self.rb_relative = QRadioButton(self.gb_terms)
        self.rb_relative.setObjectName(u"rb_relative")

        self.verticalLayout_2.addWidget(self.rb_relative)

        self.fr_relative = QWidget(self.gb_terms)
        self.fr_relative.setObjectName(u"fr_relative")
        self.verticalLayout_3 = QVBoxLayout(self.fr_relative)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(24, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_7 = QLabel(self.fr_relative)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_3.addWidget(self.label_7)

        self.spb_rel_days = QSpinBox(self.fr_relative)
        self.spb_rel_days.setObjectName(u"spb_rel_days")
        self.spb_rel_days.setMaximum(365)

        self.horizontalLayout_3.addWidget(self.spb_rel_days)

        self.cmb_rel_daystype = QComboBox(self.fr_relative)
        self.cmb_rel_daystype.setObjectName(u"cmb_rel_daystype")

        self.horizontalLayout_3.addWidget(self.cmb_rel_daystype)

        self.label_11 = QLabel(self.fr_relative)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_3.addWidget(self.label_11)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.chb_rel_additional = QCheckBox(self.fr_relative)
        self.chb_rel_additional.setObjectName(u"chb_rel_additional")

        self.horizontalLayout_6.addWidget(self.chb_rel_additional)

        self.wdg_rel_dayofmonth = QWidget(self.fr_relative)
        self.wdg_rel_dayofmonth.setObjectName(u"wdg_rel_dayofmonth")
        self.horizontalLayout_2 = QHBoxLayout(self.wdg_rel_dayofmonth)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.spb_rel_dayofmonth = QSpinBox(self.wdg_rel_dayofmonth)
        self.spb_rel_dayofmonth.setObjectName(u"spb_rel_dayofmonth")
        self.spb_rel_dayofmonth.setMinimum(1)
        self.spb_rel_dayofmonth.setMaximum(31)

        self.horizontalLayout_2.addWidget(self.spb_rel_dayofmonth)

        self.label_10 = QLabel(self.wdg_rel_dayofmonth)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_2.addWidget(self.label_10)

        self.cmb_rel_month = QComboBox(self.wdg_rel_dayofmonth)
        self.cmb_rel_month.setObjectName(u"cmb_rel_month")

        self.horizontalLayout_2.addWidget(self.cmb_rel_month)

        self.label_12 = QLabel(self.wdg_rel_dayofmonth)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_2.addWidget(self.label_12)


        self.horizontalLayout_6.addWidget(self.wdg_rel_dayofmonth)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_8)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)


        self.verticalLayout_2.addWidget(self.fr_relative)

        self.rb_fixed = QRadioButton(self.gb_terms)
        self.rb_fixed.setObjectName(u"rb_fixed")

        self.verticalLayout_2.addWidget(self.rb_fixed)

        self.fr_fixed = QWidget(self.gb_terms)
        self.fr_fixed.setObjectName(u"fr_fixed")
        self.horizontalLayout_4 = QHBoxLayout(self.fr_fixed)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(24, 0, 0, 0)
        self.label_8 = QLabel(self.fr_fixed)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_4.addWidget(self.label_8)

        self.spb_fixed_dayofmonth = QSpinBox(self.fr_fixed)
        self.spb_fixed_dayofmonth.setObjectName(u"spb_fixed_dayofmonth")
        self.spb_fixed_dayofmonth.setMinimum(1)
        self.spb_fixed_dayofmonth.setMaximum(31)

        self.horizontalLayout_4.addWidget(self.spb_fixed_dayofmonth)

        self.label_13 = QLabel(self.fr_fixed)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_4.addWidget(self.label_13)

        self.cmb_fixed_month = QComboBox(self.fr_fixed)
        self.cmb_fixed_month.setObjectName(u"cmb_fixed_month")

        self.horizontalLayout_4.addWidget(self.cmb_fixed_month)

        self.label_14 = QLabel(self.fr_fixed)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_4.addWidget(self.label_14)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addWidget(self.fr_fixed)


        self.verticalLayout.addWidget(self.gb_terms)

        self.gb_monthly = QGroupBox(ContractDialog)
        self.gb_monthly.setObjectName(u"gb_monthly")
        self.verticalLayout_4 = QVBoxLayout(self.gb_monthly)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.chb_monthly = QCheckBox(self.gb_monthly)
        self.chb_monthly.setObjectName(u"chb_monthly")

        self.verticalLayout_4.addWidget(self.chb_monthly)

        self.wdg_monthly = QWidget(self.gb_monthly)
        self.wdg_monthly.setObjectName(u"wdg_monthly")
        self.gridLayout_monthly = QGridLayout(self.wdg_monthly)
        self.gridLayout_monthly.setObjectName(u"gridLayout_monthly")
        self.gridLayout_monthly.setContentsMargins(24, 0, 0, 0)
        self.label_15 = QLabel(self.wdg_monthly)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_monthly.addWidget(self.label_15, 0, 0, 1, 1)

        self.dsb_monthlyamount = QDoubleSpinBox(self.wdg_monthly)
        self.dsb_monthlyamount.setObjectName(u"dsb_monthlyamount")
        self.dsb_monthlyamount.setMinimumSize(QSize(120, 0))
        self.dsb_monthlyamount.setMaximumSize(QSize(120, 16777215))
        self.dsb_monthlyamount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_monthlyamount.setProperty(u"showGroupSeparator", True)
        self.dsb_monthlyamount.setMaximum(99999999.000000000000000)

        self.gridLayout_monthly.addWidget(self.dsb_monthlyamount, 0, 1, 1, 1)

        self.chb_byinvoice = QCheckBox(self.wdg_monthly)
        self.chb_byinvoice.setObjectName(u"chb_byinvoice")

        self.gridLayout_monthly.addWidget(self.chb_byinvoice, 0, 2, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_monthly.addItem(self.horizontalSpacer_5, 0, 3, 1, 1)

        self.la_monthlyname = QLabel(self.wdg_monthly)
        self.la_monthlyname.setObjectName(u"la_monthlyname")

        self.gridLayout_monthly.addWidget(self.la_monthlyname, 1, 0, 1, 1)

        self.le_monthlyname = QLineEdit(self.wdg_monthly)
        self.le_monthlyname.setObjectName(u"le_monthlyname")

        self.gridLayout_monthly.addWidget(self.le_monthlyname, 1, 1, 1, 3)


        self.verticalLayout_4.addWidget(self.wdg_monthly)


        self.verticalLayout.addWidget(self.gb_monthly)

        self.line = QFrame(ContractDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pb_history = QPushButton(ContractDialog)
        self.pb_history.setObjectName(u"pb_history")
        self.pb_history.setAutoDefault(False)

        self.horizontalLayout_buttons.addWidget(self.pb_history)

        self.buttonBox = QDialogButtonBox(ContractDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.horizontalLayout_buttons.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)

#if QT_CONFIG(shortcut)
        self.label_15.setBuddy(self.dsb_monthlyamount)
        self.la_monthlyname.setBuddy(self.le_monthlyname)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.le_documentname, self.cmb_documenttype)
        QWidget.setTabOrder(self.cmb_documenttype, self.cmb_responsible)
        QWidget.setTabOrder(self.cmb_responsible, self.te_description)
        QWidget.setTabOrder(self.te_description, self.rb_termsunknown)
        QWidget.setTabOrder(self.rb_termsunknown, self.rb_relative)
        QWidget.setTabOrder(self.rb_relative, self.spb_rel_days)
        QWidget.setTabOrder(self.spb_rel_days, self.cmb_rel_daystype)
        QWidget.setTabOrder(self.cmb_rel_daystype, self.chb_rel_additional)
        QWidget.setTabOrder(self.chb_rel_additional, self.spb_rel_dayofmonth)
        QWidget.setTabOrder(self.spb_rel_dayofmonth, self.cmb_rel_month)
        QWidget.setTabOrder(self.cmb_rel_month, self.rb_fixed)
        QWidget.setTabOrder(self.rb_fixed, self.spb_fixed_dayofmonth)
        QWidget.setTabOrder(self.spb_fixed_dayofmonth, self.cmb_fixed_month)
        QWidget.setTabOrder(self.cmb_fixed_month, self.chb_monthly)
        QWidget.setTabOrder(self.chb_monthly, self.dsb_monthlyamount)
        QWidget.setTabOrder(self.dsb_monthlyamount, self.chb_byinvoice)
        QWidget.setTabOrder(self.chb_byinvoice, self.le_monthlyname)
        QWidget.setTabOrder(self.le_monthlyname, self.pb_history)

        self.retranslateUi(ContractDialog)

        QMetaObject.connectSlotsByName(ContractDialog)
    # setupUi

    def retranslateUi(self, ContractDialog):
        ContractDialog.setWindowTitle(QCoreApplication.translate("ContractDialog", u"\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442", None))
        self.gb_contract.setTitle(QCoreApplication.translate("ContractDialog", u"\u0414\u043e\u0433\u043e\u0432\u043e\u0440", None))
        self.label.setText(QCoreApplication.translate("ContractDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442:", None))
        self.label_2.setText(QCoreApplication.translate("ContractDialog", u"\u0414\u043e\u0433\u043e\u0432\u043e\u0440 \u2116:", None))
        self.label_4.setText(QCoreApplication.translate("ContractDialog", u"\u043e\u0442", None))
        self.de_contractdate.setDisplayFormat(QCoreApplication.translate("ContractDialog", u"dd.MM.yyyy", None))
        self.gb_document.setTitle(QCoreApplication.translate("ContractDialog", u"\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442", None))
        self.label_5.setText(QCoreApplication.translate("ContractDialog", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:", None))
        self.le_documentname.setPlaceholderText(QCoreApplication.translate("ContractDialog", u"\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: \u0421\u0447\u0451\u0442 \u043d\u0430 \u043e\u043f\u043b\u0430\u0442\u0443 \u0443\u0441\u043b\u0443\u0433", None))
        self.label_3.setText(QCoreApplication.translate("ContractDialog", u"\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430:", None))
        self.cmb_documenttype.setPlaceholderText(QCoreApplication.translate("ContractDialog", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430", None))
        self.label_9.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", None))
        self.cmb_responsible.setPlaceholderText(QCoreApplication.translate("ContractDialog", u"\u041d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d", None))
        self.gb_terms.setTitle(QCoreApplication.translate("ContractDialog", u"\u0421\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.label_6.setText(QCoreApplication.translate("ContractDialog", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b \u043f\u043e \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0443 (\u0442\u0435\u043a\u0441\u0442):", None))
        self.te_description.setPlaceholderText(QCoreApplication.translate("ContractDialog", u"\u0412\u0441\u0442\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0440\u043c\u0443\u043b\u0438\u0440\u043e\u0432\u043a\u0443 \u0438\u0437 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430, \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: \u00ab\u041e\u043f\u043b\u0430\u0442\u0430 \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0435 10 \u0440\u0430\u0431\u043e\u0447\u0438\u0445 \u0434\u043d\u0435\u0439 \u0441 \u0434\u0430\u0442\u044b \u0432\u044b\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0438\u044f \u0441\u0447\u0451\u0442\u0430\u00bb", None))
        self.rb_termsunknown.setText(QCoreApplication.translate("ContractDialog", u"\u041f\u0440\u0435\u0434\u043e\u043f\u043b\u0430\u0442\u0430 / \u0421\u0440\u043e\u043a \u044f\u0432\u043d\u043e \u043d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d", None))
        self.rb_relative.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0441\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b (\u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0430 \u043a \u0441\u043e\u0431\u044b\u0442\u0438\u044e)", None))
        self.label_7.setText(QCoreApplication.translate("ContractDialog", u"\u041e\u043f\u043b\u0430\u0442\u0430 \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0435", None))
        self.label_11.setText(QCoreApplication.translate("ContractDialog", u"\u0434\u043d\u0435\u0439 \u043f\u043e\u0441\u043b\u0435 \u0441\u043e\u0431\u044b\u0442\u0438\u044f", None))
        self.chb_rel_additional.setText(QCoreApplication.translate("ContractDialog", u"\u043d\u043e \u043d\u0435 \u043f\u043e\u0437\u0434\u043d\u0435\u0435", None))
#if QT_CONFIG(tooltip)
        self.spb_rel_dayofmonth.setToolTip(QCoreApplication.translate("ContractDialog", u"\u0415\u0441\u043b\u0438 \u0432 \u043c\u0435\u0441\u044f\u0446\u0435 \u043c\u0435\u043d\u044c\u0448\u0435 \u0434\u043d\u0435\u0439, \u0431\u0435\u0440\u0451\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u0434\u0435\u043d\u044c \u043c\u0435\u0441\u044f\u0446\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("ContractDialog", u"\u0447\u0438\u0441\u043b\u0430", None))
        self.label_12.setText(QCoreApplication.translate("ContractDialog", u"\u043c\u0435\u0441\u044f\u0446\u0430", None))
        self.rb_fixed.setText(QCoreApplication.translate("ContractDialog", u"\u0424\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0441\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b (\u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0430 \u043a \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044e)", None))
        self.label_8.setText(QCoreApplication.translate("ContractDialog", u"\u041d\u0435 \u043f\u043e\u0437\u0434\u043d\u0435\u0435", None))
#if QT_CONFIG(tooltip)
        self.spb_fixed_dayofmonth.setToolTip(QCoreApplication.translate("ContractDialog", u"\u0415\u0441\u043b\u0438 \u0432 \u043c\u0435\u0441\u044f\u0446\u0435 \u043c\u0435\u043d\u044c\u0448\u0435 \u0434\u043d\u0435\u0439, \u0431\u0435\u0440\u0451\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u0434\u0435\u043d\u044c \u043c\u0435\u0441\u044f\u0446\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_13.setText(QCoreApplication.translate("ContractDialog", u"\u0447\u0438\u0441\u043b\u0430", None))
        self.label_14.setText(QCoreApplication.translate("ContractDialog", u"\u043c\u0435\u0441\u044f\u0446\u0430", None))
        self.gb_monthly.setTitle(QCoreApplication.translate("ContractDialog", u"\u0415\u0436\u0435\u043c\u0435\u0441\u044f\u0447\u043d\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436", None))
#if QT_CONFIG(tooltip)
        self.chb_monthly.setToolTip(QCoreApplication.translate("ContractDialog", u"\u0412 \u043f\u0435\u0440\u0435\u0447\u043d\u0435 \u0435\u0436\u0435\u043c\u0435\u0441\u044f\u0447\u043d\u044b\u0445 \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439 (Ctrl+Shift+K) \u0434\u043b\u044f \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u043c\u0435\u0441\u044f\u0446\u0430 \u0431\u0443\u0434\u0435\u0442 \u0432\u0438\u0434\u043d\u043e, \u0441\u043e\u0437\u0434\u0430\u043d \u043b\u0438 \u043f\u043b\u0430\u0442\u0435\u0436 \u043f\u043e \u044d\u0442\u043e\u043c\u0443 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0443", None))
#endif // QT_CONFIG(tooltip)
        self.chb_monthly.setText(QCoreApplication.translate("ContractDialog", u"\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0432 \u043f\u0435\u0440\u0435\u0447\u0435\u043d\u044c \u0435\u0436\u0435\u043c\u0435\u0441\u044f\u0447\u043d\u044b\u0445 \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439", None))
        self.label_15.setText(QCoreApplication.translate("ContractDialog", u"\u0421\u0443\u043c\u043c\u0430 \u0432 \u043c\u0435\u0441\u044f\u0446:", None))
#if QT_CONFIG(tooltip)
        self.chb_byinvoice.setToolTip(QCoreApplication.translate("ContractDialog", u"\u0415\u0441\u043b\u0438 \u0441\u0443\u043c\u043c\u0430 \u043a\u0430\u0436\u0434\u044b\u0439 \u043c\u0435\u0441\u044f\u0446 \u0440\u0430\u0437\u043d\u0430\u044f (\u0443\u043a\u0430\u0437\u0430\u043d\u0430 \u0432 \u0441\u0447\u0451\u0442\u0435 \u0438\u043b\u0438 \u0430\u043a\u0442\u0435), \u043e\u0442\u043c\u0435\u0442\u044c\u0442\u0435 \u044d\u0442\u043e\u0442 \u043f\u0443\u043d\u043a\u0442", None))
#endif // QT_CONFIG(tooltip)
        self.chb_byinvoice.setText(QCoreApplication.translate("ContractDialog", u"\u041f\u043e \u0441\u0447\u0451\u0442\u0443", None))
        self.la_monthlyname.setText(QCoreApplication.translate("ContractDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
#if QT_CONFIG(tooltip)
        self.le_monthlyname.setToolTip(QCoreApplication.translate("ContractDialog", u"\u0415\u0441\u043b\u0438 \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u043e, \u043d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430 \u0431\u0435\u0440\u0451\u0442\u0441\u044f \u043e\u0442\u0441\u044e\u0434\u0430, \u0430 \u043d\u0435 \u0438\u0437 \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0445 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0439. \u041c\u043e\u0436\u043d\u043e \u043f\u0438\u0441\u0430\u0442\u044c {\u043c\u0435\u0441\u044f\u0446} \u0438 {\u0433\u043e\u0434} - \u043e\u043d\u0438 \u0437\u0430\u043c\u0435\u043d\u044f\u0442\u0441\u044f \u043d\u0430 \u043c\u0435\u0441\u044f\u0446 \u0438 \u0433\u043e\u0434 \u043f\u0435\u0440\u0438\u043e\u0434\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.le_monthlyname.setPlaceholderText(QCoreApplication.translate("ContractDialog", u"\u0438\u0437 \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0445 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0439", None))
        self.pb_history.setText(QCoreApplication.translate("ContractDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438\u2026", None))
    # retranslateUi

