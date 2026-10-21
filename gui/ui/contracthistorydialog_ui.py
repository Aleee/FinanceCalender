# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'contracthistorydialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ContractHistoryDialog(object):
    def setupUi(self, ContractHistoryDialog):
        if not ContractHistoryDialog.objectName():
            ContractHistoryDialog.setObjectName(u"ContractHistoryDialog")
        ContractHistoryDialog.resize(820, 480)
        ContractHistoryDialog.setMinimumSize(QSize(600, 360))
        self.verticalLayout = QVBoxLayout(ContractHistoryDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_scope = QLabel(ContractHistoryDialog)
        self.lbl_scope.setObjectName(u"lbl_scope")
        self.lbl_scope.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_scope)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_year = QLabel(ContractHistoryDialog)
        self.label_year.setObjectName(u"label_year")

        self.horizontalLayout.addWidget(self.label_year)

        self.cmb_year = QComboBox(ContractHistoryDialog)
        self.cmb_year.setObjectName(u"cmb_year")

        self.horizontalLayout.addWidget(self.cmb_year)

        self.chb_only_unpaid = QCheckBox(ContractHistoryDialog)
        self.chb_only_unpaid.setObjectName(u"chb_only_unpaid")

        self.horizontalLayout.addWidget(self.chb_only_unpaid)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tw_history = QTabWidget(ContractHistoryDialog)
        self.tw_history.setObjectName(u"tw_history")
        self.tab_obligations = QWidget()
        self.tab_obligations.setObjectName(u"tab_obligations")
        self.verticalLayout_2 = QVBoxLayout(self.tab_obligations)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tbl_obligations = QTableWidget(self.tab_obligations)
        self.tbl_obligations.setObjectName(u"tbl_obligations")
        self.tbl_obligations.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_obligations.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_obligations.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_obligations.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tbl_obligations)

        self.tw_history.addTab(self.tab_obligations, "")
        self.tab_payments = QWidget()
        self.tab_payments.setObjectName(u"tab_payments")
        self.verticalLayout_3 = QVBoxLayout(self.tab_payments)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tbl_payments = QTableWidget(self.tab_payments)
        self.tbl_payments.setObjectName(u"tbl_payments")
        self.tbl_payments.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_payments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_payments.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_payments.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.tbl_payments)

        self.tw_history.addTab(self.tab_payments, "")

        self.verticalLayout.addWidget(self.tw_history)

        self.lbl_summary = QLabel(ContractHistoryDialog)
        self.lbl_summary.setObjectName(u"lbl_summary")
        self.lbl_summary.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_summary)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lbl_hint = QLabel(ContractHistoryDialog)
        self.lbl_hint.setObjectName(u"lbl_hint")
        self.lbl_hint.setStyleSheet(u"color: gray")

        self.horizontalLayout_2.addWidget(self.lbl_hint)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pb_close = QPushButton(ContractHistoryDialog)
        self.pb_close.setObjectName(u"pb_close")

        self.horizontalLayout_2.addWidget(self.pb_close)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.cmb_year, self.chb_only_unpaid)
        QWidget.setTabOrder(self.chb_only_unpaid, self.tw_history)
        QWidget.setTabOrder(self.tw_history, self.tbl_obligations)
        QWidget.setTabOrder(self.tbl_obligations, self.tbl_payments)
        QWidget.setTabOrder(self.tbl_payments, self.pb_close)

        self.retranslateUi(ContractHistoryDialog)

        self.tw_history.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ContractHistoryDialog)
    # setupUi

    def retranslateUi(self, ContractHistoryDialog):
        ContractHistoryDialog.setWindowTitle(QCoreApplication.translate("ContractHistoryDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u043f\u043e \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430\u043c", None))
        self.lbl_scope.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442", None))
        self.label_year.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0413\u043e\u0434 \u043e\u043f\u043b\u0430\u0442:", None))
#if QT_CONFIG(tooltip)
        self.cmb_year.setToolTip(QCoreApplication.translate("ContractHistoryDialog", u"\u0413\u043e\u0434 \u0432\u043b\u0438\u044f\u0435\u0442 \u043d\u0430 \u0432\u043a\u043b\u0430\u0434\u043a\u0443 \u00ab\u041e\u043f\u043b\u0430\u0442\u044b\u00bb \u0438 \u043d\u0430 \u0441\u0443\u043c\u043c\u0443 \u00ab\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e \u0437\u0430 \u0433\u043e\u0434\u00bb", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.chb_only_unpaid.setToolTip(QCoreApplication.translate("ContractHistoryDialog", u"\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0441\u044f \u043a \u0432\u043a\u043b\u0430\u0434\u043a\u0435 \u00ab\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430\u00bb", None))
#endif // QT_CONFIG(tooltip)
        self.chb_only_unpaid.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0422\u043e\u043b\u044c\u043a\u043e \u043d\u0435\u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435", None))
        self.tw_history.setTabText(self.tw_history.indexOf(self.tab_obligations), QCoreApplication.translate("ContractHistoryDialog", u"\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
        self.tw_history.setTabText(self.tw_history.indexOf(self.tab_payments), QCoreApplication.translate("ContractHistoryDialog", u"\u041e\u043f\u043b\u0430\u0442\u044b", None))
        self.lbl_summary.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0418\u0442\u043e\u0433\u0438", None))
        self.lbl_hint.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0414\u0432\u043e\u0439\u043d\u043e\u0439 \u043a\u043b\u0438\u043a \u043f\u043e \u0441\u0442\u0440\u043e\u043a\u0435 \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u0435\u0442 \u043f\u043b\u0430\u0442\u0435\u0436", None))
        self.pb_close.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
    # retranslateUi

