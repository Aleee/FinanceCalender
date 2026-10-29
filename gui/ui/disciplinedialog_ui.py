# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'disciplinedialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DisciplineDialog(object):
    def setupUi(self, DisciplineDialog):
        if not DisciplineDialog.objectName():
            DisciplineDialog.setObjectName(u"DisciplineDialog")
        DisciplineDialog.resize(1500, 820)
        self.horizontalLayout = QHBoxLayout(DisciplineDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.label_period = QLabel(DisciplineDialog)
        self.label_period.setObjectName(u"label_period")
        font = QFont()
        font.setBold(True)
        self.label_period.setFont(font)
        self.label_period.setMaximumSize(QSize(260, 16777215))
        self.label_period.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.label_period)

        self.label_2 = QLabel(DisciplineDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.verticalLayout_6.addWidget(self.label_2)

        self.le_receiver = QLineEdit(DisciplineDialog)
        self.le_receiver.setObjectName(u"le_receiver")
        self.le_receiver.setMaximumSize(QSize(260, 16777215))
        self.le_receiver.setClearButtonEnabled(True)

        self.verticalLayout_6.addWidget(self.le_receiver)

        self.label = QLabel(DisciplineDialog)
        self.label.setObjectName(u"label")
        self.label.setFont(font)
        self.label.setMaximumSize(QSize(260, 16777215))
        self.label.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.label)

        self.lw_categories = QListWidget(DisciplineDialog)
        self.lw_categories.setObjectName(u"lw_categories")
        self.lw_categories.setMinimumSize(QSize(260, 0))
        self.lw_categories.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lw_categories.setMaximumSize(QSize(260, 16777215))
        self.lw_categories.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        self.verticalLayout_6.addWidget(self.lw_categories)

        self.pb_reset = QPushButton(DisciplineDialog)
        self.pb_reset.setObjectName(u"pb_reset")

        self.verticalLayout_6.addWidget(self.pb_reset)

        self.pb_export = QPushButton(DisciplineDialog)
        self.pb_export.setObjectName(u"pb_export")

        self.verticalLayout_6.addWidget(self.pb_export)


        self.horizontalLayout.addLayout(self.verticalLayout_6)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_kpi = QHBoxLayout()
        self.horizontalLayout_kpi.setObjectName(u"horizontalLayout_kpi")
        self.fr_kpi1 = QFrame(DisciplineDialog)
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

        self.fr_kpi2 = QFrame(DisciplineDialog)
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

        self.fr_kpi3 = QFrame(DisciplineDialog)
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

        self.fr_kpi4 = QFrame(DisciplineDialog)
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

        self.horizontalLayout_mode = QHBoxLayout()
        self.horizontalLayout_mode.setObjectName(u"horizontalLayout_mode")
        self.label_mode = QLabel(DisciplineDialog)
        self.label_mode.setObjectName(u"label_mode")

        self.horizontalLayout_mode.addWidget(self.label_mode)

        self.rb_count = QRadioButton(DisciplineDialog)
        self.rb_count.setObjectName(u"rb_count")
        self.rb_count.setChecked(True)

        self.horizontalLayout_mode.addWidget(self.rb_count)

        self.rb_amount = QRadioButton(DisciplineDialog)
        self.rb_amount.setObjectName(u"rb_amount")

        self.horizontalLayout_mode.addWidget(self.rb_amount)

        self.horizontalSpacer_mode = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_mode.addItem(self.horizontalSpacer_mode)

        self.lb_bucket = QLabel(DisciplineDialog)
        self.lb_bucket.setObjectName(u"lb_bucket")

        self.horizontalLayout_mode.addWidget(self.lb_bucket)


        self.verticalLayout.addLayout(self.horizontalLayout_mode)

        self.spl_report = QSplitter(DisciplineDialog)
        self.spl_report.setObjectName(u"spl_report")
        self.spl_report.setOrientation(Qt.Orientation.Vertical)
        self.spl_report.setChildrenCollapsible(False)
        self.wdg_chart = QWidget(self.spl_report)
        self.wdg_chart.setObjectName(u"wdg_chart")
        self.wdg_chart.setMinimumSize(QSize(0, 200))
        self.spl_report.addWidget(self.wdg_chart)
        self.tw_report = QTabWidget(self.spl_report)
        self.tw_report.setObjectName(u"tw_report")
        self.tab_receivers = QWidget()
        self.tab_receivers.setObjectName(u"tab_receivers")
        self.verticalLayout_2 = QVBoxLayout(self.tab_receivers)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tbl_receivers = QTableWidget(self.tab_receivers)
        self.tbl_receivers.setObjectName(u"tbl_receivers")
        self.tbl_receivers.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_receivers.setAlternatingRowColors(True)
        self.tbl_receivers.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_receivers.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tbl_receivers)

        self.tw_report.addTab(self.tab_receivers, "")
        self.tab_categories = QWidget()
        self.tab_categories.setObjectName(u"tab_categories")
        self.verticalLayout_3 = QVBoxLayout(self.tab_categories)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tbl_categories = QTableWidget(self.tab_categories)
        self.tbl_categories.setObjectName(u"tbl_categories")
        self.tbl_categories.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_categories.setAlternatingRowColors(True)
        self.tbl_categories.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_categories.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.tbl_categories)

        self.tw_report.addTab(self.tab_categories, "")
        self.tab_months = QWidget()
        self.tab_months.setObjectName(u"tab_months")
        self.verticalLayout_4 = QVBoxLayout(self.tab_months)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.wdg_trend = QWidget(self.tab_months)
        self.wdg_trend.setObjectName(u"wdg_trend")
        self.wdg_trend.setMinimumSize(QSize(0, 130))
        self.wdg_trend.setMaximumSize(QSize(16777215, 160))

        self.verticalLayout_4.addWidget(self.wdg_trend)

        self.tbl_months = QTableWidget(self.tab_months)
        self.tbl_months.setObjectName(u"tbl_months")
        self.tbl_months.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_months.setAlternatingRowColors(True)
        self.tbl_months.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_months.verticalHeader().setVisible(False)

        self.verticalLayout_4.addWidget(self.tbl_months)

        self.tw_report.addTab(self.tab_months, "")
        self.tab_closed = QWidget()
        self.tab_closed.setObjectName(u"tab_closed")
        self.verticalLayout_7 = QVBoxLayout(self.tab_closed)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.tbl_closed = QTableWidget(self.tab_closed)
        self.tbl_closed.setObjectName(u"tbl_closed")
        self.tbl_closed.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_closed.setAlternatingRowColors(True)
        self.tbl_closed.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_closed.verticalHeader().setVisible(False)

        self.verticalLayout_7.addWidget(self.tbl_closed)

        self.tw_report.addTab(self.tab_closed, "")
        self.tab_overdue = QWidget()
        self.tab_overdue.setObjectName(u"tab_overdue")
        self.verticalLayout_5 = QVBoxLayout(self.tab_overdue)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.lb_overdue = QLabel(self.tab_overdue)
        self.lb_overdue.setObjectName(u"lb_overdue")
        self.lb_overdue.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.lb_overdue)

        self.tbl_overdue = QTableWidget(self.tab_overdue)
        self.tbl_overdue.setObjectName(u"tbl_overdue")
        self.tbl_overdue.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_overdue.setAlternatingRowColors(True)
        self.tbl_overdue.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_overdue.verticalHeader().setVisible(False)

        self.verticalLayout_5.addWidget(self.tbl_overdue)

        self.tw_report.addTab(self.tab_overdue, "")
        self.spl_report.addWidget(self.tw_report)

        self.verticalLayout.addWidget(self.spl_report)


        self.horizontalLayout.addLayout(self.verticalLayout)

        QWidget.setTabOrder(self.le_receiver, self.lw_categories)
        QWidget.setTabOrder(self.lw_categories, self.pb_reset)
        QWidget.setTabOrder(self.pb_reset, self.pb_export)
        QWidget.setTabOrder(self.pb_export, self.rb_count)
        QWidget.setTabOrder(self.rb_count, self.rb_amount)
        QWidget.setTabOrder(self.rb_amount, self.tw_report)
        QWidget.setTabOrder(self.tw_report, self.tbl_receivers)
        QWidget.setTabOrder(self.tbl_receivers, self.tbl_categories)
        QWidget.setTabOrder(self.tbl_categories, self.tbl_months)
        QWidget.setTabOrder(self.tbl_months, self.tbl_closed)
        QWidget.setTabOrder(self.tbl_closed, self.tbl_overdue)

        self.retranslateUi(DisciplineDialog)

        self.tw_report.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DisciplineDialog)
    # setupUi

    def retranslateUi(self, DisciplineDialog):
        DisciplineDialog.setWindowTitle(QCoreApplication.translate("DisciplineDialog", u"\u041e\u0442\u0447\u0435\u0442 - \u041f\u043b\u0430\u0442\u0435\u0436\u043d\u0430\u044f \u0434\u0438\u0441\u0446\u0438\u043f\u043b\u0438\u043d\u0430", None))
        self.label_period.setText(QCoreApplication.translate("DisciplineDialog", u"\u041f\u0435\u0440\u0438\u043e\u0434:", None))
        self.label_2.setText(QCoreApplication.translate("DisciplineDialog", u"\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", None))
        self.le_receiver.setPlaceholderText(QCoreApplication.translate("DisciplineDialog", u"\u0427\u0430\u0441\u0442\u044c \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f", None))
        self.label.setText(QCoreApplication.translate("DisciplineDialog", u"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:", None))
        self.pb_reset.setText(QCoreApplication.translate("DisciplineDialog", u"\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0444\u0438\u043b\u044c\u0442\u0440\u044b", None))
        self.pb_export.setText(QCoreApplication.translate("DisciplineDialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 Excel...", None))
        self.lb_kpi1_value.setText(QCoreApplication.translate("DisciplineDialog", u"-", None))
        self.lb_kpi1_caption.setText("")
        self.lb_kpi2_value.setText(QCoreApplication.translate("DisciplineDialog", u"-", None))
        self.lb_kpi2_caption.setText("")
        self.lb_kpi3_value.setText(QCoreApplication.translate("DisciplineDialog", u"-", None))
        self.lb_kpi3_caption.setText("")
        self.lb_kpi4_value.setText(QCoreApplication.translate("DisciplineDialog", u"-", None))
        self.lb_kpi4_caption.setText("")
        self.label_mode.setText(QCoreApplication.translate("DisciplineDialog", u"\u0421\u0442\u043e\u043b\u0431\u0446\u044b \u043f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u044e\u0442:", None))
        self.rb_count.setText(QCoreApplication.translate("DisciplineDialog", u"\u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e", None))
        self.rb_amount.setText(QCoreApplication.translate("DisciplineDialog", u"\u0441\u0443\u043c\u043c\u0443", None))
        self.lb_bucket.setText(QCoreApplication.translate("DisciplineDialog", u"TextLabel", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_receivers), QCoreApplication.translate("DisciplineDialog", u"\u041f\u043e \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_categories), QCoreApplication.translate("DisciplineDialog", u"\u041f\u043e \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_months), QCoreApplication.translate("DisciplineDialog", u"\u041f\u043e \u043c\u0435\u0441\u044f\u0446\u0430\u043c", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_closed), QCoreApplication.translate("DisciplineDialog", u"\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.lb_overdue.setText(QCoreApplication.translate("DisciplineDialog", u"TextLabel", None))
        self.tw_report.setTabText(self.tw_report.indexOf(self.tab_overdue), QCoreApplication.translate("DisciplineDialog", u"\u041d\u0435\u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435", None))
    # retranslateUi

