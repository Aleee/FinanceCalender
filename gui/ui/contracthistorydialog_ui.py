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
    QDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_ContractHistoryDialog(object):
    def setupUi(self, ContractHistoryDialog):
        if not ContractHistoryDialog.objectName():
            ContractHistoryDialog.setObjectName(u"ContractHistoryDialog")
        ContractHistoryDialog.resize(900, 520)
        ContractHistoryDialog.setMinimumSize(QSize(760, 400))
        self.verticalLayout = QVBoxLayout(ContractHistoryDialog)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.la_scope = QLabel(ContractHistoryDialog)
        self.la_scope.setObjectName(u"la_scope")
        font = QFont()
        font.setPointSize(12)
        self.la_scope.setFont(font)
        self.la_scope.setTextFormat(Qt.TextFormat.RichText)
        self.la_scope.setWordWrap(True)

        self.verticalLayout.addWidget(self.la_scope)

        self.la_subtitle = QLabel(ContractHistoryDialog)
        self.la_subtitle.setObjectName(u"la_subtitle")
        self.la_subtitle.setWordWrap(True)

        self.verticalLayout.addWidget(self.la_subtitle)

        self.line = QFrame(ContractHistoryDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.tw_history = QTabWidget(ContractHistoryDialog)
        self.tw_history.setObjectName(u"tw_history")
        self.tab_obligations = QWidget()
        self.tab_obligations.setObjectName(u"tab_obligations")
        self.verticalLayout_2 = QVBoxLayout(self.tab_obligations)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lay_obligations_filter = QHBoxLayout()
        self.lay_obligations_filter.setSpacing(8)
        self.lay_obligations_filter.setObjectName(u"lay_obligations_filter")
        self.lay_obligations_filter.setContentsMargins(-1, -1, -1, 8)
        self.chb_only_unpaid = QCheckBox(self.tab_obligations)
        self.chb_only_unpaid.setObjectName(u"chb_only_unpaid")

        self.lay_obligations_filter.addWidget(self.chb_only_unpaid)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_obligations_filter.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.lay_obligations_filter)

        self.tbl_obligations = QTableWidget(self.tab_obligations)
        self.tbl_obligations.setObjectName(u"tbl_obligations")
        self.tbl_obligations.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_obligations.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_obligations.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_obligations.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_obligations.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tbl_obligations)

        self.lay_obligations_total = QHBoxLayout()
        self.lay_obligations_total.setObjectName(u"lay_obligations_total")
        self.tbl_obligations_total = QTableWidget(self.tab_obligations)
        self.tbl_obligations_total.setObjectName(u"tbl_obligations_total")
        self.tbl_obligations_total.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tbl_obligations_total.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_obligations_total.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_obligations_total.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_obligations_total.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tbl_obligations_total.horizontalHeader().setVisible(False)
        self.tbl_obligations_total.verticalHeader().setVisible(False)

        self.lay_obligations_total.addWidget(self.tbl_obligations_total)


        self.verticalLayout_2.addLayout(self.lay_obligations_total)

        self.tw_history.addTab(self.tab_obligations, "")
        self.tab_payments = QWidget()
        self.tab_payments.setObjectName(u"tab_payments")
        self.verticalLayout_3 = QVBoxLayout(self.tab_payments)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.lay_payments_filter = QHBoxLayout()
        self.lay_payments_filter.setSpacing(8)
        self.lay_payments_filter.setObjectName(u"lay_payments_filter")
        self.lay_payments_filter.setContentsMargins(-1, -1, -1, 8)
        self.la_year = QLabel(self.tab_payments)
        self.la_year.setObjectName(u"la_year")

        self.lay_payments_filter.addWidget(self.la_year)

        self.cmb_year = QComboBox(self.tab_payments)
        self.cmb_year.setObjectName(u"cmb_year")

        self.lay_payments_filter.addWidget(self.cmb_year)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_payments_filter.addItem(self.horizontalSpacer_3)


        self.verticalLayout_3.addLayout(self.lay_payments_filter)

        self.tbl_payments = QTableWidget(self.tab_payments)
        self.tbl_payments.setObjectName(u"tbl_payments")
        self.tbl_payments.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_payments.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_payments.setAlternatingRowColors(True)
        self.tbl_payments.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_payments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_payments.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.tbl_payments)

        self.lay_payments_total = QHBoxLayout()
        self.lay_payments_total.setObjectName(u"lay_payments_total")
        self.tbl_payments_total = QTableWidget(self.tab_payments)
        self.tbl_payments_total.setObjectName(u"tbl_payments_total")
        self.tbl_payments_total.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tbl_payments_total.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_payments_total.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tbl_payments_total.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_payments_total.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tbl_payments_total.horizontalHeader().setVisible(False)
        self.tbl_payments_total.verticalHeader().setVisible(False)

        self.lay_payments_total.addWidget(self.tbl_payments_total)


        self.verticalLayout_3.addLayout(self.lay_payments_total)

        self.tw_history.addTab(self.tab_payments, "")

        self.verticalLayout.addWidget(self.tw_history)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pb_close = QPushButton(ContractHistoryDialog)
        self.pb_close.setObjectName(u"pb_close")

        self.horizontalLayout_2.addWidget(self.pb_close)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.tw_history, self.chb_only_unpaid)
        QWidget.setTabOrder(self.chb_only_unpaid, self.tbl_obligations)
        QWidget.setTabOrder(self.tbl_obligations, self.cmb_year)
        QWidget.setTabOrder(self.cmb_year, self.tbl_payments)
        QWidget.setTabOrder(self.tbl_payments, self.pb_close)

        self.retranslateUi(ContractHistoryDialog)

        self.tw_history.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ContractHistoryDialog)
    # setupUi

    def retranslateUi(self, ContractHistoryDialog):
        ContractHistoryDialog.setWindowTitle(QCoreApplication.translate("ContractHistoryDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u043f\u043e \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430\u043c", None))
        self.la_scope.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a", None))
        self.la_subtitle.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u041f\u043e\u0434\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a", None))
        self.chb_only_unpaid.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0422\u043e\u043b\u044c\u043a\u043e \u043d\u0435\u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435", None))
        self.tw_history.setTabText(self.tw_history.indexOf(self.tab_obligations), QCoreApplication.translate("ContractHistoryDialog", u"\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430", None))
        self.la_year.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0413\u043e\u0434 \u043e\u043f\u043b\u0430\u0442:", None))
        self.tw_history.setTabText(self.tw_history.indexOf(self.tab_payments), QCoreApplication.translate("ContractHistoryDialog", u"\u041e\u043f\u043b\u0430\u0442\u044b", None))
        self.pb_close.setText(QCoreApplication.translate("ContractHistoryDialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
    # retranslateUi

