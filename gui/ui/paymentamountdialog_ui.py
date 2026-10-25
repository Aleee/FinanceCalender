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
        self.la_receiver_title = QLabel(self.gb_info)
        self.la_receiver_title.setObjectName(u"la_receiver_title")

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.LabelRole, self.la_receiver_title)

        self.la_receiver = QLabel(self.gb_info)
        self.la_receiver.setObjectName(u"la_receiver")
        self.la_receiver.setWordWrap(True)

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.FieldRole, self.la_receiver)

        self.la_name_title = QLabel(self.gb_info)
        self.la_name_title.setObjectName(u"la_name_title")

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.LabelRole, self.la_name_title)

        self.la_name = QLabel(self.gb_info)
        self.la_name.setObjectName(u"la_name")
        self.la_name.setWordWrap(True)

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.FieldRole, self.la_name)

        self.la_duedate_title = QLabel(self.gb_info)
        self.la_duedate_title.setObjectName(u"la_duedate_title")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.LabelRole, self.la_duedate_title)

        self.la_duedate = QLabel(self.gb_info)
        self.la_duedate.setObjectName(u"la_duedate")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.FieldRole, self.la_duedate)

        self.la_paidbefore_title = QLabel(self.gb_info)
        self.la_paidbefore_title.setObjectName(u"la_paidbefore_title")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.LabelRole, self.la_paidbefore_title)

        self.la_paidbefore = QLabel(self.gb_info)
        self.la_paidbefore.setObjectName(u"la_paidbefore")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.FieldRole, self.la_paidbefore)

        self.la_remain_title = QLabel(self.gb_info)
        self.la_remain_title.setObjectName(u"la_remain_title")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.LabelRole, self.la_remain_title)

        self.la_remain = QLabel(self.gb_info)
        self.la_remain.setObjectName(u"la_remain")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.FieldRole, self.la_remain)


        self.gridLayout.addWidget(self.gb_info, 0, 0, 1, 1)

        self.gb_amounts = QGroupBox(PaymentAmountDialog)
        self.gb_amounts.setObjectName(u"gb_amounts")
        self.formLayout_amounts = QFormLayout(self.gb_amounts)
        self.formLayout_amounts.setObjectName(u"formLayout_amounts")
        self.la_paymentdate = QLabel(self.gb_amounts)
        self.la_paymentdate.setObjectName(u"la_paymentdate")

        self.formLayout_amounts.setWidget(0, QFormLayout.ItemRole.LabelRole, self.la_paymentdate)

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

        self.la_payment = QLabel(self.gb_amounts)
        self.la_payment.setObjectName(u"la_payment")

        self.formLayout_amounts.setWidget(1, QFormLayout.ItemRole.LabelRole, self.la_payment)

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

        self.la_total_title = QLabel(self.gb_amounts)
        self.la_total_title.setObjectName(u"la_total_title")

        self.formLayout_amounts.setWidget(3, QFormLayout.ItemRole.LabelRole, self.la_total_title)

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
        self.la_paymentdate.setBuddy(self.de_paymentdate)
        self.la_payment.setBuddy(self.dsb_payment)
        self.la_total_title.setBuddy(self.dsb_total)
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
        self.la_receiver_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.la_receiver.setText("")
        self.la_name_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.la_name.setText("")
        self.la_duedate_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.la_duedate.setText("")
        self.la_paidbefore_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e \u0440\u0430\u043d\u0435\u0435:", None))
        self.la_paidbefore.setText("")
        self.la_remain_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0441\u0442\u0430\u0442\u043e\u043a \u043f\u043e\u0441\u043b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f:", None))
        self.la_remain.setText("")
        self.gb_amounts.setTitle(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0443\u043c\u043c\u044b", None))
        self.la_paymentdate.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0414\u0430\u0442\u0430 \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.la_payment.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0421\u0443\u043c\u043c\u0430 \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.chb_changetotal.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043e\u0431\u0449\u0443\u044e \u0441\u0443\u043c\u043c\u0443 \u043f\u043b\u0430\u0442\u0435\u0436\u0430 \u043d\u0430 \u0442\u0443 \u0436\u0435 \u0440\u0430\u0437\u043d\u0438\u0446\u0443", None))
        self.la_total_title.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430:", None))
#if QT_CONFIG(tooltip)
        self.pb_deletepayment.setToolTip(QCoreApplication.translate("PaymentAmountDialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u044d\u0442\u0443 \u043e\u043f\u043b\u0430\u0442\u0443: \u043f\u043b\u0430\u0442\u0435\u0436 \u0432\u0435\u0440\u043d\u0435\u0442\u0441\u044f \u0432 \u043d\u0435\u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u043e\u0435 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u043d\u0430 \u0441\u0443\u043c\u043c\u0443 \u043e\u043f\u043b\u0430\u0442\u044b", None))
#endif // QT_CONFIG(tooltip)
        self.pb_deletepayment.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043e\u043f\u043b\u0430\u0442\u0443", None))
        self.pb_cancel.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_accept.setText(QCoreApplication.translate("PaymentAmountDialog", u"\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c", None))
    # retranslateUi

