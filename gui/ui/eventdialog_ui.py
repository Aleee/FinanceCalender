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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDateEdit, QDialog, QDoubleSpinBox, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QPlainTextEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QToolButton, QVBoxLayout, QWidget)

from gui.commonwidgets.completingtextedit import CompletingPlainTextEdit
import resources_rc

class Ui_EventDialog(object):
    def setupUi(self, EventDialog):
        if not EventDialog.objectName():
            EventDialog.setObjectName(u"EventDialog")
        EventDialog.resize(789, 579)
        self.gridLayout_2 = QGridLayout(EventDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.gridLayout_2.setHorizontalSpacing(10)
        self.gridLayout_2.setVerticalSpacing(8)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.formLayout.setHorizontalSpacing(10)
        self.formLayout.setVerticalSpacing(8)
        self.label = QLabel(EventDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.le_receiver = QLineEdit(EventDialog)
        self.le_receiver.setObjectName(u"le_receiver")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.le_receiver)

        self.label_2 = QLabel(EventDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.te_name = CompletingPlainTextEdit(EventDialog)
        self.te_name.setObjectName(u"te_name")
        self.te_name.setMinimumSize(QSize(0, 50))
        self.te_name.setMaximumSize(QSize(16777215, 50))

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.te_name)

        self.label_16 = QLabel(EventDialog)
        self.label_16.setObjectName(u"label_16")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_16)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(4)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.la_contract = QLabel(EventDialog)
        self.la_contract.setObjectName(u"la_contract")

        self.horizontalLayout_9.addWidget(self.la_contract)

        self.tb_unbindcontract = QToolButton(EventDialog)
        self.tb_unbindcontract.setObjectName(u"tb_unbindcontract")
        self.tb_unbindcontract.setAutoRaise(True)

        self.horizontalLayout_9.addWidget(self.tb_unbindcontract)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_4)


        self.formLayout.setLayout(2, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_9)

        self.verticalSpacer_2 = QSpacerItem(20, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.formLayout.setItem(3, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer_2)

        self.label_3 = QLabel(EventDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.dsb_totalamount = QDoubleSpinBox(EventDialog)
        self.dsb_totalamount.setObjectName(u"dsb_totalamount")
        self.dsb_totalamount.setMinimumSize(QSize(110, 0))
        self.dsb_totalamount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_totalamount.setMaximum(99999999.000000000000000)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.dsb_totalamount)

        self.label_13 = QLabel(EventDialog)
        self.label_13.setObjectName(u"label_13")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_13)

        self.de_incurrencedate = QDateEdit(EventDialog)
        self.de_incurrencedate.setObjectName(u"de_incurrencedate")
        self.de_incurrencedate.setCalendarPopup(True)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.de_incurrencedate)

        self.label_4 = QLabel(EventDialog)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.de_duedate = QDateEdit(EventDialog)
        self.de_duedate.setObjectName(u"de_duedate")
        self.de_duedate.setCalendarPopup(True)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.de_duedate)

        self.verticalSpacer_4 = QSpacerItem(20, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.formLayout.setItem(7, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer_4)

        self.label_5 = QLabel(EventDialog)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.cmb_category = QComboBox(EventDialog)
        self.cmb_category.setObjectName(u"cmb_category")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmb_category.sizePolicy().hasHeightForWidth())
        self.cmb_category.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.cmb_category)

        self.label_11 = QLabel(EventDialog)
        self.label_11.setObjectName(u"label_11")

        self.formLayout.setWidget(9, QFormLayout.ItemRole.LabelRole, self.label_11)

        self.cmb_subcategory = QComboBox(EventDialog)
        self.cmb_subcategory.setObjectName(u"cmb_subcategory")
        sizePolicy.setHeightForWidth(self.cmb_subcategory.sizePolicy().hasHeightForWidth())
        self.cmb_subcategory.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(9, QFormLayout.ItemRole.FieldRole, self.cmb_subcategory)

        self.label_10 = QLabel(EventDialog)
        self.label_10.setObjectName(u"label_10")

        self.formLayout.setWidget(10, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.cmb_nds = QComboBox(EventDialog)
        self.cmb_nds.setObjectName(u"cmb_nds")

        self.formLayout.setWidget(10, QFormLayout.ItemRole.FieldRole, self.cmb_nds)

        self.label_8 = QLabel(EventDialog)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(11, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(12)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.rb_typenormal = QRadioButton(EventDialog)
        self.rb_typenormal.setObjectName(u"rb_typenormal")

        self.horizontalLayout_6.addWidget(self.rb_typenormal)

        self.rb_typeadvance = QRadioButton(EventDialog)
        self.rb_typeadvance.setObjectName(u"rb_typeadvance")

        self.horizontalLayout_6.addWidget(self.rb_typeadvance)

        self.rb_typerefund = QRadioButton(EventDialog)
        self.rb_typerefund.setObjectName(u"rb_typerefund")

        self.horizontalLayout_6.addWidget(self.rb_typerefund)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)


        self.formLayout.setLayout(11, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_6)

        self.label_7 = QLabel(EventDialog)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(12, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(4)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.cmb_responsible = QComboBox(EventDialog)
        self.cmb_responsible.setObjectName(u"cmb_responsible")
        self.cmb_responsible.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_7.addWidget(self.cmb_responsible)

        self.tb_responsible = QToolButton(EventDialog)
        self.tb_responsible.setObjectName(u"tb_responsible")

        self.horizontalLayout_7.addWidget(self.tb_responsible)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_9)


        self.formLayout.setLayout(12, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_7)

        self.verticalSpacer_5 = QSpacerItem(20, 4, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.formLayout.setItem(13, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer_5)

        self.label_6 = QLabel(EventDialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(14, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.te_descr = CompletingPlainTextEdit(EventDialog)
        self.te_descr.setObjectName(u"te_descr")
        self.te_descr.setMinimumSize(QSize(0, 50))
        self.te_descr.setMaximumSize(QSize(16777215, 50))

        self.formLayout.setWidget(14, QFormLayout.ItemRole.FieldRole, self.te_descr)

        self.label_9 = QLabel(EventDialog)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(15, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.te_notes = QPlainTextEdit(EventDialog)
        self.te_notes.setObjectName(u"te_notes")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.te_notes.sizePolicy().hasHeightForWidth())
        self.te_notes.setSizePolicy(sizePolicy1)
        self.te_notes.setMinimumSize(QSize(0, 45))
        self.te_notes.setTabChangesFocus(True)

        self.formLayout.setWidget(15, QFormLayout.ItemRole.FieldRole, self.te_notes)


        self.gridLayout_2.addLayout(self.formLayout, 0, 0, 1, 1)

        self.wdg_contract = QWidget(EventDialog)
        self.wdg_contract.setObjectName(u"wdg_contract")
        self.verticalLayout_2 = QVBoxLayout(self.wdg_contract)
        self.verticalLayout_2.setSpacing(8)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setHorizontalSpacing(10)
        self.gridLayout_5.setVerticalSpacing(8)
        self.label_15 = QLabel(self.wdg_contract)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_5.addWidget(self.label_15, 0, 0, 1, 1)

        self.cmb_contractor = QComboBox(self.wdg_contract)
        self.cmb_contractor.setObjectName(u"cmb_contractor")
        sizePolicy.setHeightForWidth(self.cmb_contractor.sizePolicy().hasHeightForWidth())
        self.cmb_contractor.setSizePolicy(sizePolicy)
        self.cmb_contractor.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_contractor.setMinimumContentsLength(24)

        self.gridLayout_5.addWidget(self.cmb_contractor, 0, 1, 1, 1)

        self.label_14 = QLabel(self.wdg_contract)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_5.addWidget(self.label_14, 1, 0, 1, 1)

        self.cmb_contract = QComboBox(self.wdg_contract)
        self.cmb_contract.setObjectName(u"cmb_contract")
        sizePolicy.setHeightForWidth(self.cmb_contract.sizePolicy().hasHeightForWidth())
        self.cmb_contract.setSizePolicy(sizePolicy)
        self.cmb_contract.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_contract.setMinimumContentsLength(24)

        self.gridLayout_5.addWidget(self.cmb_contract, 1, 1, 1, 1)

        self.label_18 = QLabel(self.wdg_contract)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_5.addWidget(self.label_18, 2, 0, 1, 1)

        self.cmb_document = QComboBox(self.wdg_contract)
        self.cmb_document.setObjectName(u"cmb_document")
        sizePolicy.setHeightForWidth(self.cmb_document.sizePolicy().hasHeightForWidth())
        self.cmb_document.setSizePolicy(sizePolicy)
        self.cmb_document.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_document.setMinimumContentsLength(24)

        self.gridLayout_5.addWidget(self.cmb_document, 2, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_5)

        self.wdg_contractterms = QWidget(self.wdg_contract)
        self.wdg_contractterms.setObjectName(u"wdg_contractterms")
        self.verticalLayout = QVBoxLayout(self.wdg_contractterms)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pb_bindcontract = QPushButton(self.wdg_contractterms)
        self.pb_bindcontract.setObjectName(u"pb_bindcontract")

        self.verticalLayout.addWidget(self.pb_bindcontract)

        self.line_8 = QFrame(self.wdg_contractterms)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.Shape.HLine)
        self.line_8.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_8)

        self.label_20 = QLabel(self.wdg_contractterms)
        self.label_20.setObjectName(u"label_20")

        self.verticalLayout.addWidget(self.label_20)

        self.te_paytermsdescr = QPlainTextEdit(self.wdg_contractterms)
        self.te_paytermsdescr.setObjectName(u"te_paytermsdescr")
        self.te_paytermsdescr.setMaximumSize(QSize(16777215, 80))
        self.te_paytermsdescr.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.te_paytermsdescr.setStyleSheet(u"QPlainTextEdit { background: palette(window); }")
        self.te_paytermsdescr.setReadOnly(True)

        self.verticalLayout.addWidget(self.te_paytermsdescr)

        self.wdg_relative = QWidget(self.wdg_contractterms)
        self.wdg_relative.setObjectName(u"wdg_relative")
        self.gridLayout_10 = QGridLayout(self.wdg_relative)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_19 = QLabel(self.wdg_relative)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_10.addWidget(self.label_19, 0, 0, 1, 1)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.de_paymenttrigger = QDateEdit(self.wdg_relative)
        self.de_paymenttrigger.setObjectName(u"de_paymenttrigger")
        self.de_paymenttrigger.setCalendarPopup(True)

        self.horizontalLayout_11.addWidget(self.de_paymenttrigger)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_16)


        self.gridLayout_10.addLayout(self.horizontalLayout_11, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.wdg_relative)

        self.wdg_fixedmonth = QWidget(self.wdg_contractterms)
        self.wdg_fixedmonth.setObjectName(u"wdg_fixedmonth")
        self.gridLayout_9 = QGridLayout(self.wdg_fixedmonth)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_21 = QLabel(self.wdg_fixedmonth)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_9.addWidget(self.label_21, 0, 0, 1, 1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.cmb_paymentperiodmonth = QComboBox(self.wdg_fixedmonth)
        self.cmb_paymentperiodmonth.setObjectName(u"cmb_paymentperiodmonth")

        self.horizontalLayout_12.addWidget(self.cmb_paymentperiodmonth)

        self.spb_paymentperiodyear = QSpinBox(self.wdg_fixedmonth)
        self.spb_paymentperiodyear.setObjectName(u"spb_paymentperiodyear")
        self.spb_paymentperiodyear.setMinimum(2000)
        self.spb_paymentperiodyear.setMaximum(2100)

        self.horizontalLayout_12.addWidget(self.spb_paymentperiodyear)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_17)


        self.gridLayout_9.addLayout(self.horizontalLayout_12, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.wdg_fixedmonth)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_22 = QLabel(self.wdg_contractterms)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout_13.addWidget(self.label_22)

        self.la_calculatedpaymentdate = QLabel(self.wdg_contractterms)
        self.la_calculatedpaymentdate.setObjectName(u"la_calculatedpaymentdate")
        font = QFont()
        font.setBold(True)
        self.la_calculatedpaymentdate.setFont(font)

        self.horizontalLayout_13.addWidget(self.la_calculatedpaymentdate)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_18)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.pb_applypaymentdate = QPushButton(self.wdg_contractterms)
        self.pb_applypaymentdate.setObjectName(u"pb_applypaymentdate")

        self.verticalLayout.addWidget(self.pb_applypaymentdate)

        self.line_10 = QFrame(self.wdg_contractterms)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFrameShape(QFrame.Shape.HLine)
        self.line_10.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_10)

        self.pb_fillwithvalues = QPushButton(self.wdg_contractterms)
        self.pb_fillwithvalues.setObjectName(u"pb_fillwithvalues")

        self.verticalLayout.addWidget(self.pb_fillwithvalues)

        self.pb_savevalues = QPushButton(self.wdg_contractterms)
        self.pb_savevalues.setObjectName(u"pb_savevalues")

        self.verticalLayout.addWidget(self.pb_savevalues)


        self.verticalLayout_2.addWidget(self.wdg_contractterms)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.gridLayout_2.addWidget(self.wdg_contract, 0, 2, 1, 1)

        self.pb_toggle = QPushButton(EventDialog)
        self.pb_toggle.setObjectName(u"pb_toggle")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pb_toggle.sizePolicy().hasHeightForWidth())
        self.pb_toggle.setSizePolicy(sizePolicy2)
        self.pb_toggle.setMaximumSize(QSize(20, 16777215))
        icon = QIcon()
        icon.addFile(u":/designer/icons/right.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_toggle.setIcon(icon)

        self.gridLayout_2.addWidget(self.pb_toggle, 0, 1, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.chb_hidden = QCheckBox(EventDialog)
        self.chb_hidden.setObjectName(u"chb_hidden")

        self.horizontalLayout_3.addWidget(self.chb_hidden)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_8)

        self.pb_cancel = QPushButton(EventDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")
        self.pb_cancel.setAutoDefault(False)

        self.horizontalLayout_3.addWidget(self.pb_cancel)

        self.horizontalSpacer = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.pb_accept = QPushButton(EventDialog)
        self.pb_accept.setObjectName(u"pb_accept")

        self.horizontalLayout_3.addWidget(self.pb_accept)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 3, 0, 1, 3)

        self.line_7 = QFrame(EventDialog)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.Shape.HLine)
        self.line_7.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_7, 1, 0, 1, 3)

        self.verticalSpacer_3 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_3, 2, 0, 1, 1)

        self.gridLayout_2.setRowStretch(0, 1)
        self.gridLayout_2.setColumnStretch(0, 1)
