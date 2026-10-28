# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'calendarwidget.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTableView, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget)

class Ui_CalendarWidget(object):
    def setupUi(self, CalendarWidget):
        if not CalendarWidget.objectName():
            CalendarWidget.setObjectName(u"CalendarWidget")
        CalendarWidget.resize(980, 720)
        self.verticalLayout = QVBoxLayout(CalendarWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.wdg_nav = QWidget(CalendarWidget)
        self.wdg_nav.setObjectName(u"wdg_nav")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdg_nav.sizePolicy().hasHeightForWidth())
        self.wdg_nav.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.wdg_nav)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.tb_prev = QToolButton(self.wdg_nav)
        self.tb_prev.setObjectName(u"tb_prev")
        self.tb_prev.setMinimumSize(QSize(28, 28))
        self.tb_prev.setAutoRaise(True)
        self.tb_prev.setArrowType(Qt.ArrowType.LeftArrow)

        self.horizontalLayout.addWidget(self.tb_prev)

        self.pb_month = QPushButton(self.wdg_nav)
        self.pb_month.setObjectName(u"pb_month")
        self.pb_month.setMinimumSize(QSize(170, 28))
        self.pb_month.setStyleSheet(u"QPushButton { font-size: 12pt; font-weight: bold; } QPushButton:hover { background: #e9ecef; }")
        self.pb_month.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pb_month.setFlat(True)

        self.horizontalLayout.addWidget(self.pb_month)

        self.tb_next = QToolButton(self.wdg_nav)
        self.tb_next.setObjectName(u"tb_next")
        self.tb_next.setMinimumSize(QSize(28, 28))
        self.tb_next.setAutoRaise(True)
        self.tb_next.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout.addWidget(self.tb_next)

        self.pb_today = QPushButton(self.wdg_nav)
        self.pb_today.setObjectName(u"pb_today")

        self.horizontalLayout.addWidget(self.pb_today)

        self.spacer_overdue = QSpacerItem(16, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.spacer_overdue)

        self.pb_overdue = QPushButton(self.wdg_nav)
        self.pb_overdue.setObjectName(u"pb_overdue")
        self.pb_overdue.setStyleSheet(u"QPushButton { color: #d00000; font-weight: bold; background: #fbeeec; border: 1px solid #d00000; border-radius: 3px; padding: 3px 10px; } QPushButton:hover { background: #f6d9d6; }")
        self.pb_overdue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.pb_overdue)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_undated = QPushButton(self.wdg_nav)
        self.pb_undated.setObjectName(u"pb_undated")
        self.pb_undated.setStyleSheet(u"QPushButton { color: #855a00; font-weight: bold; } QPushButton:hover { text-decoration: underline; }")
        self.pb_undated.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pb_undated.setFlat(True)

        self.horizontalLayout.addWidget(self.pb_undated)


        self.verticalLayout.addWidget(self.wdg_nav)

        self.spl_calendar = QSplitter(CalendarWidget)
        self.spl_calendar.setObjectName(u"spl_calendar")
        self.spl_calendar.setOrientation(Qt.Orientation.Horizontal)
        self.spl_calendar.setChildrenCollapsible(False)
        self.tv_calendar = QTableView(self.spl_calendar)
        self.tv_calendar.setObjectName(u"tv_calendar")
        self.tv_calendar.setMinimumSize(QSize(0, 300))
        self.tv_calendar.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tv_calendar.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tv_calendar.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tv_calendar.setShowGrid(True)
        self.spl_calendar.addWidget(self.tv_calendar)
        self.wdg_day = QWidget(self.spl_calendar)
        self.wdg_day.setObjectName(u"wdg_day")
        self.verticalLayout_day = QVBoxLayout(self.wdg_day)
        self.verticalLayout_day.setSpacing(4)
        self.verticalLayout_day.setObjectName(u"verticalLayout_day")
        self.verticalLayout_day.setContentsMargins(0, 0, 0, 0)
        self.la_day = QLabel(self.wdg_day)
        self.la_day.setObjectName(u"la_day")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.la_day.sizePolicy().hasHeightForWidth())
        self.la_day.setSizePolicy(sizePolicy1)
        self.la_day.setStyleSheet(u"font-weight: bold;")
        self.la_day.setWordWrap(True)

        self.verticalLayout_day.addWidget(self.la_day)

        self.tbl_events = QTableWidget(self.wdg_day)
        self.tbl_events.setObjectName(u"tbl_events")
        self.tbl_events.setMinimumSize(QSize(260, 0))
        self.tbl_events.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_events.setAlternatingRowColors(True)
        self.tbl_events.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_events.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_events.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tbl_events.verticalHeader().setVisible(False)

        self.verticalLayout_day.addWidget(self.tbl_events)

        self.spl_calendar.addWidget(self.wdg_day)

        self.verticalLayout.addWidget(self.spl_calendar)

        QWidget.setTabOrder(self.tv_calendar, self.tbl_events)
        QWidget.setTabOrder(self.tbl_events, self.pb_today)
        QWidget.setTabOrder(self.pb_today, self.pb_overdue)

        self.retranslateUi(CalendarWidget)

        QMetaObject.connectSlotsByName(CalendarWidget)
    # setupUi

    def retranslateUi(self, CalendarWidget):
