# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'exportdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_ExportDialog(object):
    def setupUi(self, ExportDialog):
        if not ExportDialog.objectName():
            ExportDialog.setObjectName(u"ExportDialog")
        ExportDialog.resize(260, 440)
        self.verticalLayout = QVBoxLayout(ExportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(12)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_12 = QLabel(ExportDialog)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_2.addWidget(self.label_12)

        self.rb_xlsx = QRadioButton(ExportDialog)
        self.rb_xlsx.setObjectName(u"rb_xlsx")
        self.rb_xlsx.setChecked(True)

        self.horizontalLayout_2.addWidget(self.rb_xlsx)

        self.rb_pdf = QRadioButton(ExportDialog)
        self.rb_pdf.setObjectName(u"rb_pdf")

        self.horizontalLayout_2.addWidget(self.rb_pdf)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.gb_columns = QGroupBox(ExportDialog)
        self.gb_columns.setObjectName(u"gb_columns")
        self.verticalLayout_2 = QVBoxLayout(self.gb_columns)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.chb_receiver = QCheckBox(self.gb_columns)
        self.chb_receiver.setObjectName(u"chb_receiver")
        self.chb_receiver.setEnabled(False)
        self.chb_receiver.setChecked(True)

        self.verticalLayout_2.addWidget(self.chb_receiver)

        self.chb_name = QCheckBox(self.gb_columns)
        self.chb_name.setObjectName(u"chb_name")

        self.verticalLayout_2.addWidget(self.chb_name)

        self.chb_remainsum = QCheckBox(self.gb_columns)
        self.chb_remainsum.setObjectName(u"chb_remainsum")

        self.verticalLayout_2.addWidget(self.chb_remainsum)

        self.chb_totalsum = QCheckBox(self.gb_columns)
        self.chb_totalsum.setObjectName(u"chb_totalsum")

        self.verticalLayout_2.addWidget(self.chb_totalsum)

        self.chb_duedate = QCheckBox(self.gb_columns)
        self.chb_duedate.setObjectName(u"chb_duedate")

        self.verticalLayout_2.addWidget(self.chb_duedate)

        self.chb_paymenttype = QCheckBox(self.gb_columns)
        self.chb_paymenttype.setObjectName(u"chb_paymenttype")

        self.verticalLayout_2.addWidget(self.chb_paymenttype)

        self.chb_desc = QCheckBox(self.gb_columns)
        self.chb_desc.setObjectName(u"chb_desc")

        self.verticalLayout_2.addWidget(self.chb_desc)

        self.chb_responsible = QCheckBox(self.gb_columns)
        self.chb_responsible.setObjectName(u"chb_responsible")

        self.verticalLayout_2.addWidget(self.chb_responsible)

        self.chb_todayshare = QCheckBox(self.gb_columns)
        self.chb_todayshare.setObjectName(u"chb_todayshare")

        self.verticalLayout_2.addWidget(self.chb_todayshare)


        self.verticalLayout.addWidget(self.gb_columns)

        self.gb_hidden = QGroupBox(ExportDialog)
        self.gb_hidden.setObjectName(u"gb_hidden")
        self.verticalLayout_3 = QVBoxLayout(self.gb_hidden)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.rb_hidden_none = QRadioButton(self.gb_hidden)
        self.rb_hidden_none.setObjectName(u"rb_hidden_none")
        self.rb_hidden_none.setChecked(True)

        self.verticalLayout_3.addWidget(self.rb_hidden_none)

        self.rb_hidden_full = QRadioButton(self.gb_hidden)
        self.rb_hidden_full.setObjectName(u"rb_hidden_full")

        self.verticalLayout_3.addWidget(self.rb_hidden_full)

        self.rb_hidden_sumonly = QRadioButton(self.gb_hidden)
        self.rb_hidden_sumonly.setObjectName(u"rb_hidden_sumonly")

        self.verticalLayout_3.addWidget(self.rb_hidden_sumonly)


        self.verticalLayout.addWidget(self.gb_hidden)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 6, -1, -1)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_export = QPushButton(ExportDialog)
        self.pb_export.setObjectName(u"pb_export")

        self.horizontalLayout.addWidget(self.pb_export)

        self.pb_cancel = QPushButton(ExportDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout.addWidget(self.pb_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(ExportDialog)

        self.pb_export.setDefault(True)


        QMetaObject.connectSlotsByName(ExportDialog)
    # setupUi

    def retranslateUi(self, ExportDialog):
        ExportDialog.setWindowTitle(QCoreApplication.translate("ExportDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 \u0444\u0430\u0439\u043b", None))
        self.label_12.setText(QCoreApplication.translate("ExportDialog", u"\u0424\u043e\u0440\u043c\u0430\u0442:", None))
        self.rb_xlsx.setText(QCoreApplication.translate("ExportDialog", u"XLSX", None))
        self.rb_pdf.setText(QCoreApplication.translate("ExportDialog", u"PDF", None))
        self.gb_columns.setTitle(QCoreApplication.translate("ExportDialog", u"\u0421\u0442\u043e\u043b\u0431\u0446\u044b", None))
#if QT_CONFIG(tooltip)
        self.chb_receiver.setToolTip(QCoreApplication.translate("ExportDialog", u"\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0441\u0442\u043e\u043b\u0431\u0435\u0446", None))
#endif // QT_CONFIG(tooltip)
        self.chb_receiver.setText(QCoreApplication.translate("ExportDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c", None))
        self.chb_name.setText(QCoreApplication.translate("ExportDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.chb_remainsum.setText(QCoreApplication.translate("ExportDialog", u"\u0417\u0430\u0434\u043e\u043b\u0436\u0435\u043d\u043d\u043e\u0441\u0442\u044c", None))
        self.chb_totalsum.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430", None))
        self.chb_duedate.setText(QCoreApplication.translate("ExportDialog", u"\u0414\u0430\u0442\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_paymenttype.setText(QCoreApplication.translate("ExportDialog", u"\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_desc.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.chb_responsible.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439", None))
        self.chb_todayshare.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u043f\u043b\u0430\u0442\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f", None))
        self.gb_hidden.setTitle(QCoreApplication.translate("ExportDialog", u"\u0421\u043a\u0440\u044b\u0442\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.rb_hidden_none.setText(QCoreApplication.translate("ExportDialog", u"\u041d\u0435 \u0432\u043a\u043b\u044e\u0447\u0430\u0442\u044c", None))
        self.rb_hidden_full.setText(QCoreApplication.translate("ExportDialog", u"\u0412\u043a\u043b\u044e\u0447\u0430\u0442\u044c \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e", None))
#if QT_CONFIG(tooltip)
        self.rb_hidden_sumonly.setToolTip(QCoreApplication.translate("ExportDialog", u"\u0421\u0442\u0440\u043e\u043a\u0438 \u0441\u043a\u0440\u044b\u0442\u044b\u0445 \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439 \u043f\u043e\u043f\u0430\u0434\u0443\u0442 \u0432 \u0444\u0430\u0439\u043b \u0431\u0435\u0437 \u0442\u0435\u043a\u0441\u0442\u0430 \u2014 \u0442\u043e\u043b\u044c\u043a\u043e \u0441 \u0441\u0443\u043c\u043c\u0430\u043c\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.rb_hidden_sumonly.setText(QCoreApplication.translate("ExportDialog", u"\u0412\u043a\u043b\u044e\u0447\u0430\u0442\u044c \u0442\u043e\u043b\u044c\u043a\u043e \u0441\u0443\u043c\u043c\u044b", None))
        self.pb_export.setText(QCoreApplication.translate("ExportDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442\u2026", None))
        self.pb_cancel.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