#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.le_receiver)
        self.label_2.setBuddy(self.te_name)
        self.label_3.setBuddy(self.dsb_totalamount)
        self.label_13.setBuddy(self.de_incurrencedate)
        self.label_4.setBuddy(self.de_duedate)
        self.label_5.setBuddy(self.cmb_category)
        self.label_11.setBuddy(self.cmb_subcategory)
        self.label_10.setBuddy(self.cmb_nds)
        self.label_7.setBuddy(self.cmb_responsible)
        self.label_6.setBuddy(self.te_descr)
        self.label_9.setBuddy(self.te_notes)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.le_receiver, self.te_name)
        QWidget.setTabOrder(self.te_name, self.tb_unbindcontract)
        QWidget.setTabOrder(self.tb_unbindcontract, self.dsb_totalamount)
        QWidget.setTabOrder(self.dsb_totalamount, self.de_incurrencedate)
        QWidget.setTabOrder(self.de_incurrencedate, self.de_duedate)
        QWidget.setTabOrder(self.de_duedate, self.cmb_category)
        QWidget.setTabOrder(self.cmb_category, self.cmb_subcategory)
        QWidget.setTabOrder(self.cmb_subcategory, self.cmb_nds)
        QWidget.setTabOrder(self.cmb_nds, self.rb_typenormal)
        QWidget.setTabOrder(self.rb_typenormal, self.rb_typeadvance)
        QWidget.setTabOrder(self.rb_typeadvance, self.rb_typerefund)
        QWidget.setTabOrder(self.rb_typerefund, self.cmb_responsible)
        QWidget.setTabOrder(self.cmb_responsible, self.tb_responsible)
        QWidget.setTabOrder(self.tb_responsible, self.te_descr)
        QWidget.setTabOrder(self.te_descr, self.te_notes)
        QWidget.setTabOrder(self.te_notes, self.chb_hidden)
        QWidget.setTabOrder(self.chb_hidden, self.pb_cancel)
        QWidget.setTabOrder(self.pb_cancel, self.pb_toggle)
        QWidget.setTabOrder(self.pb_toggle, self.cmb_contractor)
        QWidget.setTabOrder(self.cmb_contractor, self.cmb_contract)
        QWidget.setTabOrder(self.cmb_contract, self.cmb_document)
        QWidget.setTabOrder(self.cmb_document, self.pb_bindcontract)
        QWidget.setTabOrder(self.pb_bindcontract, self.de_paymenttrigger)
        QWidget.setTabOrder(self.de_paymenttrigger, self.cmb_paymentperiodmonth)
        QWidget.setTabOrder(self.cmb_paymentperiodmonth, self.spb_paymentperiodyear)
        QWidget.setTabOrder(self.spb_paymentperiodyear, self.pb_applypaymentdate)
        QWidget.setTabOrder(self.pb_applypaymentdate, self.pb_fillwithvalues)
        QWidget.setTabOrder(self.pb_fillwithvalues, self.pb_savevalues)

        self.retranslateUi(EventDialog)

        self.pb_accept.setDefault(True)


        QMetaObject.connectSlotsByName(EventDialog)
    # setupUi

    def retranslateUi(self, EventDialog):
        EventDialog.setWindowTitle(QCoreApplication.translate("EventDialog", u"\u041d\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436", None))
        self.label.setText(QCoreApplication.translate("EventDialog", u"&\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.label_2.setText(QCoreApplication.translate("EventDialog", u"&\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.label_16.setText(QCoreApplication.translate("EventDialog", u"\u0414\u043e\u0433\u043e\u0432\u043e\u0440:", None))
#if QT_CONFIG(tooltip)
        self.la_contract.setToolTip(QCoreApplication.translate("EventDialog", u"\u041f\u0440\u0438\u0432\u044f\u0437\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u043a \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0443 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430 \u043c\u043e\u0436\u043d\u043e \u0432 \u043f\u0430\u043d\u0435\u043b\u0438 \u0441\u043f\u0440\u0430\u0432\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.la_contract.setText(QCoreApplication.translate("EventDialog", u"\u043d\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d", None))
#if QT_CONFIG(tooltip)
        self.tb_unbindcontract.setToolTip(QCoreApplication.translate("EventDialog", u"\u041e\u0442\u0432\u044f\u0437\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u043e\u0442 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.tb_unbindcontract.setText(QCoreApplication.translate("EventDialog", u"\u2715", None))
        self.label_3.setText(QCoreApplication.translate("EventDialog", u"&\u0421\u0443\u043c\u043c\u0430:", None))
#if QT_CONFIG(tooltip)
        self.label_13.setToolTip(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_13.setText(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430 &\u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f:", None))
#if QT_CONFIG(tooltip)
        self.de_incurrencedate.setToolTip(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430 \u043f\u043b\u0430&\u0442\u0435\u0436\u0430:", None))
        self.label_5.setText(QCoreApplication.translate("EventDialog", u"&\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", None))
        self.label_11.setText(QCoreApplication.translate("EventDialog", u"\u041f\u043e\u0434\u043a\u0430\u0442\u0435&\u0433\u043e\u0440\u0438\u044f:", None))
        self.label_10.setText(QCoreApplication.translate("EventDialog", u"\u041d&\u0414\u0421:", None))
#if QT_CONFIG(tooltip)
        self.cmb_nds.setToolTip(QCoreApplication.translate("EventDialog", u"\u041f\u043e\u0434\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u0438 \u0432\u044b\u0431\u043e\u0440\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.label_8.setText(QCoreApplication.translate("EventDialog", u"\u0412\u0438\u0434:", None))
        self.rb_typenormal.setText(QCoreApplication.translate("EventDialog", u"\u043f\u043e &\u0444\u0430\u043a\u0442\u0443", None))
        self.rb_typeadvance.setText(QCoreApplication.translate("EventDialog", u"\u043f\u0440&\u0435\u0434\u043e\u043f\u043b\u0430\u0442\u0430", None))
        self.rb_typerefund.setText(QCoreApplication.translate("EventDialog", u"\u0432\u043e&\u0437\u0432\u0440\u0430\u0442", None))
        self.label_7.setText(QCoreApplication.translate("EventDialog", u"&\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", None))
#if QT_CONFIG(tooltip)
        self.tb_responsible.setToolTip(QCoreApplication.translate("EventDialog", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u043e \u0437\u0430\u043d\u0438\u043c\u0430\u0435\u043c\u043e\u0439 \u0434\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.tb_responsible.setText(QCoreApplication.translate("EventDialog", u"\u041f\u043e \u0434\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0438\u2026", None))
        self.label_6.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0441\u043d\u043e\u0432&\u0430\u043d\u0438\u0435:", None))
        self.label_9.setText(QCoreApplication.translate("EventDialog", u"\u0417\u0430&\u043c\u0435\u0442\u043a\u0438:", None))
        self.label_15.setText(QCoreApplication.translate("EventDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442:", None))
        self.label_14.setText(QCoreApplication.translate("EventDialog", u"\u0414\u043e\u0433\u043e\u0432\u043e\u0440:", None))
        self.label_18.setText(QCoreApplication.translate("EventDialog", u"\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442:", None))
        self.pb_bindcontract.setText(QCoreApplication.translate("EventDialog", u"\u041f\u0440\u0438\u0432\u044f\u0437\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u043a \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0443", None))
        self.label_20.setText(QCoreApplication.translate("EventDialog", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.label_19.setText(QCoreApplication.translate("EventDialog", u"\u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430:", None))
        self.label_21.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0442\u0447\u0435\u0442\u043d\u044b\u0439 \u043c\u0435\u0441\u044f\u0446:", None))
        self.label_22.setText(QCoreApplication.translate("EventDialog", u"\u0420\u0430\u0441\u0447\u0435\u0442\u043d\u0430\u044f \u0434\u0430\u0442\u0430:", None))
        self.la_calculatedpaymentdate.setText(QCoreApplication.translate("EventDialog", u"\u2014", None))
#if QT_CONFIG(tooltip)
        self.pb_applypaymentdate.setToolTip(QCoreApplication.translate("EventDialog", u"\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e, \u043a\u043e\u0433\u0434\u0430 \u043f\u043b\u0430\u0442\u0435\u0436 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d \u043a \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u043e\u043c\u0443 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0443", None))
#endif // QT_CONFIG(tooltip)
        self.pb_applypaymentdate.setText(QCoreApplication.translate("EventDialog", u"\u2190 \u041f\u043e\u0434\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0434\u0430\u0442\u0443", None))
        self.pb_fillwithvalues.setText(QCoreApplication.translate("EventDialog", u"\u2190 \u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u043f\u043e\u043b\u044f \u0438\u0437 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430", None))
        self.pb_savevalues.setText(QCoreApplication.translate("EventDialog", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043f\u043e\u043b\u044f \u0432 \u0434\u043e\u0433\u043e\u0432\u043e\u0440 \u2192", None))
#if QT_CONFIG(tooltip)
        self.pb_toggle.setToolTip(QCoreApplication.translate("EventDialog", u"\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0438\u043b\u0438 \u0441\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043d\u0435\u043b\u044c \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.pb_toggle.setText("")
        self.chb_hidden.setText(QCoreApplication.translate("EventDialog", u"\u0421\u043a\u0440&\u044b\u0442\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436", None))
        self.pb_cancel.setText(QCoreApplication.translate("EventDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_accept.setText(QCoreApplication.translate("EventDialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
    # retranslateUi

