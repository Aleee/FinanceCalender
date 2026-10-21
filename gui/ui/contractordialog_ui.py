# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'contractordialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget)
import resources_rc

class Ui_ContractorDialog(object):
    def setupUi(self, ContractorDialog):
        if not ContractorDialog.objectName():
            ContractorDialog.setObjectName(u"ContractorDialog")
        ContractorDialog.resize(480, 380)
        ContractorDialog.setMinimumSize(QSize(420, 320))
        self.gridLayout = QGridLayout(ContractorDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lbl_steps = QLabel(ContractorDialog)
        self.lbl_steps.setObjectName(u"lbl_steps")
        self.lbl_steps.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_steps.setWordWrap(True)

        self.gridLayout.addWidget(self.lbl_steps, 0, 0, 1, 1)

        self.stw_main = QStackedWidget(ContractorDialog)
        self.stw_main.setObjectName(u"stw_main")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.gridLayout_2 = QGridLayout(self.page)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout_contractor_actions = QVBoxLayout()
        self.verticalLayout_contractor_actions.setObjectName(u"verticalLayout_contractor_actions")
        self.tb_rename_contractor = QToolButton(self.page)
        self.tb_rename_contractor.setObjectName(u"tb_rename_contractor")
        icon = QIcon()
        icon.addFile(u":/icon-contractors/designer/icons/item_edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tb_rename_contractor.setIcon(icon)
        self.tb_rename_contractor.setMinimumSize(QSize(32, 32))
        self.tb_rename_contractor.setIconSize(QSize(24, 24))
        self.tb_rename_contractor.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_rename_contractor.setAutoRaise(True)

        self.verticalLayout_contractor_actions.addWidget(self.tb_rename_contractor)

        self.tb_archive_contractor = QToolButton(self.page)
        self.tb_archive_contractor.setObjectName(u"tb_archive_contractor")
        icon1 = QIcon()
        icon1.addFile(u":/icon-contractors/designer/icons/item_archive.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tb_archive_contractor.setIcon(icon1)
        self.tb_archive_contractor.setMinimumSize(QSize(32, 32))
        self.tb_archive_contractor.setIconSize(QSize(24, 24))
        self.tb_archive_contractor.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_archive_contractor.setAutoRaise(True)

        self.verticalLayout_contractor_actions.addWidget(self.tb_archive_contractor)

        self.tb_history_contractor = QToolButton(self.page)
        self.tb_history_contractor.setObjectName(u"tb_history_contractor")
        icon2 = QIcon()
        icon2.addFile(u":/icon-contractors/designer/icons/item_payments.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tb_history_contractor.setIcon(icon2)
        self.tb_history_contractor.setMinimumSize(QSize(32, 32))
        self.tb_history_contractor.setIconSize(QSize(24, 24))
        self.tb_history_contractor.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_history_contractor.setAutoRaise(True)

        self.verticalLayout_contractor_actions.addWidget(self.tb_history_contractor)

        self.verticalSpacer_contractor_actions = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_contractor_actions.addItem(self.verticalSpacer_contractor_actions)


        self.gridLayout_2.addLayout(self.verticalLayout_contractor_actions, 1, 1, 1, 1)

        self.le_filter = QLineEdit(self.page)
        self.le_filter.setObjectName(u"le_filter")
        self.le_filter.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.le_filter, 0, 0, 1, 1)

        self.lw_contractor = QListWidget(self.page)
        self.lw_contractor.setObjectName(u"lw_contractor")

        self.gridLayout_2.addWidget(self.lw_contractor, 1, 0, 1, 1)

        self.stw_main.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.gridLayout_3 = QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(-1, 0, -1, 0)
        self.lw_contract = QListWidget(self.page_2)
        self.lw_contract.setObjectName(u"lw_contract")

        self.gridLayout_3.addWidget(self.lw_contract, 0, 0, 1, 1)

        self.verticalLayout_contract_actions = QVBoxLayout()
        self.verticalLayout_contract_actions.setObjectName(u"verticalLayout_contract_actions")
        self.tb_rename_contract = QToolButton(self.page_2)
        self.tb_rename_contract.setObjectName(u"tb_rename_contract")
        self.tb_rename_contract.setIcon(icon)
        self.tb_rename_contract.setMinimumSize(QSize(32, 32))
        self.tb_rename_contract.setIconSize(QSize(24, 24))
        self.tb_rename_contract.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_rename_contract.setAutoRaise(True)

        self.verticalLayout_contract_actions.addWidget(self.tb_rename_contract)

        self.tb_archive_contract = QToolButton(self.page_2)
        self.tb_archive_contract.setObjectName(u"tb_archive_contract")
        self.tb_archive_contract.setIcon(icon1)
        self.tb_archive_contract.setMinimumSize(QSize(32, 32))
        self.tb_archive_contract.setIconSize(QSize(24, 24))
        self.tb_archive_contract.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_archive_contract.setAutoRaise(True)

        self.verticalLayout_contract_actions.addWidget(self.tb_archive_contract)

        self.tb_history_contract = QToolButton(self.page_2)
        self.tb_history_contract.setObjectName(u"tb_history_contract")
        self.tb_history_contract.setIcon(icon2)
        self.tb_history_contract.setMinimumSize(QSize(32, 32))
        self.tb_history_contract.setIconSize(QSize(24, 24))
        self.tb_history_contract.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_history_contract.setAutoRaise(True)

        self.verticalLayout_contract_actions.addWidget(self.tb_history_contract)

        self.verticalSpacer_contract_actions = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_contract_actions.addItem(self.verticalSpacer_contract_actions)


        self.gridLayout_3.addLayout(self.verticalLayout_contract_actions, 0, 1, 1, 1)

        self.stw_main.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.gridLayout_4 = QGridLayout(self.page_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(-1, 0, -1, 0)
        self.lw_document = QListWidget(self.page_3)
        self.lw_document.setObjectName(u"lw_document")

        self.gridLayout_4.addWidget(self.lw_document, 0, 0, 1, 1)

        self.verticalLayout_document_actions = QVBoxLayout()
        self.verticalLayout_document_actions.setObjectName(u"verticalLayout_document_actions")
        self.tb_history_document = QToolButton(self.page_3)
        self.tb_history_document.setObjectName(u"tb_history_document")
        self.tb_history_document.setIcon(icon2)
        self.tb_history_document.setMinimumSize(QSize(32, 32))
        self.tb_history_document.setIconSize(QSize(24, 24))
        self.tb_history_document.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.tb_history_document.setAutoRaise(True)

        self.verticalLayout_document_actions.addWidget(self.tb_history_document)

        self.verticalSpacer_document_actions = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_document_actions.addItem(self.verticalSpacer_document_actions)


        self.gridLayout_4.addLayout(self.verticalLayout_document_actions, 0, 1, 1, 1)

        self.stw_main.addWidget(self.page_3)

        self.gridLayout.addWidget(self.stw_main, 1, 0, 1, 1)

        self.chb_show_archived = QCheckBox(ContractorDialog)
        self.chb_show_archived.setObjectName(u"chb_show_archived")

        self.gridLayout.addWidget(self.chb_show_archived, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pb_back = QPushButton(ContractorDialog)
        self.pb_back.setObjectName(u"pb_back")
        self.pb_back.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_back)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(ContractorDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")
        self.pb_cancel.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_next = QPushButton(ContractorDialog)
        self.pb_next.setObjectName(u"pb_next")

        self.horizontalLayout.addWidget(self.pb_next)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)

        QWidget.setTabOrder(self.le_filter, self.lw_contractor)
        QWidget.setTabOrder(self.lw_contractor, self.tb_rename_contractor)
        QWidget.setTabOrder(self.tb_rename_contractor, self.tb_archive_contractor)
        QWidget.setTabOrder(self.tb_archive_contractor, self.tb_history_contractor)
        QWidget.setTabOrder(self.tb_history_contractor, self.lw_contract)
        QWidget.setTabOrder(self.lw_contract, self.tb_rename_contract)
        QWidget.setTabOrder(self.tb_rename_contract, self.tb_archive_contract)
        QWidget.setTabOrder(self.tb_archive_contract, self.tb_history_contract)
        QWidget.setTabOrder(self.tb_history_contract, self.lw_document)
        QWidget.setTabOrder(self.lw_document, self.tb_history_document)
        QWidget.setTabOrder(self.tb_history_document, self.chb_show_archived)
        QWidget.setTabOrder(self.chb_show_archived, self.pb_next)
        QWidget.setTabOrder(self.pb_next, self.pb_cancel)
        QWidget.setTabOrder(self.pb_cancel, self.pb_back)

        self.retranslateUi(ContractorDialog)

        self.stw_main.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ContractorDialog)
    # setupUi

    def retranslateUi(self, ContractorDialog):
        ContractorDialog.setWindowTitle(QCoreApplication.translate("ContractorDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u044b \u0438 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u044b", None))
        self.lbl_steps.setText(QCoreApplication.translate("ContractorDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442 \u2192 \u0414\u043e\u0433\u043e\u0432\u043e\u0440 \u2192 \u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442", None))
#if QT_CONFIG(tooltip)
        self.tb_rename_contractor.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u0442\u044c \u043a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.tb_rename_contractor.setText(QCoreApplication.translate("ContractorDialog", u"\u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u0442\u044c", None))
#if QT_CONFIG(tooltip)
        self.tb_archive_contractor.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u0412 \u0430\u0440\u0445\u0438\u0432", None))
#endif // QT_CONFIG(tooltip)
        self.tb_archive_contractor.setText(QCoreApplication.translate("ContractorDialog", u"\u0412 \u0430\u0440\u0445\u0438\u0432", None))
#if QT_CONFIG(tooltip)
        self.tb_history_contractor.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u043a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u0430\u2026", None))
#endif // QT_CONFIG(tooltip)
        self.tb_history_contractor.setText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438\u2026", None))
        self.le_filter.setPlaceholderText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043e\u0438\u0441\u043a\u2026", None))
#if QT_CONFIG(tooltip)
        self.tb_rename_contract.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043d\u043e\u043c\u0435\u0440 \u0438 \u0434\u0430\u0442\u0443 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.tb_rename_contract.setText(QCoreApplication.translate("ContractorDialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", None))
#if QT_CONFIG(tooltip)
        self.tb_archive_contract.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u0412 \u0430\u0440\u0445\u0438\u0432", None))
#endif // QT_CONFIG(tooltip)
        self.tb_archive_contract.setText(QCoreApplication.translate("ContractorDialog", u"\u0412 \u0430\u0440\u0445\u0438\u0432", None))
#if QT_CONFIG(tooltip)
        self.tb_history_contract.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u043f\u043e \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0443\u2026", None))
#endif // QT_CONFIG(tooltip)
        self.tb_history_contract.setText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438\u2026", None))
#if QT_CONFIG(tooltip)
        self.tb_history_document.setToolTip(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438 \u043f\u043e \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0443\u2026", None))
#endif // QT_CONFIG(tooltip)
        self.tb_history_document.setText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u0438\u2026", None))
        self.chb_show_archived.setText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0430\u0440\u0445\u0438\u0432\u043d\u044b\u0435", None))
        self.pb_back.setText(QCoreApplication.translate("ContractorDialog", u"\u041d\u0430\u0437\u0430\u0434", None))
        self.pb_cancel.setText(QCoreApplication.translate("ContractorDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_next.setText(QCoreApplication.translate("ContractorDialog", u"\u0414\u0430\u043b\u0435\u0435", None))
    # retranslateUi

