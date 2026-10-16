# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'matchingdialog.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget)

class Ui_matchingdialog(object):
    def setupUi(self, matchingdialog):
        if not matchingdialog.objectName():
            matchingdialog.setObjectName(u"matchingdialog")
        matchingdialog.resize(1200, 480)
        matchingdialog.setStyleSheet(u"QGroupBox { font-weight: bold; }")
        self.verticalLayout = QVBoxLayout(matchingdialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.hl_file = QHBoxLayout()
        self.hl_file.setObjectName(u"hl_file")
        self.lb_file = QLabel(matchingdialog)
        self.lb_file.setObjectName(u"lb_file")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_file.sizePolicy().hasHeightForWidth())
        self.lb_file.setSizePolicy(sizePolicy)

        self.hl_file.addWidget(self.lb_file)

        self.pb_opencsv = QPushButton(matchingdialog)
        self.pb_opencsv.setObjectName(u"pb_opencsv")

        self.hl_file.addWidget(self.pb_opencsv)

        self.pb_refresh = QPushButton(matchingdialog)
        self.pb_refresh.setObjectName(u"pb_refresh")
        self.pb_refresh.setEnabled(False)

        self.hl_file.addWidget(self.pb_refresh)


        self.verticalLayout.addLayout(self.hl_file)

        self.lb_summary = QLabel(matchingdialog)
        self.lb_summary.setObjectName(u"lb_summary")
        self.lb_summary.setStyleSheet(u"QLabel { background-color: palette(alternate-base); border: 1px solid palette(mid); border-radius: 4px; padding: 8px; }")
        self.lb_summary.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout.addWidget(self.lb_summary)

        self.spl_main = QSplitter(matchingdialog)
        self.spl_main.setObjectName(u"spl_main")
        self.spl_main.setOrientation(Qt.Orientation.Vertical)
        self.spl_main.setChildrenCollapsible(False)
        self.gb_proposals = QGroupBox(self.spl_main)
        self.gb_proposals.setObjectName(u"gb_proposals")
        self.vl_proposals = QVBoxLayout(self.gb_proposals)
        self.vl_proposals.setObjectName(u"vl_proposals")
        self.tw_proposals = QTableWidget(self.gb_proposals)
        self.tw_proposals.setObjectName(u"tw_proposals")
        self.tw_proposals.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_proposals.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tw_proposals.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_proposals.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_proposals.setWordWrap(True)
        self.tw_proposals.verticalHeader().setVisible(False)

        self.vl_proposals.addWidget(self.tw_proposals)

        self.spl_main.addWidget(self.gb_proposals)
        self.w_unmatched = QWidget(self.spl_main)
        self.w_unmatched.setObjectName(u"w_unmatched")
        self.vl_unmatched = QVBoxLayout(self.w_unmatched)
        self.vl_unmatched.setObjectName(u"vl_unmatched")
        self.vl_unmatched.setContentsMargins(0, 0, 0, 0)
        self.spl_lists = QSplitter(self.w_unmatched)
        self.spl_lists.setObjectName(u"spl_lists")
        self.spl_lists.setOrientation(Qt.Orientation.Horizontal)
        self.spl_lists.setChildrenCollapsible(False)
        self.gb_statement = QGroupBox(self.spl_lists)
        self.gb_statement.setObjectName(u"gb_statement")
        self.vl_statement = QVBoxLayout(self.gb_statement)
        self.vl_statement.setObjectName(u"vl_statement")
        self.le_searchstatement = QLineEdit(self.gb_statement)
        self.le_searchstatement.setObjectName(u"le_searchstatement")
        self.le_searchstatement.setClearButtonEnabled(True)

        self.vl_statement.addWidget(self.le_searchstatement)

        self.tw_statement = QTableWidget(self.gb_statement)
        self.tw_statement.setObjectName(u"tw_statement")
        self.tw_statement.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_statement.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tw_statement.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_statement.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_statement.setWordWrap(True)
        self.tw_statement.verticalHeader().setVisible(False)

        self.vl_statement.addWidget(self.tw_statement)

        self.hl_statementactions = QHBoxLayout()
        self.hl_statementactions.setObjectName(u"hl_statementactions")
        self.pb_create = QPushButton(self.gb_statement)
        self.pb_create.setObjectName(u"pb_create")
        self.pb_create.setEnabled(False)

        self.hl_statementactions.addWidget(self.pb_create)

        self.horizontalSpacer_statement = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_statementactions.addItem(self.horizontalSpacer_statement)


        self.vl_statement.addLayout(self.hl_statementactions)

        self.spl_lists.addWidget(self.gb_statement)
        self.gb_calendar = QGroupBox(self.spl_lists)
        self.gb_calendar.setObjectName(u"gb_calendar")
        self.vl_calendar = QVBoxLayout(self.gb_calendar)
        self.vl_calendar.setObjectName(u"vl_calendar")
        self.le_searchcalendar = QLineEdit(self.gb_calendar)
        self.le_searchcalendar.setObjectName(u"le_searchcalendar")
        self.le_searchcalendar.setClearButtonEnabled(True)

        self.vl_calendar.addWidget(self.le_searchcalendar)

        self.tw_calendar = QTableWidget(self.gb_calendar)
        self.tw_calendar.setObjectName(u"tw_calendar")
        self.tw_calendar.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_calendar.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tw_calendar.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_calendar.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_calendar.setWordWrap(True)
        self.tw_calendar.verticalHeader().setVisible(False)

        self.vl_calendar.addWidget(self.tw_calendar)

        self.hl_calendaractions = QHBoxLayout()
        self.hl_calendaractions.setObjectName(u"hl_calendaractions")
        self.pb_open = QPushButton(self.gb_calendar)
        self.pb_open.setObjectName(u"pb_open")
        self.pb_open.setEnabled(False)

        self.hl_calendaractions.addWidget(self.pb_open)

        self.horizontalSpacer_calendar = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_calendaractions.addItem(self.horizontalSpacer_calendar)


        self.vl_calendar.addLayout(self.hl_calendaractions)

        self.spl_lists.addWidget(self.gb_calendar)

        self.vl_unmatched.addWidget(self.spl_lists)

        self.hl_actions = QHBoxLayout()
        self.hl_actions.setObjectName(u"hl_actions")
        self.lb_selection = QLabel(self.w_unmatched)
        self.lb_selection.setObjectName(u"lb_selection")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lb_selection.sizePolicy().hasHeightForWidth())
        self.lb_selection.setSizePolicy(sizePolicy1)
        self.lb_selection.setWordWrap(False)

        self.hl_actions.addWidget(self.lb_selection)

        self.pb_link = QPushButton(self.w_unmatched)
        self.pb_link.setObjectName(u"pb_link")
        self.pb_link.setEnabled(False)
        font = QFont()
        font.setBold(True)
        self.pb_link.setFont(font)

        self.hl_actions.addWidget(self.pb_link)

        self.pb_hide = QPushButton(self.w_unmatched)
        self.pb_hide.setObjectName(u"pb_hide")
        self.pb_hide.setEnabled(False)

        self.hl_actions.addWidget(self.pb_hide)


        self.vl_unmatched.addLayout(self.hl_actions)

        self.spl_main.addWidget(self.w_unmatched)

        self.verticalLayout.addWidget(self.spl_main)

        self.tb_resolved = QToolButton(matchingdialog)
        self.tb_resolved.setObjectName(u"tb_resolved")
        self.tb_resolved.setCheckable(True)
        self.tb_resolved.setAutoRaise(True)
        self.tb_resolved.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tb_resolved.setArrowType(Qt.ArrowType.RightArrow)

        self.verticalLayout.addWidget(self.tb_resolved)

        self.tab_resolved = QTabWidget(matchingdialog)
        self.tab_resolved.setObjectName(u"tab_resolved")
        self.tab_resolved.setVisible(False)
        self.tab_resolved.setMinimumSize(QSize(0, 180))
        self.tab_resolved.setMaximumSize(QSize(16777215, 180))
        self.tab_linked = QWidget()
        self.tab_linked.setObjectName(u"tab_linked")
        self.hl_linked = QHBoxLayout(self.tab_linked)
        self.hl_linked.setObjectName(u"hl_linked")
        self.tw_linked = QTableWidget(self.tab_linked)
        self.tw_linked.setObjectName(u"tw_linked")
        self.tw_linked.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_linked.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tw_linked.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_linked.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_linked.setWordWrap(True)
        self.tw_linked.verticalHeader().setVisible(False)

        self.hl_linked.addWidget(self.tw_linked)

        self.vl_linkedbuttons = QVBoxLayout()
        self.vl_linkedbuttons.setObjectName(u"vl_linkedbuttons")
        self.pb_unlink = QPushButton(self.tab_linked)
        self.pb_unlink.setObjectName(u"pb_unlink")
        self.pb_unlink.setEnabled(False)

        self.vl_linkedbuttons.addWidget(self.pb_unlink)

        self.verticalSpacer_linked = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vl_linkedbuttons.addItem(self.verticalSpacer_linked)


        self.hl_linked.addLayout(self.vl_linkedbuttons)

        self.tab_resolved.addTab(self.tab_linked, "")
        self.tab_hidden = QWidget()
        self.tab_hidden.setObjectName(u"tab_hidden")
        self.hl_hidden = QHBoxLayout(self.tab_hidden)
        self.hl_hidden.setObjectName(u"hl_hidden")
        self.tw_hidden = QTableWidget(self.tab_hidden)
        self.tw_hidden.setObjectName(u"tw_hidden")
        self.tw_hidden.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tw_hidden.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tw_hidden.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_hidden.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tw_hidden.setWordWrap(True)
        self.tw_hidden.verticalHeader().setVisible(False)

        self.hl_hidden.addWidget(self.tw_hidden)

        self.vl_hiddenbuttons = QVBoxLayout()
        self.vl_hiddenbuttons.setObjectName(u"vl_hiddenbuttons")
        self.pb_restore = QPushButton(self.tab_hidden)
        self.pb_restore.setObjectName(u"pb_restore")
        self.pb_restore.setEnabled(False)

        self.vl_hiddenbuttons.addWidget(self.pb_restore)

        self.pb_restoreall = QPushButton(self.tab_hidden)
        self.pb_restoreall.setObjectName(u"pb_restoreall")
        self.pb_restoreall.setEnabled(False)

        self.vl_hiddenbuttons.addWidget(self.pb_restoreall)

        self.verticalSpacer_hidden = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vl_hiddenbuttons.addItem(self.verticalSpacer_hidden)


        self.hl_hidden.addLayout(self.vl_hiddenbuttons)

        self.tab_resolved.addTab(self.tab_hidden, "")

        self.verticalLayout.addWidget(self.tab_resolved)

        self.hl_bottom = QHBoxLayout()
        self.hl_bottom.setObjectName(u"hl_bottom")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_bottom.addItem(self.horizontalSpacer)

        self.pb_close = QPushButton(matchingdialog)
        self.pb_close.setObjectName(u"pb_close")

        self.hl_bottom.addWidget(self.pb_close)


        self.verticalLayout.addLayout(self.hl_bottom)


        self.retranslateUi(matchingdialog)

        self.tab_resolved.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(matchingdialog)
    # setupUi

    def retranslateUi(self, matchingdialog):
        matchingdialog.setWindowTitle(QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u0435\u0440\u043a\u0430 \u0432\u044b\u043f\u0438\u0441\u043a\u0438", None))
        self.lb_file.setText(QCoreApplication.translate("matchingdialog", u"\u0424\u0430\u0439\u043b \u0432\u044b\u043f\u0438\u0441\u043a\u0438 \u043d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d", None))
        self.pb_opencsv.setText(QCoreApplication.translate("matchingdialog", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443 (CSV-\u0444\u0430\u0439\u043b)\u2026", None))
#if QT_CONFIG(tooltip)
        self.pb_refresh.setToolTip(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u043d\u043e\u0432\u043e \u043f\u0440\u043e\u0447\u0438\u0442\u0430\u0442\u044c \u0444\u0430\u0439\u043b \u0432\u044b\u043f\u0438\u0441\u043a\u0438 \u0438 \u043f\u043b\u0430\u0442\u0435\u0436\u0438 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044f", None))
#endif // QT_CONFIG(tooltip)
        self.pb_refresh.setText(QCoreApplication.translate("matchingdialog", u"\u041f\u0435\u0440\u0435\u0447\u0438\u0442\u0430\u0442\u044c", None))
        self.lb_summary.setText("")
        self.gb_proposals.setTitle(QCoreApplication.translate("matchingdialog", u"\u041f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u043f\u043e \u0441\u043e\u043f\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0438\u044e", None))
        self.gb_statement.setTitle(QCoreApplication.translate("matchingdialog", u"\u0422\u043e\u043b\u044c\u043a\u043e \u0432 \u0432\u044b\u043f\u0438\u0441\u043a\u0435", None))
        self.le_searchstatement.setPlaceholderText(QCoreApplication.translate("matchingdialog", u"\u041f\u043e\u0438\u0441\u043a \u043f\u043e \u0434\u0430\u0442\u0435, \u0441\u0443\u043c\u043c\u0435, \u0442\u0435\u043a\u0441\u0442\u0443\u2026", None))
        self.pb_create.setText(QCoreApplication.translate("matchingdialog", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0432 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c", None))
        self.gb_calendar.setTitle(QCoreApplication.translate("matchingdialog", u"\u0422\u043e\u043b\u044c\u043a\u043e \u0432 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u0435", None))
        self.le_searchcalendar.setPlaceholderText(QCoreApplication.translate("matchingdialog", u"\u041f\u043e\u0438\u0441\u043a \u043f\u043e \u0434\u0430\u0442\u0435, \u0441\u0443\u043c\u043c\u0435, \u0442\u0435\u043a\u0441\u0442\u0443\u2026", None))
        self.pb_open.setText(QCoreApplication.translate("matchingdialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0443\u043c\u043c\u0443 \u043e\u043f\u043b\u0430\u0442\u044b", None))
        self.lb_selection.setText("")
        self.pb_link.setText(QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u044f\u0437\u0430\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0435", None))
        self.pb_hide.setText(QCoreApplication.translate("matchingdialog", u"\u0421\u043a\u0440\u044b\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0435", None))
#if QT_CONFIG(tooltip)
        self.tb_resolved.setToolTip(QCoreApplication.translate("matchingdialog", u"\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0438\u043b\u0438 \u0441\u043a\u0440\u044b\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u0438, \u0441\u0432\u044f\u0437\u0430\u043d\u043d\u044b\u0435 \u0438\u043b\u0438 \u0441\u043a\u0440\u044b\u0442\u044b\u0435 \u0432\u0440\u0443\u0447\u043d\u0443\u044e", None))
#endif // QT_CONFIG(tooltip)
        self.tb_resolved.setText(QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u044f\u0437\u0430\u043d\u043e \u0432\u0440\u0443\u0447\u043d\u0443\u044e: 0, \u0441\u043a\u0440\u044b\u0442\u043e: 0", None))
#if QT_CONFIG(tooltip)
        self.pb_unlink.setToolTip(QCoreApplication.translate("matchingdialog", u"\u0420\u0430\u0437\u043e\u0440\u0432\u0430\u0442\u044c \u0441\u0432\u044f\u0437\u044c: \u0437\u0430\u043f\u0438\u0441\u0438 \u0432\u0435\u0440\u043d\u0443\u0442\u0441\u044f \u0432 \u0441\u043f\u0438\u0441\u043a\u0438 \u0432\u044b\u0448\u0435", None))
#endif // QT_CONFIG(tooltip)
        self.pb_unlink.setText(QCoreApplication.translate("matchingdialog", u"\u0420\u0430\u0437\u043e\u0440\u0432\u0430\u0442\u044c \u0441\u0432\u044f\u0437\u044c", None))
        self.tab_resolved.setTabText(self.tab_resolved.indexOf(self.tab_linked), QCoreApplication.translate("matchingdialog", u"\u0421\u0432\u044f\u0437\u0430\u043d\u043e \u0432\u0440\u0443\u0447\u043d\u0443\u044e", None))
#if QT_CONFIG(tooltip)
        self.pb_restore.setToolTip(QCoreApplication.translate("matchingdialog", u"\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0435 \u0437\u0430\u043f\u0438\u0441\u0438 \u0432 \u0441\u043f\u0438\u0441\u043a\u0438 \u0432\u044b\u0448\u0435", None))
#endif // QT_CONFIG(tooltip)
        self.pb_restore.setText(QCoreApplication.translate("matchingdialog", u"\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u0435", None))
#if QT_CONFIG(tooltip)
        self.pb_restoreall.setToolTip(QCoreApplication.translate("matchingdialog", u"\u0421\u043d\u043e\u0432\u0430 \u043f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0432\u0441\u0435 \u0441\u043a\u0440\u044b\u0442\u044b\u0435 \u0432\u0440\u0443\u0447\u043d\u0443\u044e \u0437\u0430\u043f\u0438\u0441\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.pb_restoreall.setText(QCoreApplication.translate("matchingdialog", u"\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432\u0441\u0435", None))
        self.tab_resolved.setTabText(self.tab_resolved.indexOf(self.tab_hidden), QCoreApplication.translate("matchingdialog", u"\u0421\u043a\u0440\u044b\u0442\u044b\u0435", None))
        self.pb_close.setText(QCoreApplication.translate("matchingdialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
    # retranslateUi

