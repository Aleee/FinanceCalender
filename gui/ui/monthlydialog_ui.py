# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monthlydialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QDialog,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

class Ui_MonthlyDialog(object):
    def setupUi(self, MonthlyDialog):
        if not MonthlyDialog.objectName():
            MonthlyDialog.setObjectName(u"MonthlyDialog")
        MonthlyDialog.resize(980, 520)
        self.verticalLayout = QVBoxLayout(MonthlyDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.la_monthcaption = QLabel(MonthlyDialog)
        self.la_monthcaption.setObjectName(u"la_monthcaption")

        self.horizontalLayout.addWidget(self.la_monthcaption)

        self.tb_prev = QToolButton(MonthlyDialog)
        self.tb_prev.setObjectName(u"tb_prev")
        self.tb_prev.setAutoRaise(True)
        self.tb_prev.setArrowType(Qt.ArrowType.LeftArrow)

        self.horizontalLayout.addWidget(self.tb_prev)

        self.la_month = QLabel(MonthlyDialog)
        self.la_month.setObjectName(u"la_month")
        self.la_month.setMinimumSize(QSize(150, 0))
        self.la_month.setStyleSheet(u"font-weight: bold;")
        self.la_month.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.la_month)

        self.tb_next = QToolButton(MonthlyDialog)
        self.tb_next.setObjectName(u"tb_next")
        self.tb_next.setAutoRaise(True)
        self.tb_next.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout.addWidget(self.tb_next)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.chb_onlymissing = QCheckBox(MonthlyDialog)
        self.chb_onlymissing.setObjectName(u"chb_onlymissing")

        self.horizontalLayout.addWidget(self.chb_onlymissing)

        self.chb_hidden = QCheckBox(MonthlyDialog)
        self.chb_hidden.setObjectName(u"chb_hidden")

        self.horizontalLayout.addWidget(self.chb_hidden)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.stk_monthly = QStackedWidget(MonthlyDialog)
        self.stk_monthly.setObjectName(u"stk_monthly")
        self.page_table = QWidget()
        self.page_table.setObjectName(u"page_table")
        self.verticalLayout_2 = QVBoxLayout(self.page_table)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tbl_monthly = QTableWidget(self.page_table)
        self.tbl_monthly.setObjectName(u"tbl_monthly")
        self.tbl_monthly.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_monthly.setAlternatingRowColors(True)
        self.tbl_monthly.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_monthly.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_monthly.setShowGrid(False)
        self.tbl_monthly.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tbl_monthly)

        self.stk_monthly.addWidget(self.page_table)
        self.page_empty = QWidget()
        self.page_empty.setObjectName(u"page_empty")
        self.verticalLayout_3 = QVBoxLayout(self.page_empty)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.la_empty = QLabel(self.page_empty)
        self.la_empty.setObjectName(u"la_empty")
        self.la_empty.setStyleSheet(u"color: gray;")
        self.la_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.la_empty.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.la_empty)

        self.stk_monthly.addWidget(self.page_empty)

        self.verticalLayout.addWidget(self.stk_monthly)

        self.la_summary = QLabel(MonthlyDialog)
        self.la_summary.setObjectName(u"la_summary")
        self.la_summary.setStyleSheet(u"font-weight: bold;")

        self.verticalLayout.addWidget(self.la_summary)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pb_create = QPushButton(MonthlyDialog)
        self.pb_create.setObjectName(u"pb_create")
        self.pb_create.setAutoDefault(False)

        self.horizontalLayout_2.addWidget(self.pb_create)

        self.pb_hide = QPushButton(MonthlyDialog)
        self.pb_hide.setObjectName(u"pb_hide")
        self.pb_hide.setAutoDefault(False)

        self.horizontalLayout_2.addWidget(self.pb_hide)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pb_close = QPushButton(MonthlyDialog)
        self.pb_close.setObjectName(u"pb_close")
        self.pb_close.setAutoDefault(False)

        self.horizontalLayout_2.addWidget(self.pb_close)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.tb_prev, self.tb_next)
        QWidget.setTabOrder(self.tb_next, self.chb_onlymissing)
        QWidget.setTabOrder(self.chb_onlymissing, self.chb_hidden)
        QWidget.setTabOrder(self.chb_hidden, self.tbl_monthly)
        QWidget.setTabOrder(self.tbl_monthly, self.pb_create)
        QWidget.setTabOrder(self.pb_create, self.pb_hide)
        QWidget.setTabOrder(self.pb_hide, self.pb_close)

        self.retranslateUi(MonthlyDialog)

        self.stk_monthly.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MonthlyDialog)
    # setupUi

    def retranslateUi(self, MonthlyDialog):
        MonthlyDialog.setWindowTitle(QCoreApplication.translate("MonthlyDialog", u"\u0415\u0436\u0435\u043c\u0435\u0441\u044f\u0447\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.la_monthcaption.setText(QCoreApplication.translate("MonthlyDialog", u"\u0421\u0440\u043e\u043a \u043e\u043f\u043b\u0430\u0442\u044b:", None))
#if QT_CONFIG(tooltip)
        self.tb_prev.setToolTip(QCoreApplication.translate("MonthlyDialog", u"\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u043c\u0435\u0441\u044f\u0446 (Ctrl+\u2190)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.tb_prev.setShortcut(QCoreApplication.translate("MonthlyDialog", u"Ctrl+Left", None))
#endif // QT_CONFIG(shortcut)
        self.la_month.setText(QCoreApplication.translate("MonthlyDialog", u"\u041c\u0435\u0441\u044f\u0446", None))
#if QT_CONFIG(tooltip)
        self.tb_next.setToolTip(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043c\u0435\u0441\u044f\u0446 (Ctrl+\u2192)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.tb_next.setShortcut(QCoreApplication.translate("MonthlyDialog", u"Ctrl+Right", None))
#endif // QT_CONFIG(shortcut)
        self.chb_onlymissing.setText(QCoreApplication.translate("MonthlyDialog", u"\u0422\u043e\u043b\u044c\u043a\u043e \u043d\u0435 \u0441\u043e\u0437\u0434\u0430\u043d\u043d\u044b\u0435", None))
#if QT_CONFIG(tooltip)
        self.chb_hidden.setToolTip(QCoreApplication.translate("MonthlyDialog", u"\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0442\u043e\u043b\u044c\u043a\u043e \u0441\u043a\u0440\u044b\u0442\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.chb_hidden.setText(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043a\u0440\u044b\u0442\u044b\u0435", None))
        self.la_empty.setText(QCoreApplication.translate("MonthlyDialog", u"\u041f\u0443\u0441\u0442\u043e", None))
        self.la_summary.setText(QCoreApplication.translate("MonthlyDialog", u"\u0421\u0432\u043e\u0434\u043a\u0430", None))
#if QT_CONFIG(tooltip)
        self.pb_create.setToolTip(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0451\u0436 \u0437\u0430 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0439 \u043c\u0435\u0441\u044f\u0446 \u0438\u043b\u0438 \u043e\u0442\u043a\u0440\u044b\u0442\u044c \u0443\u0436\u0435 \u0441\u043e\u0437\u0434\u0430\u043d\u043d\u044b\u0439", None))
#endif // QT_CONFIG(tooltip)
        self.pb_create.setText(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
#if QT_CONFIG(tooltip)
        self.pb_hide.setToolTip(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043a\u0440\u044b\u0442\u044c \u043d\u0435\u0441\u043e\u0437\u0434\u0430\u043d\u043d\u044b\u0439 \u043f\u043b\u0430\u0442\u0451\u0436 \u0437\u0430 \u044d\u0442\u043e\u0442 \u043c\u0435\u0441\u044f\u0446 (\u0437\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u0435\u0442\u0441\u044f \u043d\u0430 \u044d\u0442\u043e\u043c \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u0435 \u043d\u0430 \u0433\u043e\u0434)", None))
#endif // QT_CONFIG(tooltip)
        self.pb_hide.setText(QCoreApplication.translate("MonthlyDialog", u"\u0421\u043a\u0440\u044b\u0442\u044c", None))
        self.pb_close.setText(QCoreApplication.translate("MonthlyDialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
    # retranslateUi