#if QT_CONFIG(tooltip)
        self.tb_prev.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u043c\u0435\u0441\u044f\u0446 (Ctrl+\u2190)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.tb_prev.setShortcut(QCoreApplication.translate("CalendarWidget", u"Ctrl+Left", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.pb_month.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u043c\u0435\u0441\u044f\u0446 \u0438 \u0433\u043e\u0434", None))
#endif // QT_CONFIG(tooltip)
        self.pb_month.setText(QCoreApplication.translate("CalendarWidget", u"\u041c\u0435\u0441\u044f\u0446", None))
#if QT_CONFIG(tooltip)
        self.tb_next.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043c\u0435\u0441\u044f\u0446 (Ctrl+\u2192)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.tb_next.setShortcut(QCoreApplication.translate("CalendarWidget", u"Ctrl+Right", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.pb_today.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043a \u0441\u0435\u0433\u043e\u0434\u043d\u044f\u0448\u043d\u0435\u043c\u0443 \u0434\u043d\u044e", None))
#endif // QT_CONFIG(tooltip)
        self.pb_today.setText(QCoreApplication.translate("CalendarWidget", u"\u0421\u0435\u0433\u043e\u0434\u043d\u044f", None))
#if QT_CONFIG(tooltip)
        self.pb_overdue.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043a\u043e \u0434\u043d\u044e \u0441 \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u043c\u0438 \u043f\u043b\u0430\u0442\u0435\u0436\u0430\u043c\u0438 (\u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e\u0435 \u043d\u0430\u0436\u0430\u0442\u0438\u0435 \u2014 \u043a \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u043c\u0443 \u0442\u0430\u043a\u043e\u043c\u0443 \u0434\u043d\u044e)", None))
#endif // QT_CONFIG(tooltip)
        self.pb_overdue.setText(QCoreApplication.translate("CalendarWidget", u"\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e", None))
#if QT_CONFIG(tooltip)
        self.pb_undated.setToolTip(QCoreApplication.translate("CalendarWidget", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u0431\u0435\u0437 \u0441\u0440\u043e\u043a\u0430 \u043e\u043f\u043b\u0430\u0442\u044b \u0432 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u0435 \u043d\u0435 \u043f\u043e\u043a\u0430\u0437\u0430\u043d\u044b. \u041d\u0430\u0436\u043c\u0438\u0442\u0435, \u0447\u0442\u043e\u0431\u044b \u0432\u044b\u0431\u0440\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u0438\u0437 \u0441\u043f\u0438\u0441\u043a\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.pb_undated.setText("")
        self.la_day.setText("")
        pass
    # retranslateUi

