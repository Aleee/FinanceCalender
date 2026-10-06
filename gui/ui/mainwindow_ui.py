# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDateEdit, QDoubleSpinBox, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidgetItem, QMainWindow, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QStackedWidget, QStatusBar, QToolBar, QToolButton,
    QTreeWidgetItem, QWidget)

from gui.commonwidgets.autoresizetextedit import AutoResizingTextEdit
from gui.commonwidgets.switchpushbutton import SwitchPushButton
from gui.eventwidget import EventWidget
from gui.filterwidget import (CategoryFilterListWidget, TermFilterListWidget)
from gui.paymenthistorywidget import PaymentHistoryTableView
import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1311, 750)
        MainWindow.setMinimumSize(QSize(1000, 600))
        icon = QIcon()
        icon.addFile(u":/icon-app/designer/icons/app.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        self.act_settings = QAction(MainWindow)
        self.act_settings.setObjectName(u"act_settings")
        icon1 = QIcon()
        icon1.addFile(u":/icon-toolbar/designer/icons/settings.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_settings.setIcon(icon1)
        self.act_settings.setMenuRole(QAction.MenuRole.NoRole)
        self.act_toggleheaders = QAction(MainWindow)
        self.act_toggleheaders.setObjectName(u"act_toggleheaders")
        self.act_toggleheaders.setCheckable(True)
        icon2 = QIcon()
        icon2.addFile(u":/icon-toolbar/designer/icons/itemtop.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_toggleheaders.setIcon(icon2)
        self.act_toggleheaders.setMenuRole(QAction.MenuRole.NoRole)
        self.act_togglefooters = QAction(MainWindow)
        self.act_togglefooters.setObjectName(u"act_togglefooters")
        self.act_togglefooters.setCheckable(True)
        icon3 = QIcon()
        icon3.addFile(u":/icon-toolbar/designer/icons/itembottom.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_togglefooters.setIcon(icon3)
        self.act_togglefooters.setMenuRole(QAction.MenuRole.NoRole)
        self.act_new = QAction(MainWindow)
        self.act_new.setObjectName(u"act_new")
        icon4 = QIcon()
        icon4.addFile(u":/icon-toolbar/designer/icons/new.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_new.setIcon(icon4)
        self.act_new.setMenuRole(QAction.MenuRole.NoRole)
        self.act_edit = QAction(MainWindow)
        self.act_edit.setObjectName(u"act_edit")
        icon5 = QIcon()
        icon5.addFile(u":/icon-toolbar/designer/icons/edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_edit.setIcon(icon5)
        self.act_edit.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.act_delete = QAction(MainWindow)
        self.act_delete.setObjectName(u"act_delete")
        icon6 = QIcon()
        icon6.addFile(u":/icon-toolbar/designer/icons/delete.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_delete.setIcon(icon6)
        self.act_delete.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.act_delete.setMenuRole(QAction.MenuRole.NoRole)
        self.act_copy = QAction(MainWindow)
        self.act_copy.setObjectName(u"act_copy")
        icon7 = QIcon()
        icon7.addFile(u":/icon-toolbar/designer/icons/copy.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_copy.setIcon(icon7)
        self.act_copy.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.act_copy.setMenuRole(QAction.MenuRole.NoRole)
        self.act_copydoc = QAction(MainWindow)
        self.act_copydoc.setObjectName(u"act_copydoc")
        self.act_copydoc.setEnabled(False)
        icon8 = QIcon()
        icon8.addFile(u":/icon-toolbar/designer/icons/copydoc.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_copydoc.setIcon(icon8)
        self.act_copydoc.setMenuRole(QAction.MenuRole.NoRole)
        self.act_export = QAction(MainWindow)
        self.act_export.setObjectName(u"act_export")
        icon9 = QIcon()
        icon9.addFile(u":/icon-toolbar/designer/icons/export.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_export.setIcon(icon9)
        self.act_export.setMenuRole(QAction.MenuRole.NoRole)
        self.act_finplan = QAction(MainWindow)
        self.act_finplan.setObjectName(u"act_finplan")
        self.act_finplan.setEnabled(True)
        icon10 = QIcon()
        icon10.addFile(u":/icon-toolbar/designer/icons/financing.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_finplan.setIcon(icon10)
        self.act_finplan.setMenuRole(QAction.MenuRole.NoRole)
        self.act_fulfillment = QAction(MainWindow)
        self.act_fulfillment.setObjectName(u"act_fulfillment")
        self.act_fulfillment.setEnabled(True)
        icon11 = QIcon()
        icon11.addFile(u":/icon-toolbar/designer/icons/fulfillment.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_fulfillment.setIcon(icon11)
        self.act_fulfillment.setMenuRole(QAction.MenuRole.NoRole)
        self.act_featured = QAction(MainWindow)
        self.act_featured.setObjectName(u"act_featured")
        self.act_featured.setCheckable(True)
        icon12 = QIcon()
        icon12.addFile(u":/icon-toolbar/designer/icons/featured.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_featured.setIcon(icon12)
        self.act_featured.setMenuRole(QAction.MenuRole.NoRole)
        self.act_fees = QAction(MainWindow)
        self.act_fees.setObjectName(u"act_fees")
        icon13 = QIcon()
        icon13.addFile(u":/icon-toolbar/designer/icons/fees.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_fees.setIcon(icon13)
        self.act_fees.setMenuRole(QAction.MenuRole.NoRole)
        self.act_chart = QAction(MainWindow)
        self.act_chart.setObjectName(u"act_chart")
        icon14 = QIcon()
        icon14.addFile(u":/icon-toolbar/designer/icons/chart.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_chart.setIcon(icon14)
        self.act_chart.setMenuRole(QAction.MenuRole.NoRole)
        self.act_matching = QAction(MainWindow)
        self.act_matching.setObjectName(u"act_matching")
        icon15 = QIcon()
        icon15.addFile(u":/icon-toolbar/designer/icons/matching.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_matching.setIcon(icon15)
        self.act_matching.setMenuRole(QAction.MenuRole.NoRole)
        self.act_contracts = QAction(MainWindow)
        self.act_contracts.setObjectName(u"act_contracts")
        self.act_contracts.setEnabled(True)
        icon16 = QIcon()
        icon16.addFile(u":/icon-toolbar/designer/icons/contract.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_contracts.setIcon(icon16)
        self.act_contracts.setMenuRole(QAction.MenuRole.NoRole)
        self.act_gotocontract = QAction(MainWindow)
        self.act_gotocontract.setObjectName(u"act_gotocontract")
        self.act_gotocontract.setEnabled(False)
        icon17 = QIcon()
        icon17.addFile(u":/icon-table/designer/icons/attachment.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.act_gotocontract.setIcon(icon17)
        self.act_gotocontract.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.spl_main = QSplitter(self.centralwidget)
        self.spl_main.setObjectName(u"spl_main")
        self.spl_main.setOrientation(Qt.Orientation.Horizontal)
        self.spl_main.setChildrenCollapsible(False)
        self.wdg_eventfilter = QWidget(self.spl_main)
        self.wdg_eventfilter.setObjectName(u"wdg_eventfilter")
        self.wdg_eventfilter.setMinimumSize(QSize(200, 0))
        self.wdg_eventfilter.setStyleSheet(u"background-color:white;")
        self.gridLayout_2 = QGridLayout(self.wdg_eventfilter)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(self.wdg_eventfilter)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setStyleSheet(u"QPushButton {\n"
"    border:none\n"
"}")
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setLineWidth(1)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 337, 671))
        self.gridLayout_3 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.spb_responsible = SwitchPushButton(self.scrollAreaWidgetContents)
        self.spb_responsible.setObjectName(u"spb_responsible")
        font = QFont()
        font.setBold(True)
        self.spb_responsible.setFont(font)
        self.spb_responsible.setStyleSheet(u"border-width: 0px; text-align: left;")

        self.gridLayout_3.addWidget(self.spb_responsible, 14, 0, 1, 2)

        self.verticalSpacer_7 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_7, 13, 0, 1, 1)

        self.chb_paytoday = QCheckBox(self.scrollAreaWidgetContents)
        self.chb_paytoday.setObjectName(u"chb_paytoday")
        self.chb_paytoday.setFont(font)

        self.gridLayout_3.addWidget(self.chb_paytoday, 17, 0, 1, 2)

        self.lw_term = TermFilterListWidget(self.scrollAreaWidgetContents)
        self.lw_term.setObjectName(u"lw_term")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lw_term.sizePolicy().hasHeightForWidth())
        self.lw_term.setSizePolicy(sizePolicy)
        self.lw_term.setFrameShape(QFrame.Shape.NoFrame)
        self.lw_term.setIconSize(QSize(17, 17))

        self.gridLayout_3.addWidget(self.lw_term, 5, 0, 1, 2)

        self.spb_receiver = SwitchPushButton(self.scrollAreaWidgetContents)
        self.spb_receiver.setObjectName(u"spb_receiver")
        self.spb_receiver.setFont(font)
        self.spb_receiver.setStyleSheet(u"border-width: 0px; text-align: left;")

        self.gridLayout_3.addWidget(self.spb_receiver, 11, 0, 1, 2)

        self.verticalSpacer_6 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_6, 10, 0, 1, 1)

        self.le_receiverfilter = QLineEdit(self.scrollAreaWidgetContents)
        self.le_receiverfilter.setObjectName(u"le_receiverfilter")
        self.le_receiverfilter.setStyleSheet(u"border: 1px solid #cbcbcb")
        self.le_receiverfilter.setClearButtonEnabled(True)

        self.gridLayout_3.addWidget(self.le_receiverfilter, 12, 0, 1, 2)

        self.spb_category = SwitchPushButton(self.scrollAreaWidgetContents)
        self.spb_category.setObjectName(u"spb_category")
        self.spb_category.setFont(font)
        self.spb_category.setStyleSheet(u"border-width: 0px; text-align: left;")

        self.gridLayout_3.addWidget(self.spb_category, 7, 0, 1, 2)

        self.cmb_responsiblefilter = QComboBox(self.scrollAreaWidgetContents)
        self.cmb_responsiblefilter.setObjectName(u"cmb_responsiblefilter")

        self.gridLayout_3.addWidget(self.cmb_responsiblefilter, 15, 0, 1, 2)

        self.verticalSpacer_8 = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_8, 16, 0, 1, 1)

        self.pb_resetfilters = QPushButton(self.scrollAreaWidgetContents)
        self.pb_resetfilters.setObjectName(u"pb_resetfilters")
        self.pb_resetfilters.setStyleSheet(u"QPushButton {border: 1px solid #cbcbcb; padding: 3px; background-color: #f4f4f4;}\n"
"QPushButton:hover {background-color: #e8eef4;}\n"
"QPushButton:disabled {color: #a0a0a0;}")

        self.gridLayout_3.addWidget(self.pb_resetfilters, 2, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 18, 0, 1, 2)

        self.lw_category = CategoryFilterListWidget(self.scrollAreaWidgetContents)
        self.lw_category.setObjectName(u"lw_category")
        sizePolicy.setHeightForWidth(self.lw_category.sizePolicy().hasHeightForWidth())
        self.lw_category.setSizePolicy(sizePolicy)
        self.lw_category.setFrameShape(QFrame.Shape.NoFrame)
        self.lw_category.setIconSize(QSize(17, 17))

        self.gridLayout_3.addWidget(self.lw_category, 9, 0, 1, 2)

        self.spb_term = SwitchPushButton(self.scrollAreaWidgetContents)
        self.spb_term.setObjectName(u"spb_term")
        self.spb_term.setFont(font)
        self.spb_term.setStyleSheet(u"border-width: 0px; text-align: left;")

        self.gridLayout_3.addWidget(self.spb_term, 4, 0, 1, 2)

        self.verticalSpacer_5 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_5, 6, 0, 1, 1)

        self.verticalSpacer_9 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_9, 3, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_2.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.spl_main.addWidget(self.wdg_eventfilter)
        self.spl_workarea = QSplitter(self.spl_main)
        self.spl_workarea.setObjectName(u"spl_workarea")
        self.spl_workarea.setOrientation(Qt.Orientation.Vertical)
        self.spl_workarea.setChildrenCollapsible(False)
        self.trw_event = EventWidget(self.spl_workarea)
        self.trw_event.setObjectName(u"trw_event")
        self.spl_workarea.addWidget(self.trw_event)
        self.stw_eventinfo = QStackedWidget(self.spl_workarea)
        self.stw_eventinfo.setObjectName(u"stw_eventinfo")
        self.stw_eventinfo.setFrameShape(QFrame.Shape.StyledPanel)
        self.descr = QWidget()
        self.descr.setObjectName(u"descr")
        self.gridLayout_4 = QGridLayout(self.descr)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(-1, -1, -1, 9)
        self.horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_2, 1, 10, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(15, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_4, 1, 1, 1, 1)

        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setVerticalSpacing(6)
        self.gridLayout_5.setContentsMargins(4, -1, -1, -1)
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_3, 6, 0, 1, 1)

        self.pb_deletepayment = QPushButton(self.descr)
        self.pb_deletepayment.setObjectName(u"pb_deletepayment")

        self.gridLayout_5.addWidget(self.pb_deletepayment, 8, 0, 1, 2)

        self.dsb_paymentsum = QDoubleSpinBox(self.descr)
        self.dsb_paymentsum.setObjectName(u"dsb_paymentsum")
        self.dsb_paymentsum.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dsb_paymentsum.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.dsb_paymentsum.setMaximum(9999999999.000000000000000)

        self.gridLayout_5.addWidget(self.dsb_paymentsum, 2, 0, 1, 1)

        self.pb_addpayment = QPushButton(self.descr)
        self.pb_addpayment.setObjectName(u"pb_addpayment")

        self.gridLayout_5.addWidget(self.pb_addpayment, 3, 0, 1, 2)

        self.line = QFrame(self.descr)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_5.addWidget(self.line, 5, 0, 1, 2)

        self.de_paymentdate = QDateEdit(self.descr)
        self.de_paymentdate.setObjectName(u"de_paymentdate")
        self.de_paymentdate.setMinimumSize(QSize(84, 0))
        self.de_paymentdate.setCalendarPopup(True)

        self.gridLayout_5.addWidget(self.de_paymentdate, 1, 0, 1, 1)

        self.label_2 = QLabel(self.descr)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.label_2, 0, 0, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_5, 1, 7, 2, 1)

        self.line_2 = QFrame(self.descr)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_4.addWidget(self.line_2, 1, 3, 2, 1)

        self.horizontalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_3, 1, 8, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer_2, 2, 0, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(15, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_5, 1, 4, 1, 1)

        self.tv_payment = PaymentHistoryTableView(self.descr)
        self.tv_payment.setObjectName(u"tv_payment")
        self.tv_payment.setMinimumSize(QSize(190, 0))
        self.tv_payment.setMaximumSize(QSize(190, 16777215))
        self.tv_payment.horizontalHeader().setStretchLastSection(True)

        self.gridLayout_4.addWidget(self.tv_payment, 1, 5, 2, 1)

        self.wdg_eventinfo = QWidget(self.descr)
        self.wdg_eventinfo.setObjectName(u"wdg_eventinfo")
        self.wdg_eventinfo.setMinimumSize(QSize(350, 0))
        self.wdg_eventinfo.setMaximumSize(QSize(350, 16777215))
        self.gridLayout_6 = QGridLayout(self.wdg_eventinfo)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setVerticalSpacing(4)
        self.gridLayout_6.setContentsMargins(-1, 0, 4, 0)
        self.gridLayout_8 = QGridLayout()
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setHorizontalSpacing(6)
        self.gridLayout_8.setVerticalSpacing(0)
        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_8.addItem(self.verticalSpacer_4, 0, 1, 1, 1)

        self.te_notes = QPlainTextEdit(self.wdg_eventinfo)
        self.te_notes.setObjectName(u"te_notes")
        self.te_notes.setMinimumSize(QSize(0, 55))

        self.gridLayout_8.addWidget(self.te_notes, 0, 0, 2, 1)

        self.tb_savenote = QToolButton(self.wdg_eventinfo)
        self.tb_savenote.setObjectName(u"tb_savenote")
        self.tb_savenote.setMinimumSize(QSize(0, 22))

        self.gridLayout_8.addWidget(self.tb_savenote, 1, 1, 1, 1)


        self.gridLayout_6.addLayout(self.gridLayout_8, 12, 0, 1, 5)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tla_remainsum = QLabel(self.wdg_eventinfo)
        self.tla_remainsum.setObjectName(u"tla_remainsum")
        self.tla_remainsum.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.tla_remainsum)

        self.la_remainsum = QLabel(self.wdg_eventinfo)
        self.la_remainsum.setObjectName(u"la_remainsum")

        self.horizontalLayout.addWidget(self.la_remainsum)

        self.horizontalSpacer_6 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_6)


        self.gridLayout_6.addLayout(self.horizontalLayout, 0, 0, 1, 5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.tla_contractbound = QLabel(self.wdg_eventinfo)
        self.tla_contractbound.setObjectName(u"tla_contractbound")
        self.tla_contractbound.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.tla_contractbound)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_7)


        self.gridLayout_6.addLayout(self.horizontalLayout_4, 5, 0, 1, 5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.tla_paymenttype = QLabel(self.wdg_eventinfo)
        self.tla_paymenttype.setObjectName(u"tla_paymenttype")
        self.tla_paymenttype.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.tla_paymenttype)

        self.la_paymenttype = QLabel(self.wdg_eventinfo)
        self.la_paymenttype.setObjectName(u"la_paymenttype")
        self.la_paymenttype.setMinimumSize(QSize(65, 0))

        self.horizontalLayout_3.addWidget(self.la_paymenttype)

        self.hs_paymenttype = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.hs_paymenttype)

        self.ln_paymenttype = QFrame(self.wdg_eventinfo)
        self.ln_paymenttype.setObjectName(u"ln_paymenttype")
        self.ln_paymenttype.setFrameShape(QFrame.Shape.VLine)
        self.ln_paymenttype.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_3.addWidget(self.ln_paymenttype)

        self.tla_createdate = QLabel(self.wdg_eventinfo)
        self.tla_createdate.setObjectName(u"tla_createdate")
        self.tla_createdate.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.tla_createdate)

        self.la_createdate = QLabel(self.wdg_eventinfo)
        self.la_createdate.setObjectName(u"la_createdate")

        self.horizontalLayout_3.addWidget(self.la_createdate)

        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.gridLayout_6.addLayout(self.horizontalLayout_3, 3, 0, 1, 5)

        self.la_contractbound = QLabel(self.wdg_eventinfo)
        self.la_contractbound.setObjectName(u"la_contractbound")
        self.la_contractbound.setWordWrap(True)
        self.la_contractbound.setOpenExternalLinks(False)

        self.gridLayout_6.addWidget(self.la_contractbound, 6, 0, 1, 5)

        self.label = QLabel(self.wdg_eventinfo)
        self.label.setObjectName(u"label")

        self.gridLayout_6.addWidget(self.label, 11, 0, 1, 4)

        self.tla_descr = QLabel(self.wdg_eventinfo)
        self.tla_descr.setObjectName(u"tla_descr")
        self.tla_descr.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_6.addWidget(self.tla_descr, 9, 0, 1, 4)

        self.te_descr = AutoResizingTextEdit(self.wdg_eventinfo)
        self.te_descr.setObjectName(u"te_descr")
        self.te_descr.setReadOnly(True)

        self.gridLayout_6.addWidget(self.te_descr, 10, 0, 1, 5)

        self.verticalSpacer_10 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_10, 4, 0, 1, 1)


        self.gridLayout_4.addWidget(self.wdg_eventinfo, 1, 0, 1, 1)

        self.stw_eventinfo.addWidget(self.descr)
        self.empty = QWidget()
        self.empty.setObjectName(u"empty")
        self.gridLayout_9 = QGridLayout(self.empty)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.la_emptyinfo = QLabel(self.empty)
        self.la_emptyinfo.setObjectName(u"la_emptyinfo")
        self.la_emptyinfo.setStyleSheet(u"color: #808080;")
        self.la_emptyinfo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_9.addWidget(self.la_emptyinfo, 0, 0, 1, 1)

        self.stw_eventinfo.addWidget(self.empty)
        self.spl_workarea.addWidget(self.stw_eventinfo)
        self.spl_main.addWidget(self.spl_workarea)

        self.gridLayout.addWidget(self.spl_main, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.tlbr = QToolBar(MainWindow)
        self.tlbr.setObjectName(u"tlbr")
        self.tlbr.setIconSize(QSize(30, 30))
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tlbr)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.tlbr.addAction(self.act_new)
        self.tlbr.addAction(self.act_copy)
        self.tlbr.addAction(self.act_copydoc)
        self.tlbr.addAction(self.act_edit)
        self.tlbr.addAction(self.act_delete)
        self.tlbr.addSeparator()
        self.tlbr.addAction(self.act_featured)
        self.tlbr.addAction(self.act_toggleheaders)
        self.tlbr.addAction(self.act_togglefooters)
        self.tlbr.addSeparator()
        self.tlbr.addAction(self.act_finplan)
        self.tlbr.addAction(self.act_fulfillment)
        self.tlbr.addAction(self.act_chart)
        self.tlbr.addSeparator()
        self.tlbr.addAction(self.act_fees)
        self.tlbr.addAction(self.act_matching)
        self.tlbr.addSeparator()
        self.tlbr.addAction(self.act_export)
        self.tlbr.addAction(self.act_contracts)
        self.tlbr.addAction(self.act_settings)

        self.retranslateUi(MainWindow)

        self.stw_eventinfo.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u041f\u043b\u0430\u0442\u0435\u0436\u043d\u044b\u0439 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c", None))
        self.act_settings.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.act_settings.setIconText(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
#if QT_CONFIG(tooltip)
        self.act_settings.setToolTip(QCoreApplication.translate("MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.act_toggleheaders.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.act_togglefooters.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u043f\u043e \u0440\u0430\u0437\u0434\u0435\u043b\u0430\u043c", None))
#if QT_CONFIG(tooltip)
        self.act_togglefooters.setToolTip(QCoreApplication.translate("MainWindow", u"\u0418\u0442\u043e\u0433\u043e \u043f\u043e \u0440\u0430\u0437\u0434\u0435\u043b\u0430\u043c", None))
#endif // QT_CONFIG(tooltip)
        self.act_new.setText(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436", None))
#if QT_CONFIG(tooltip)
        self.act_new.setToolTip(QCoreApplication.translate("MainWindow", u"\u041d\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436 (Ctrl+N)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.act_new.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.act_edit.setText(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436", None))
#if QT_CONFIG(tooltip)
        self.act_edit.setToolTip(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 (F2 \u0438\u043b\u0438 \u0434\u0432\u043e\u0439\u043d\u043e\u0439 \u043a\u043b\u0438\u043a)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.act_edit.setShortcut(QCoreApplication.translate("MainWindow", u"F2", None))
#endif // QT_CONFIG(shortcut)
        self.act_delete.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436", None))
#if QT_CONFIG(tooltip)
        self.act_delete.setToolTip(QCoreApplication.translate("MainWindow", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 (Del)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.act_delete.setShortcut(QCoreApplication.translate("MainWindow", u"Del", None))
#endif // QT_CONFIG(shortcut)
        self.act_copy.setText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436", None))
#if QT_CONFIG(tooltip)
        self.act_copy.setToolTip(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 (Ctrl+D)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.act_copy.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.act_copydoc.setText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u0441 \u043d\u043e\u0432\u044b\u043c \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u043c", None))
#if QT_CONFIG(tooltip)
        self.act_copydoc.setToolTip(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043b\u0430\u0442\u0435\u0436 \u0441 \u043d\u043e\u0432\u044b\u043c \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u043c", None))
#endif // QT_CONFIG(tooltip)
        self.act_export.setText(QCoreApplication.translate("MainWindow", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442", None))
#if QT_CONFIG(tooltip)
        self.act_export.setToolTip(QCoreApplication.translate("MainWindow", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 (Ctrl+E)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.act_export.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+E", None))
#endif // QT_CONFIG(shortcut)
        self.act_finplan.setText(QCoreApplication.translate("MainWindow", u"\u0424\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u043d", None))
#if QT_CONFIG(tooltip)
        self.act_finplan.setToolTip(QCoreApplication.translate("MainWindow", u"\u0424\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u043d (\u041f\u041a\u041c: \u0432\u044b\u0431\u043e\u0440 \u0433\u043e\u0434\u0430)", None))
#endif // QT_CONFIG(tooltip)
        self.act_fulfillment.setText(QCoreApplication.translate("MainWindow", u"\u0418\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0433\u043e \u043f\u043b\u0430\u043d\u0430", None))
        self.act_featured.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0430 \u043a\u043e\u043d\u0442\u0440\u043e\u043b\u0435", None))
#if QT_CONFIG(tooltip)
        self.act_featured.setToolTip(QCoreApplication.translate("MainWindow", u"\u041d\u0430 \u043a\u043e\u043d\u0442\u0440\u043e\u043b\u0435", None))
#endif // QT_CONFIG(tooltip)
        self.act_fees.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443", None))
#if QT_CONFIG(tooltip)
        self.act_fees.setToolTip(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443", None))
#endif // QT_CONFIG(tooltip)
        self.act_chart.setText(QCoreApplication.translate("MainWindow", u"\u0413\u0440\u0430\u0444\u0438\u043a\u0438", None))
#if QT_CONFIG(tooltip)
        self.act_chart.setToolTip(QCoreApplication.translate("MainWindow", u"\u0413\u0440\u0430\u0444\u0438\u043a\u0438", None))
#endif // QT_CONFIG(tooltip)
        self.act_matching.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0432\u0435\u0440\u0438\u0442\u044c \u0432\u044b\u043f\u0438\u0441\u043a\u0443", None))
        self.act_contracts.setText(QCoreApplication.translate("MainWindow", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u044b \u0438 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u044b", None))
        self.act_gotocontract.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043a \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0443", None))
        self.spb_responsible.setText(QCoreApplication.translate("MainWindow", u"\U0001f846 \U0001f847 \U0000041e\U00000422\U00000412\U00000415\U00000422\U00000421\U00000422\U00000412\U00000415\U0000041d\U0000041d\U0000042b\U00000419", None))
        self.chb_paytoday.setText(QCoreApplication.translate("MainWindow", u"\u041d\u0410\u0417\u041d\u0410\u0427\u0415\u041d\u042b \u041a \u041e\u041f\u041b\u0410\u0422\u0415", None))
        self.spb_receiver.setText(QCoreApplication.translate("MainWindow", u"\U0001f846 \U0001f847 \U0000041f\U0000041e\U0000041b\U00000423\U00000427\U00000410\U00000422\U00000415\U0000041b\U0000042c", None))
        self.spb_category.setText(QCoreApplication.translate("MainWindow", u"\U0001f846 \U0001f847 \U0000041a\U00000410\U00000422\U00000415\U00000413\U0000041e\U00000420\U00000418\U0000042f", None))
#if QT_CONFIG(tooltip)
        self.pb_resetfilters.setToolTip(QCoreApplication.translate("MainWindow", u"\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0432\u0441\u0435 \u0444\u0438\u043b\u044c\u0442\u0440\u044b (Ctrl+R)", None))
#endif // QT_CONFIG(tooltip)
        self.pb_resetfilters.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0444\u0438\u043b\u044c\u0442\u0440\u044b", None))
        self.spb_term.setText(QCoreApplication.translate("MainWindow", u"\U0001f846 \U0001f847 \U00000421\U00000420\U0000041e\U0000041a \U0000041f\U0000041e\U00000413\U00000410\U00000428\U00000415\U0000041d\U00000418\U0000042f", None))
        self.pb_deletepayment.setText(QCoreApplication.translate("MainWindow", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
        self.pb_addpayment.setText(QCoreApplication.translate("MainWindow", u"\u041e\u043f\u043b\u0430\u0442\u0438\u0442\u044c", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u0414\u0430\u0442\u0430 \u0438 \u0441\u0443\u043c\u043c\u0430", None))
#if QT_CONFIG(tooltip)
        self.tb_savenote.setToolTip(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u0437\u0430\u043c\u0435\u0442\u043a\u0443 (Ctrl+S)", None))
#endif // QT_CONFIG(tooltip)
        self.tb_savenote.setText(QCoreApplication.translate("MainWindow", u"\U0001f4be", None))
        self.tla_remainsum.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0441\u0442\u0430\u0442\u043e\u043a \u043f\u043b\u0430\u0442\u0435\u0436\u0430:  ", None))
        self.la_remainsum.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.tla_contractbound.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u0432\u044f\u0437\u0430\u043d \u043a \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0443:", None))
        self.tla_paymenttype.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0438\u0434:  ", None))
        self.la_paymenttype.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.tla_createdate.setText(QCoreApplication.translate("MainWindow", u"   \u0414\u0430\u0442\u0430 \u0432\u043e\u0437\u043d\u0438\u043a\u043d\u043e\u0432\u0435\u043d\u0438\u044f:  ", None))
        self.la_createdate.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.la_contractbound.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043c\u0435\u0442\u043a\u0438:", None))
        self.tla_descr.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430:", None))
        self.la_emptyinfo.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u043b\u0430\u0442\u0451\u0436 \u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u0435, \u0447\u0442\u043e\u0431\u044b \u0443\u0432\u0438\u0434\u0435\u0442\u044c \u043f\u043e\u0434\u0440\u043e\u0431\u043d\u043e\u0441\u0442\u0438", None))
        self.tlbr.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u041f\u0430\u043d\u0435\u043b\u044c \u0438\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u043e\u0432", None))
    # retranslateUi

