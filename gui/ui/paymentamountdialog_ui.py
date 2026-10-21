# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'paymentamountdialog.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QDateEdit,
    QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_PaymentAmountDialog(object):
    def setupUi(self, PaymentAmountDialog):
        if not PaymentAmountDialog.objectName():
            PaymentAmountDialog.setObjectName(u"PaymentAmountDialog")
        PaymentAmountDialog.resize(480, 360)
        PaymentAmountDialog.setMinimumSize(QSize(480, 0))
        self.gridLayout = QGridLayout(PaymentAmountDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gb_info = QGroupBox(PaymentAmountDialog)
        self.gb_info.setObjectName(u"gb_info")
        self.formLayout_info = QFormLayout(self.gb_info)
        self.formLayout_info.setObjectName(u"formLayout_info")
        self.label_receiver = QLabel(self.gb_info)
        self.label_receiver.setObjectName(u"label_receiver")

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_receiver)

        self.lbl_receiver = QLabel(self.gb_info)
        self.lbl_receiver.setObjectName(u"lbl_receiver")
        self.lbl_receiver.setWordWrap(True)

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lbl_receiver)

        self.label_name = QLabel(self.gb_info)
        self.label_name.setObjectName(u"label_name")

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_name)

        self.lbl_name = QLabel(self.gb_info)
        self.lbl_name.setObjectName(u"lbl_name")
        self.lbl_name.setWordWrap(True)

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lbl_name)

        self.label_duedate = QLabel(self.gb_info)
        self.label_duedate.setObjectName(u"label_duedate")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_duedate)

        self.lbl_duedate = QLabel(self.gb_info)
        self.lbl_duedate.setObjectName(u"lbl_duedate")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lbl_duedate)

        self.label_paidbefore = QLabel(self.gb_info)
        self.label_paidbefore.setObjectName(u"label_paidbefore")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_paidbefore)

        self.lbl_paidbefore = QLabel(self.gb_info)
        self.lbl_paidbefore.setObjectName(u"lbl_paidbefore")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.FieldRole, self.lbl_paidbefore)

        self.label_remain = QLabel(self.gb_info)
        self.label_remain.setObjectName(u"label_remain")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_remain)

        self.lbl_remain = QLabel(self.gb_info)
        self.lbl_remain.setObjectName(u"lbl_remain")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.FieldRole, self.lbl_remain)


        self.gridLayout.addWidget(self.gb_info, 0, 0, 1, 1)

        self.gb_amounts = QGroupBox(PaymentAmountDialog)
        self.gb_amounts.setObjectName(u"gb_amounts")
        self.formLayout_amounts = QFormLayout(self.gb_amounts)
        self.formLayout_amounts.setObjectName(u"formLayout_amounts")
        self.lbl_paymentdate = QLabel(self.gb_amounts)
        self.lbl_paymentdate.setObjectName(u"lbl_paymentdate")

        self.formLayout_amounts.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_paymentdate)

        self.horizontalLayout_paymentdate = QHBoxLayout()
        self.horizontalLayout_paymentdate.setObjectName(u"horizontalLayout_paymentdate")
        self.de_paymentdate = QDateEdit(self.gb_amounts)
        self.de_paymentdate.setObjectName(u"de_paymentdate")
        self.de_paymentdate.setMinimumSize(QSize(130, 0))
        self.de_paymentdate.setCalendarPopup(True)

        self.horizontalLayout_paymentdate.addWidget(self.de_paymentdate)

        self.horizontalSpacer_paymentdate = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_paymentdate.addItem(self.horizontalSpacer_paymentdate)


        self.formLayout_amounts.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_paymentdate)

        self.lbl_payment = QLabel(self.gb_amounts)
        self.lbl_payment.setObjectName(u"lbl_payment")

        self.formLayout_amounts.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_payment)

        self.horizontalLayout_payment = QHBoxLayout()
        self.horizontalLayout_payment.setObjectName(u"horizontalLayout_payment")
        self.dsb_payment = QDoubleSpinBox(self.gb_amounts)
        self.dsb_payment.setObjectName(u"dsb_payment")
        self.dsb_payment.setMinimumSize(QSize(130, 0))
        self.dsb_payment.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_payment.setProperty(u"showGroupSeparator", True)
        self.dsb_payment.setMaximum(99999999.000000000000000)

        self.horizontalLayout_payment.addWidget(self.dsb_payment)

        self.horizontalSpacer_payment = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_payment.addItem(self.horizontalSpacer_payment)


        self.formLayout_amounts.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_payment)

        self.chb_changetotal = QCheckBox(self.gb_amounts)
        self.chb_changetotal.setObjectName(u"chb_changetotal")
        self.chb_changetotal.setChecked(True)

        self.formLayout_amounts.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.chb_changetotal)

        self.label_total = QLabel(self.gb_amounts)
        self.label_total.setObjectName(u"label_total")

        self.formLayout_amounts.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_total)

        self.horizontalLayout_total = QHBoxLayout()
        self.horizontalLayout_total.setObjectName(u"horizontalLayout_total")
        self.dsb_total = QDoubleSpinBox(self.gb_amounts)
        self.dsb_total.setObjectName(u"dsb_total")
        self.dsb_total.setMinimumSize(QSize(130, 0))
        self.dsb_total.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_total.setProperty(u"showGroupSeparator", True)
        self.dsb_total.setMaximum(99999999.000000000000000)

        self.horizontalLayout_total.addWidget(self.dsb_total)

        self.horizontalSpacer_total = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_total.addItem(self.horizontalSpacer_total)


        self.formLayout_amounts.setLayout(3, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_total)


        self.gridLayout.addWidget(self.gb_amounts, 1, 0, 1, 1)

        self.line = QFrame(PaymentAmountDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 2, 0, 1, 1)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pb_deletepayment = QPushButton(PaymentAmountDialog)
        self.pb_deletepayment.setObjectName(u"pb_deletepayment")
        self.pb_deletepayment.setAutoDefault(False)

        self.horizontalLayout_buttons.addWidget(self.pb_deletepayment)

        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)

        self.pb_cancel = QPushButton(PaymentAmountDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout_buttons.addWidget(self.pb_cancel)

        self.pb_accept = QPushButton(PaymentAmountDialog)
        self.pb_accept.setObjectName(u"pb_accept")

        self.horizontalLayout_buttons.addWidget(self.pb_accept)


        self.gridLayout.addLayout(self.horizontalLayout_buttons, 3, 0, 1, 1)

#if QT_CONFIG(shortcut)
        self.lbl_paymentdate.setBuddy(self.de_paymentdate)
        self.lbl_payment.setBuddy(self.dsb_payment)
        self.label_total.setBuddy(self.dsb_total)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.de_paymentdate, self.dsb_payment)
        QWidget.setTabOrder(self.dsb_payment, self.chb_changetotal)
        QWidget.setTabOrder(self.chb_changetotal, self.dsb_total)
        QWidget.setTabOrder(self.dsb_total, self.pb_accept)
        QWidget.setTabOrder(self.pb_accept, self.pb_cancel)

        self.retranslateUi(PaymentAmountDialog)

        self.pb_accept.setDefault(True)


        QMetaObject.connectSlotsByName(PaymentAmountDialog)
    # setupUi

    def retranslateUi(self, PaymentAmountDialog):
        PaymentAmountDialog.setWindowTitle(QCoreApplication.translate("PaymentAmountDialog", u"\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.gb_info.setTitle(QCoreApplication.translate("PaymentAmountDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436", None))
        self.label_receiver.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.lbl_receiver.setText("")
        self.label_name.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.lbl_name.setText("")
        self.label_duedate.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.lbl_duedate.setText("")
        self.label_paidbefore.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e \u0440\u0430\u043d\u0435\u0435:", None))
        self.lbl_paidbefore.setText("")
        self.label_remain.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0441\u0442\u0430\u0442\u043e\u043a \u043f\u043e\u0441\u043b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f:", None))
        self.lbl_remain.setText("")
        self.gb_amounts.setTitle(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0443\u043c\u043c\u044b", None))
        self.lbl_paymentdate.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0414\u0430\u0442\u0430 \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.lbl_payment.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0443\u043c\u043c\u0430 \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.chb_changetotal.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043e\u0431\u0449\u0443\u044e \u0441\u0443\u043c\u043c\u0443 \u043f\u043b\u0430\u0442\u0435\u0436\u0430 \u043d\u0430 \u0442\u0443 \u0436\u0435 \u0440\u0430\u0437\u043d\u0438\u0446\u0443", None))
        self.label_total.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430:", None))
#if QT_CONFIG(tooltip)
        self.pb_deletepayment.setToolTip(QCoreApplication.translate("PaymentAmountDialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u044d\u0442\u0443 \u043e\u043f\u043b\u0430\u0442\u0443: \u043f\u043b\u0430\u0442\u0435\u0436 \u0432\u0435\u0440\u043d\u0435\u0442\u0441\u044f \u0432 \u043d\u0435\u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u043e\u0435 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u043d\u0430 \u0441\u0443\u043c\u043c\u0443 \u043e\u043f\u043b\u0430\u0442\u044b", None))
#endif // QT_CONFIG(tooltip)
        self.pb_deletepayment.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043e\u043f\u043b\u0430\u0442\u0443", None))
        self.pb_cancel.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_accept.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c", None))
    # retranslateUi

