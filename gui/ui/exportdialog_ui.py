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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_ExportDialog(object):
    def setupUi(self, ExportDialog):
        if not ExportDialog.objectName():
            ExportDialog.setObjectName(u"ExportDialog")
        ExportDialog.resize(213, 328)
        self.gridLayout_2 = QGridLayout(ExportDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer, 4, 1, 1, 1)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.gridLayout.setHorizontalSpacing(15)
        self.gridLayout.setContentsMargins(6, -1, 6, -1)
        self.label_4 = QLabel(ExportDialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)

        self.label_9 = QLabel(ExportDialog)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 9, 0, 1, 1)

        self.label_3 = QLabel(ExportDialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.rb_name_off = QRadioButton(ExportDialog)
        self.rb_name_off.setObjectName(u"rb_name_off")

        self.gridLayout.addWidget(self.rb_name_off, 2, 2, 1, 1)

        self.rb_remainsum_on = QRadioButton(ExportDialog)
        self.rb_remainsum_on.setObjectName(u"rb_remainsum_on")

        self.gridLayout.addWidget(self.rb_remainsum_on, 3, 1, 1, 1)

        self.rb_desc_on = QRadioButton(ExportDialog)
        self.rb_desc_on.setObjectName(u"rb_desc_on")

        self.gridLayout.addWidget(self.rb_desc_on, 7, 1, 1, 1)

        self.rb_desc_off = QRadioButton(ExportDialog)
        self.rb_desc_off.setObjectName(u"rb_desc_off")

        self.gridLayout.addWidget(self.rb_desc_off, 7, 2, 1, 1)

        self.rb_responsible_off = QRadioButton(ExportDialog)
        self.rb_responsible_off.setObjectName(u"rb_responsible_off")

        self.gridLayout.addWidget(self.rb_responsible_off, 8, 2, 1, 1)

        self.label_7 = QLabel(ExportDialog)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 7, 0, 1, 1)

        self.rb_todayshare_on = QRadioButton(ExportDialog)
        self.rb_todayshare_on.setObjectName(u"rb_todayshare_on")

        self.gridLayout.addWidget(self.rb_todayshare_on, 9, 1, 1, 1)

        self.rb_paymenttype_on = QRadioButton(ExportDialog)
        self.rb_paymenttype_on.setObjectName(u"rb_paymenttype_on")

        self.gridLayout.addWidget(self.rb_paymenttype_on, 6, 1, 1, 1)

        self.label_6 = QLabel(ExportDialog)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 6, 0, 1, 1)

        self.rb_totalsum_on = QRadioButton(ExportDialog)
        self.rb_totalsum_on.setObjectName(u"rb_totalsum_on")

        self.gridLayout.addWidget(self.rb_totalsum_on, 4, 1, 1, 1)

        self.rb_remainsum_off = QRadioButton(ExportDialog)
        self.rb_remainsum_off.setObjectName(u"rb_remainsum_off")

        self.gridLayout.addWidget(self.rb_remainsum_off, 3, 2, 1, 1)

        self.rb_receiver_on = QRadioButton(ExportDialog)
        self.rb_receiver_on.setObjectName(u"rb_receiver_on")
        self.rb_receiver_on.setEnabled(False)

        self.gridLayout.addWidget(self.rb_receiver_on, 1, 1, 1, 1)

        self.rb_todayshare_off = QRadioButton(ExportDialog)
        self.rb_todayshare_off.setObjectName(u"rb_todayshare_off")

        self.gridLayout.addWidget(self.rb_todayshare_off, 9, 2, 1, 1)

        self.label = QLabel(ExportDialog)
        self.label.setObjectName(u"label")
        self.label.setEnabled(True)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.label_8 = QLabel(ExportDialog)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout.addWidget(self.label_8, 8, 0, 1, 1)

        self.rb_duedate_off = QRadioButton(ExportDialog)
        self.rb_duedate_off.setObjectName(u"rb_duedate_off")

        self.gridLayout.addWidget(self.rb_duedate_off, 5, 2, 1, 1)

        self.rb_paymenttype_off = QRadioButton(ExportDialog)
        self.rb_paymenttype_off.setObjectName(u"rb_paymenttype_off")

        self.gridLayout.addWidget(self.rb_paymenttype_off, 6, 2, 1, 1)

        self.rb_duedate_on = QRadioButton(ExportDialog)
        self.rb_duedate_on.setObjectName(u"rb_duedate_on")

        self.gridLayout.addWidget(self.rb_duedate_on, 5, 1, 1, 1)

        self.rb_name_on = QRadioButton(ExportDialog)
        self.rb_name_on.setObjectName(u"rb_name_on")

        self.gridLayout.addWidget(self.rb_name_on, 2, 1, 1, 1)

        self.rb_receiver_off = QRadioButton(ExportDialog)
        self.rb_receiver_off.setObjectName(u"rb_receiver_off")
        self.rb_receiver_off.setEnabled(False)

        self.gridLayout.addWidget(self.rb_receiver_off, 1, 2, 1, 1)

        self.label_2 = QLabel(ExportDialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.rb_responsible_on = QRadioButton(ExportDialog)
        self.rb_responsible_on.setObjectName(u"rb_responsible_on")

        self.gridLayout.addWidget(self.rb_responsible_on, 8, 1, 1, 1)

        self.label_5 = QLabel(ExportDialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)

        self.rb_totalsum_off = QRadioButton(ExportDialog)
        self.rb_totalsum_off.setObjectName(u"rb_totalsum_off")

        self.gridLayout.addWidget(self.rb_totalsum_off, 4, 2, 1, 1)

        self.label_10 = QLabel(ExportDialog)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_10, 0, 1, 1, 1)

        self.label_11 = QLabel(ExportDialog)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_11, 0, 2, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 3, 1, 1, 2)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_4, 3, 3, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_export = QPushButton(ExportDialog)
        self.pb_export.setObjectName(u"pb_export")

        self.horizontalLayout.addWidget(self.pb_export)

        self.pb_cancel = QPushButton(ExportDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout.addWidget(self.pb_cancel)


        self.gridLayout_2.addLayout(self.horizontalLayout, 7, 0, 1, 4)

        self.line = QFrame(ExportDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line, 5, 0, 1, 4)

        self.line_2 = QFrame(ExportDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_2, 2, 0, 1, 4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_12 = QLabel(ExportDialog)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_2.addWidget(self.label_12)

        self.rb_xlsx = QRadioButton(ExportDialog)
        self.rb_xlsx.setObjectName(u"rb_xlsx")
        self.rb_xlsx.setChecked(True)

        self.horizontalLayout_2.addWidget(self.rb_xlsx)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.rb_pdf = QRadioButton(ExportDialog)
        self.rb_pdf.setObjectName(u"rb_pdf")

        self.horizontalLayout_2.addWidget(self.rb_pdf)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 1, 1, 3)


        self.retranslateUi(ExportDialog)

        QMetaObject.connectSlotsByName(ExportDialog)
    # setupUi

    def retranslateUi(self, ExportDialog):
        ExportDialog.setWindowTitle(QCoreApplication.translate("ExportDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 \u0444\u0430\u0439\u043b", None))
        self.label_4.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430", None))
        self.label_9.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u043f\u043b\u0430\u0442\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f", None))
        self.label_3.setText(QCoreApplication.translate("ExportDialog", u"\u0417\u0430\u0434\u043e\u043b\u0436\u0435\u043d\u043d\u043e\u0441\u0442\u044c", None))
        self.rb_name_off.setText("")
        self.rb_remainsum_on.setText("")
        self.rb_desc_on.setText("")
        self.rb_desc_off.setText("")
        self.rb_responsible_off.setText("")
        self.label_7.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.rb_todayshare_on.setText("")
        self.rb_paymenttype_on.setText("")
        self.label_6.setText(QCoreApplication.translate("ExportDialog", u"\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.rb_totalsum_on.setText("")
        self.rb_remainsum_off.setText("")
        self.rb_receiver_on.setText("")
        self.rb_todayshare_off.setText("")
        self.label.setText(QCoreApplication.translate("ExportDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c", None))
        self.label_8.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439", None))
        self.rb_duedate_off.setText("")
        self.rb_paymenttype_off.setText("")
        self.rb_duedate_on.setText("")
        self.rb_name_on.setText("")
        self.rb_receiver_off.setText("")
        self.label_2.setText(QCoreApplication.translate("ExportDialog", u"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.rb_responsible_on.setText("")
        self.label_5.setText(QCoreApplication.translate("ExportDialog", u"\u0414\u0430\u0442\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.rb_totalsum_off.setText("")
        self.label_10.setText(QCoreApplication.translate("ExportDialog", u"\u0434\u0430", None))
        self.label_11.setText(QCoreApplication.translate("ExportDialog", u"\u043d\u0435\u0442", None))
        self.pb_export.setText(QCoreApplication.translate("ExportDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442", None))
        self.pb_cancel.setText(QCoreApplication.translate("ExportDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.label_12.setText(QCoreApplication.translate("ExportDialog", u"\u0424\u043e\u0440\u043c\u0430\u0442:  ", None))
        self.rb_xlsx.setText(QCoreApplication.translate("ExportDialog", u"XLSX", None))
        self.rb_pdf.setText(QCoreApplication.translate("ExportDialog", u"PDF", None))
    # retranslateUi

