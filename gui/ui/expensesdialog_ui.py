# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'expensesdialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QDateEdit,
    QDialog, QFrame, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ExpensesDialog(object):
    def setupUi(self, ExpensesDialog):
        if not ExpensesDialog.objectName():
            ExpensesDialog.setObjectName(u"ExpensesDialog")
        ExpensesDialog.resize(1500, 820)
        self.horizontalLayout = QHBoxLayout(ExpensesDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_filters = QVBoxLayout()
        self.verticalLayout_filters.setObjectName(u"verticalLayout_filters")
        self.label_period = QLabel(ExpensesDialog)
        self.label_period.setObjectName(u"label_period")
        font = QFont()
        font.setBold(True)
        self.label_period.setFont(font)
        self.label_period.setMaximumSize(QSize(260, 16777215))
        self.label_period.setWordWrap(True)

        self.verticalLayout_filters.addWidget(self.label_period)

        self.gb_filters = QGroupBox(ExpensesDialog)
        self.gb_filters.setObjectName(u"gb_filters")
        self.verticalLayout_gb_filters = QVBoxLayout(self.gb_filters)
        self.verticalLayout_gb_filters.setObjectName(u"verticalLayout_gb_filters")
        self.label_receiver = QLabel(self.gb_filters)
        self.label_receiver.setObjectName(u"label_receiver")

        self.verticalLayout_gb_filters.addWidget(self.label_receiver)

        self.le_receiver = QLineEdit(self.gb_filters)
        self.le_receiver.setObjectName(u"le_receiver")
        self.le_receiver.setClearButtonEnabled(True)

        self.verticalLayout_gb_filters.addWidget(self.le_receiver)

        self.label_categories = QLabel(self.gb_filters)
        self.label_categories.setObjectName(u"label_categories")

        self.verticalLayout_gb_filters.addWidget(self.label_categories)

        self.lw_categories = QListWidget(self.gb_filters)
        self.lw_categories.setObjectName(u"lw_categories")
        self.lw_categories.setMinimumSize(QSize(250, 0))
        self.lw_categories.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lw_categories.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        self.verticalLayout_gb_filters.addWidget(self.lw_categories)

        self.cb_skip_finance = QCheckBox(self.gb_filters)
        self.cb_skip_finance.setObjectName(u"cb_skip_finance")

        self.verticalLayout_gb_filters.addWidget(self.cb_skip_finance)

        self.cb_skip_investment = QCheckBox(self.gb_filters)
        self.cb_skip_investment.setObjectName(u"cb_skip_investment")

        self.verticalLayout_gb_filters.addWidget(self.cb_skip_investment)

        self.pb_reset = QPushButton(self.gb_filters)
        self.pb_reset.setObjectName(u"pb_reset")

        self.verticalLayout_gb_filters.addWidget(self.pb_reset)


        self.verticalLayout_filters.addWidget(self.gb_filters)

        self.gb_view = QGroupBox(ExpensesDialog)
        self.gb_view.setObjectName(u"gb_view")
        self.verticalLayout_gb_view = QVBoxLayout(self.gb_view)
        self.verticalLayout_gb_view.setObjectName(u"verticalLayout_gb_view")
        self.cb_merge_small = QCheckBox(self.gb_view)
        self.cb_merge_small.setObjectName(u"cb_merge_small")

        self.verticalLayout_gb_view.addWidget(self.cb_merge_small)

        self.cb_compare = QCheckBox(self.gb_view)
        self.cb_compare.setObjectName(u"cb_compare")

        self.verticalLayout_gb_view.addWidget(self.cb_compare)

        self.horizontalLayout_previous = QHBoxLayout()
        self.horizontalLayout_previous.setObjectName(u"horizontalLayout_previous")
        self.de_prev_start = QDateEdit(self.gb_view)
        self.de_prev_start.setObjectName(u"de_prev_start")
        self.de_prev_start.setEnabled(False)
        self.de_prev_start.setCalendarPopup(True)

        self.horizontalLayout_previous.addWidget(self.de_prev_start)

        self.label_previous_dash = QLabel(self.gb_view)
        self.label_previous_dash.setObjectName(u"label_previous_dash")

        self.horizontalLayout_previous.addWidget(self.label_previous_dash)

        self.de_prev_end = QDateEdit(self.gb_view)
        self.de_prev_end.setObjectName(u"de_prev_end")
        self.de_prev_end.setEnabled(False)
        self.de_prev_end.setCalendarPopup(True)

        self.horizontalLayout_previous.addWidget(self.de_prev_end)

        self.horizontalSpacer_previous = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_previous.addItem(self.horizontalSpacer_previous)


        self.verticalLayout_gb_view.addLayout(self.horizontalLayout_previous)


        self.verticalLayout_filters.addWidget(self.gb_view)

        self.pb_export = QPushButton(ExpensesDialog)
        self.pb_export.setObjectName(u"pb_export")

        self.verticalLayout_filters.addWidget(self.pb_export)


        self.horizontalLayout.addLayout(self.verticalLayout_filters)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_kpi = QHBoxLayout()
        self.horizontalLayout_kpi.setObjectName(u"horizontalLayout_kpi")
        self.fr_kpi1 = QFrame(ExpensesDialog)
        self.fr_kpi1.setObjectName(u"fr_kpi1")
        self.fr_kpi1.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_kpi1 = QVBoxLayout(self.fr_kpi1)
        self.verticalLayout_kpi1.setSpacing(2)
        self.verticalLayout_kpi1.setObjectName(u"verticalLayout_kpi1")
        self.lb_kpi1_value = QLabel(self.fr_kpi1)
        self.lb_kpi1_value.setObjectName(u"lb_kpi1_value")
        font1 = QFont()
        font1.setPointSize(14)
        font1.setBold(True)
        self.lb_kpi1_value.setFont(font1)
        self.lb_kpi1_value.setWordWrap(True)

        self.verticalLayout_kpi1.addWidget(self.lb_kpi1_value)

        self.lb_kpi1_caption = QLabel(self.fr_kpi1)
        self.lb_kpi1_caption.setObjectName(u"lb_kpi1_caption")
        self.lb_kpi1_caption.setWordWrap(True)
        self.lb_kpi1_caption.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_kpi1.addWidget(self.lb_kpi1_caption)


        self.horizontalLayout_kpi.addWidget(self.fr_kpi1)

        self.fr_kpi2 = QFrame(ExpensesDialog)
        self.fr_kpi2.setObjectName(u"fr_kpi2")
        self.fr_kpi2.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_kpi2 = QVBoxLayout(self.fr_kpi2)
        self.verticalLayout_kpi2.setSpacing(2)
        self.verticalLayout_kpi2.setObjectName(u"verticalLayout_kpi2")
        self.lb_kpi2_value = QLabel(self.fr_kpi2)
        self.lb_kpi2_value.setObjectName(u"lb_kpi2_value")
        self.lb_kpi2_value.setFont(font1)
        self.lb_kpi2_value.setWordWrap(True)

        self.verticalLayout_kpi2.addWidget(self.lb_kpi2_value)

        self.lb_kpi2_caption = QLabel(self.fr_kpi2)
        self.lb_kpi2_caption.setObjectName(u"lb_kpi2_caption")
        self.lb_kpi2_caption.setWordWrap(True)
        self.lb_kpi2_caption.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_kpi2.addWidget(self.lb_kpi2_caption)


        self.horizontalLayout_kpi.addWidget(self.fr_kpi2)

        self.fr_kpi3 = QFrame(ExpensesDialog)
        self.fr_kpi3.setObjectName(u"fr_kpi3")
        self.fr_kpi3.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_kpi3 = QVBoxLayout(self.fr_kpi3)
        self.verticalLayout_kpi3.setSpacing(2)
        self.verticalLayout_kpi3.setObjectName(u"verticalLayout_kpi3")
        self.lb_kpi3_value = QLabel(self.fr_kpi3)
        self.lb_kpi3_value.setObjectName(u"lb_kpi3_value")
        self.lb_kpi3_value.setFont(font1)
        self.lb_kpi3_value.setWordWrap(True)

        self.verticalLayout_kpi3.addWidget(self.lb_kpi3_value)

        self.lb_kpi3_caption = QLabel(self.fr_kpi3)
        self.lb_kpi3_caption.setObjectName(u"lb_kpi3_caption")
        self.lb_kpi3_caption.setWordWrap(True)
        self.lb_kpi3_caption.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_kpi3.addWidget(self.lb_kpi3_caption)


        self.horizontalLayout_kpi.addWidget(self.fr_kpi3)

        self.fr_kpi4 = QFrame(ExpensesDialog)
        self.fr_kpi4.setObjectName(u"fr_kpi4")
        self.fr_kpi4.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_kpi4 = QVBoxLayout(self.fr_kpi4)
        self.verticalLayout_kpi4.setSpacing(2)
        self.verticalLayout_kpi4.setObjectName(u"verticalLayout_kpi4")
        self.lb_kpi4_value = QLabel(self.fr_kpi4)
        self.lb_kpi4_value.setObjectName(u"lb_kpi4_value")
        self.lb_kpi4_value.setFont(font1)
        self.lb_kpi4_value.setWordWrap(True)

        self.verticalLayout_kpi4.addWidget(self.lb_kpi4_value)

        self.lb_kpi4_caption = QLabel(self.fr_kpi4)
        self.lb_kpi4_caption.setObjectName(u"lb_kpi4_caption")
        self.lb_kpi4_caption.setWordWrap(True)
        self.lb_kpi4_caption.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_kpi4.addWidget(self.lb_kpi4_caption)


        self.horizontalLayout_kpi.addWidget(self.fr_kpi4)


        self.verticalLayout.addLayout(self.horizontalLayout_kpi)

        self.spl_report = QSplitter(ExpensesDialog)
        self.spl_report.setObjectName(u"spl_report")
        self.spl_report.setHandleWidth(12)
        self.spl_report.setOrientation(Qt.Orientation.Vertical)
        self.spl_report.setChildrenCollapsible(False)
        self.sa_chart = QScrollArea(self.spl_report)
        self.sa_chart.setObjectName(u"sa_chart")
        self.sa_chart.setMinimumSize(QSize(0, 200))
        self.sa_chart.setFrameShape(QFrame.Shape.NoFrame)
        self.sa_chart.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.sa_chart.setWidget(self.scrollAreaWidgetContents)
        self.spl_report.addWidget(self.sa_chart)
        self.tw_report = QTabWidget(self.spl_report)
        self.tw_report.setObjectName(u"tw_report")
        self.tab_categories = QWidget()
        self.tab_categories.setObjectName(u"tab_categories")
        self.verticalLayout_2 = QVBoxLayout(self.tab_categories)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tbl_categories = QTableWidget(self.tab_categories)
        self.tbl_categories.setObjectName(u"tbl_categories")
        self.tbl_categories.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_categories.setAlternatingRowColors(True)
        self.tbl_categories.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_categories.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tbl_categories)

        self.tw_report.addTab(self.tab_categories, "")
        self.tab_receivers = QWidget()
        self.tab_receivers.setObjectName(u"tab_receivers")
        self.verticalLayout_3 = QVBoxLayout(self.tab_receivers)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tbl_receivers = QTableWidget(self.tab_receivers)
        self.tbl_receivers.setObjectName(u"tbl_receivers")
        self.tbl_receivers.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_receivers.setAlternatingRowColors(True)
        self.tbl_receivers.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_receivers.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.tbl_receivers)

        self.tw_report.addTab(self.tab_receivers, "")
        self.tab_months = QWidget()
        self.tab_months.setObjectName(u"tab_months")
        self.verticalLayout_4 = QVBoxLayout(self.tab_months)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.spl_months = QSplitter(self.tab_months)
        self.spl_months.setObjectName(u"spl_months")
        self.spl_months.setOrientation(Qt.Orientation.Horizontal)
        self.spl_months.setChildrenCollapsible(False)
        self.wdg_months = QWidget(self.spl_months)
        self.wdg_months.setObjectName(u"wdg_months")
        self.wdg_months.setMinimumSize(QSize(300, 0))
        self.spl_months.addWidget(self.wdg_months)
        self.tbl_months = QTableWidget(self.spl_months)
        self.tbl_months.setObjectName(u"tbl_months")
        self.tbl_months.setMinimumSize(QSize(260, 0))
        self.tbl_months.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_months.setAlternatingRowColors(True)
        self.tbl_months.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.spl_months.addWidget(self.tbl_months)
        self.tbl_months.verticalHeader().setVisible(False)

        self.verticalLayout_4.addWidget(self.spl_months)

        self.tw_report.addTab(self.tab_months, "")
        self.tab_payments = QWidget()
        self.tab_payments.setObjectName(u"tab_payments")
        self.verticalLayout_5 = QVBoxLayout(self.tab_payments)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.tbl_payments = QTableWidget(self.tab_payments)
        self.tbl_payments.setObjectName(u"tbl_payments")
        self.tbl_payments.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_payments.setAlternatingRowColors(True)
        self.tbl_payments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_payments.verticalHeader().setVisible(False)

        self.verticalLayout_5.addWidget(self.tbl_payments)

        self.tw_report.addTab(self.tab_payments, "")
        self.spl_report.addWidget(self.tw_report)

        self.verticalLayout.addWidget(self.spl_report)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalLayout.setStretch(1, 1)
        QWidget.setTabOrder(self.le_receiver, self.lw_categories)
        QWidget.setTabOrder(self.lw_categories, self.cb_skip_finance)
        QWidget.setTabOrder(self.cb_skip_finance, self.cb_skip_investment)
        QWidget.setTabOrder(self.cb_skip_investment, self.pb_reset)
        QWidget.setTabOrder(self.pb_reset, self.cb_merge_small)
        QWidget.setTabOrder(self.cb_merge_small, self.cb_compare)
        QWidget.setTabOrder(self.cb_compare, self.de_prev_start)
        QWidget.setTabOrder(self.de_prev_start, self.de_prev_end)
        QWidget.setTabOrder(self.de_prev_end, self.pb_export)
        QWidget.setTabOrder(self.pb_export, self.tw_report)
        QWidget.setTabOrder(self.tw_report, self.tbl_categories)
        QWidget.setTabOrder(self.tbl_categories, self.tbl_receivers)
        QWidget.setTabOrder(self.tbl_receivers, self.tbl_months)
        QWidget.setTabOrder(self.tbl_months, self.tbl_payments)

        self.retranslateUi(ExpensesDialog)

        self.tw_report.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ExpensesDialog)
    # setupUi

    def retranslateUi(self, ExpensesDialog):
        ExpensesDialog.setWindowTitle(QCoreApplication.translate("ExpensesDialog", u"\u041e\u0442\u0447\u0435\u0442 - \u0421\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0430 \u0440\u0430\u0441\u0445\u043e\u0434\u043e\u0432", None))
        self.label_period.setText(QCoreApplication.translate("ExpensesDialog", u"\u041f\u0435\u0440\u0438\u043e\u0434:", None))
        self.gb_filters.setTitle(QCoreApplication.translate("ExpensesDialog", u"\u0427\u0442\u043e \u0443\u0447\u0438\u0442\u044b\u0432\u0430\u0442\u044c", None))
        self.label_receiver.setText(QCoreApplication.translate("ExpensesDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.le_receiver.setPlaceholderText(QCoreApplication.translate("ExpensesDialog", u"\u0427\u0430\u0441\u0442\u044c \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f", None))
        self.label_categories.setText(QCoreApplication.translate("ExpensesDialog", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:", None))
        self.cb_skip_finance.setText(QCoreApplication.translate("ExpensesDialog", u"\u0411\u0435\u0437 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0439 \u0434\u0435\u044f\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u0438", None))
        self.cb_skip_investment.setText(QCoreApplication.translate("ExpensesDialog", u"\u0411\u0435\u0437 \u0438\u043d\u0432\u0435\u0441\u0442\u0438\u0446\u0438\u043e\u043d\u043d\u043e\u0439 \u0434\u0435\u044f\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u0438", None))
        self.pb_reset.setText(QCoreApplication.translate("ExpensesDialog", u"\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0444\u0438\u043b\u044c\u0442\u0440\u044b", None))
        self.gb_view.setTitle(QCoreApplication.translate("ExpensesDialog", u"\u041a\u0430\u043a \u043f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c", None))
        self.cb_merge_small.setText(QCoreApplication.translate("ExpensesDialog", u"\u041c\u0435\u043b\u043a\u0438\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438 - \u0432 \u00ab\u041f\u0440\u043e\u0447\u0435\u0435\u00bb", None))
        self.cb_compare.setText(QCoreApplication.translate("ExpensesDialog", u"\u0421\u0440\u0430\u0432\u043d\u0438\u0442\u044c \u0441 \u043f\u0440\u043e\u0448\u043b\u044b\u043c \u043f\u0435\u0440\u0438\u043e\u0434\u043e\u043c", None))
        self.label_previous_dash.setText(QCoreApplication.translate("ExpensesDialog", u"-", None))
        self.pb_export.setText(QCoreApplication.translate("ExpensesDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 Excel...", None))
        self.lb_kpi1_value.setText(QCoreApplication.translate("ExpensesDialog", u"-", None))
        self.lb_kpi1_caption.setText("")
        self.lb_kpi2_value.setText(QCoreApplication.translate("ExpensesDialog", u"-", None))
        self.lb_kpi2_caption.setText("")
        self.lb_kpi3_value.setText(QCoreApplication.translate("ExpensesDialog", u"-", None))
        self.lb_kpi3_caption.setText("")
        self.lb_kpi4_value.setText(QCoreApplication.translate("ExpensesDialog", u"-", None))
        self.lb_kpi4_caption.setText("")
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_categories), QCoreApplication.translate("ExpensesDialog", u"\u041f\u043e \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_receivers), QCoreApplication.translate("ExpensesDialog", u"\u041f\u043e \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_months), QCoreApplication.translate("ExpensesDialog", u"\u041f\u043e \u043c\u0435\u0441\u044f\u0446\u0430\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_payments), QCoreApplication.translate("ExpensesDialog", u"\u041e\u043f\u043b\u0430\u0442\u044b", None))
    # retranslateUi

