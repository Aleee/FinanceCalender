# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'copydocdialog.ui'
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
    QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_CopyDocDialog(object):
    def setupUi(self, CopyDocDialog):
        if not CopyDocDialog.objectName():
            CopyDocDialog.setObjectName(u"CopyDocDialog")
        CopyDocDialog.resize(580, 433)
        self.verticalLayout = QVBoxLayout(CopyDocDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(CopyDocDialog)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.la_document = QLabel(CopyDocDialog)
        self.la_document.setObjectName(u"la_document")
        self.la_document.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.la_document.setWordWrap(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.la_document)

        self.label_2 = QLabel(CopyDocDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.dsb_amount = QDoubleSpinBox(CopyDocDialog)
        self.dsb_amount.setObjectName(u"dsb_amount")
        self.dsb_amount.setMinimumSize(QSize(120, 0))
        self.dsb_amount.setMaximumSize(QSize(120, 16777215))
        self.dsb_amount.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_amount.setMaximum(99999999.000000000000000)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.dsb_amount)

        self.label_3 = QLabel(CopyDocDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.de_incurrencedate = QDateEdit(CopyDocDialog)
        self.de_incurrencedate.setObjectName(u"de_incurrencedate")
        self.de_incurrencedate.setMinimumSize(QSize(120, 0))
        self.de_incurrencedate.setMaximumSize(QSize(120, 16777215))
        self.de_incurrencedate.setCalendarPopup(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.de_incurrencedate)

        self.label_4 = QLabel(CopyDocDialog)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.wdg_period = QWidget(CopyDocDialog)
        self.wdg_period.setObjectName(u"wdg_period")
        self.horizontalLayout_2 = QHBoxLayout(self.wdg_period)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.cmb_month = QComboBox(self.wdg_period)
        self.cmb_month.setObjectName(u"cmb_month")

        self.horizontalLayout_2.addWidget(self.cmb_month)

        self.spb_year = QSpinBox(self.wdg_period)
        self.spb_year.setObjectName(u"spb_year")
        self.spb_year.setMinimum(2000)
        self.spb_year.setMaximum(2100)

        self.horizontalLayout_2.addWidget(self.spb_year)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.wdg_period)

        self.label_5 = QLabel(CopyDocDialog)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.de_duedate = QDateEdit(CopyDocDialog)
        self.de_duedate.setObjectName(u"de_duedate")
        self.de_duedate.setMinimumSize(QSize(120, 0))
        self.de_duedate.setMaximumSize(QSize(120, 16777215))
        self.de_duedate.setCalendarPopup(True)

        self.horizontalLayout_3.addWidget(self.de_duedate)

        self.la_weekday = QLabel(CopyDocDialog)
        self.la_weekday.setObjectName(u"la_weekday")
        self.la_weekday.setMinimumSize(QSize(24, 0))

        self.horizontalLayout_3.addWidget(self.la_weekday)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.formLayout.setLayout(4, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_3)

        self.la_duedatehint = QLabel(CopyDocDialog)
        self.la_duedatehint.setObjectName(u"la_duedatehint")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.la_duedatehint.sizePolicy().hasHeightForWidth())
        self.la_duedatehint.setSizePolicy(sizePolicy)
        self.la_duedatehint.setStyleSheet(u"QLabel { color: gray; }")
        self.la_duedatehint.setTextFormat(Qt.TextFormat.RichText)
        self.la_duedatehint.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.la_duedatehint.setWordWrap(False)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.la_duedatehint)

        self.label_8 = QLabel(CopyDocDialog)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.te_name = QPlainTextEdit(CopyDocDialog)
        self.te_name.setObjectName(u"te_name")
        self.te_name.setTabChangesFocus(True)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.te_name)

        self.label_6 = QLabel(CopyDocDialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.te_descr = QPlainTextEdit(CopyDocDialog)
        self.te_descr.setObjectName(u"te_descr")
        self.te_descr.setTabChangesFocus(True)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.te_descr)

        self.label_7 = QLabel(CopyDocDialog)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.te_paytermsdescr = QPlainTextEdit(CopyDocDialog)
        self.te_paytermsdescr.setObjectName(u"te_paytermsdescr")
        self.te_paytermsdescr.setMaximumSize(QSize(16777215, 60))
        self.te_paytermsdescr.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.te_paytermsdescr.setStyleSheet(u"QPlainTextEdit { background: palette(window); }")
        self.te_paytermsdescr.setReadOnly(True)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.te_paytermsdescr)


        self.verticalLayout.addLayout(self.formLayout)

        self.line = QFrame(CopyDocDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(CopyDocDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")
        self.pb_cancel.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_accept = QPushButton(CopyDocDialog)
        self.pb_accept.setObjectName(u"pb_accept")

        self.horizontalLayout.addWidget(self.pb_accept)


        self.verticalLayout.addLayout(self.horizontalLayout)

#if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.dsb_amount)
        self.label_3.setBuddy(self.de_incurrencedate)
        self.label_4.setBuddy(self.cmb_month)
        self.label_5.setBuddy(self.de_duedate)
        self.label_8.setBuddy(self.te_name)
        self.label_6.setBuddy(self.te_descr)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.dsb_amount, self.de_incurrencedate)
        QWidget.setTabOrder(self.de_incurrencedate, self.cmb_month)
        QWidget.setTabOrder(self.cmb_month, self.spb_year)
        QWidget.setTabOrder(self.spb_year, self.de_duedate)
        QWidget.setTabOrder(self.de_duedate, self.te_name)
        QWidget.setTabOrder(self.te_name, self.te_descr)
        QWidget.setTabOrder(self.te_descr, self.pb_cancel)

        self.retranslateUi(CopyDocDialog)

        self.pb_accept.setDefault(True)


        QMetaObject.connectSlotsByName(CopyDocDialog)
    # setupUi

    def retranslateUi(self, CopyDocDialog):
        CopyDocDialog.setWindowTitle(QCoreApplication.translate("CopyDocDialog", u"\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430 \u0441 \u043d\u043e\u0432\u044b\u043c \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u043c", None))
        self.label.setText(QCoreApplication.translate("CopyDocDialog", u"\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442:", None))
        self.la_document.setText(QCoreApplication.translate("CopyDocDialog", u"-", None))
        self.label_2.setText(QCoreApplication.translate("CopyDocDialog", u"&\u0421\u0443\u043c\u043c\u0430:", None))
#if QT_CONFIG(tooltip)
        self.label_3.setToolTip(QCoreApplication.translate("CopyDocDialog", u"\u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("CopyDocDialog", u"\u0414\u0430\u0442\u0430 &\u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f:", None))
#if QT_CONFIG(tooltip)
        self.de_incurrencedate.setToolTip(QCoreApplication.translate("CopyDocDialog", u"\u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("CopyDocDialog", u"\u041e\u0442\u0447\u0435\u0442\u043d\u044b\u0439 &\u043c\u0435\u0441\u044f\u0446:", None))
        self.label_5.setText(QCoreApplication.translate("CopyDocDialog", u"\u0414\u0430\u0442\u0430 \u043f\u043b\u0430&\u0442\u0435\u0436\u0430:", None))
        self.label_8.setText(QCoreApplication.translate("CopyDocDialog", u"&\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435:", None))
        self.label_6.setText(QCoreApplication.translate("CopyDocDialog", u"&\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430:", None))
        self.label_7.setText(QCoreApplication.translate("CopyDocDialog", u"\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b:", None))
        self.pb_cancel.setText(QCoreApplication.translate("CopyDocDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_accept.setText(QCoreApplication.translate("CopyDocDialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
    # retranslateUi

