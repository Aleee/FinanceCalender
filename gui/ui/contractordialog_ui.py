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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QWidget)

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

        self.gridLayout.addWidget(self.lbl_steps, 0, 0, 1, 1)

        self.stw_main = QStackedWidget(ContractorDialog)
        self.stw_main.setObjectName(u"stw_main")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.gridLayout_2 = QGridLayout(self.page)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.label = QLabel(self.page)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_2, 3, 0, 1, 1)

        self.le_filter = QLineEdit(self.page)
        self.le_filter.setObjectName(u"le_filter")
        self.le_filter.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.le_filter, 1, 0, 1, 1)

        self.lw_contractor = QListWidget(self.page)
        self.lw_contractor.setObjectName(u"lw_contractor")

        self.gridLayout_2.addWidget(self.lw_contractor, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(self.page)
        self.pb_cancel.setObjectName(u"pb_cancel")
        self.pb_cancel.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_continue_to_contracts = QPushButton(self.page)
        self.pb_continue_to_contracts.setObjectName(u"pb_continue_to_contracts")

        self.horizontalLayout.addWidget(self.pb_continue_to_contracts)


        self.gridLayout_2.addLayout(self.horizontalLayout, 4, 0, 1, 1)

        self.stw_main.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.gridLayout_3 = QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pb_back_to_contractors = QPushButton(self.page_2)
        self.pb_back_to_contractors.setObjectName(u"pb_back_to_contractors")
        self.pb_back_to_contractors.setAutoDefault(False)

        self.horizontalLayout_2.addWidget(self.pb_back_to_contractors)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pb_cancel_2 = QPushButton(self.page_2)
        self.pb_cancel_2.setObjectName(u"pb_cancel_2")
        self.pb_cancel_2.setAutoDefault(False)

        self.horizontalLayout_2.addWidget(self.pb_cancel_2)

        self.pb_continue_to_documents = QPushButton(self.page_2)
        self.pb_continue_to_documents.setObjectName(u"pb_continue_to_documents")

        self.horizontalLayout_2.addWidget(self.pb_continue_to_documents)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.label_2 = QLabel(self.page_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)

        self.lw_contract = QListWidget(self.page_2)
        self.lw_contract.setObjectName(u"lw_contract")

        self.gridLayout_3.addWidget(self.lw_contract, 1, 0, 1, 1)

        self.stw_main.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.gridLayout_4 = QGridLayout(self.page_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pb_back_to_contracts = QPushButton(self.page_3)
        self.pb_back_to_contracts.setObjectName(u"pb_back_to_contracts")
        self.pb_back_to_contracts.setAutoDefault(False)

        self.horizontalLayout_3.addWidget(self.pb_back_to_contracts)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.pb_cancel_3 = QPushButton(self.page_3)
        self.pb_cancel_3.setObjectName(u"pb_cancel_3")
        self.pb_cancel_3.setAutoDefault(False)

        self.horizontalLayout_3.addWidget(self.pb_cancel_3)

        self.pb_accept = QPushButton(self.page_3)
        self.pb_accept.setObjectName(u"pb_accept")

        self.horizontalLayout_3.addWidget(self.pb_accept)


        self.gridLayout_4.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)

        self.lw_document = QListWidget(self.page_3)
        self.lw_document.setObjectName(u"lw_document")

        self.gridLayout_4.addWidget(self.lw_document, 1, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_4.addItem(self.verticalSpacer_3, 2, 0, 1, 1)

        self.label_3 = QLabel(self.page_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.gridLayout_4.addWidget(self.label_3, 0, 0, 1, 1)

        self.stw_main.addWidget(self.page_3)

        self.gridLayout.addWidget(self.stw_main, 1, 0, 1, 1)

        QWidget.setTabOrder(self.le_filter, self.lw_contractor)
        QWidget.setTabOrder(self.lw_contractor, self.pb_continue_to_contracts)
        QWidget.setTabOrder(self.pb_continue_to_contracts, self.pb_cancel)
        QWidget.setTabOrder(self.pb_cancel, self.lw_contract)
        QWidget.setTabOrder(self.lw_contract, self.pb_continue_to_documents)
        QWidget.setTabOrder(self.pb_continue_to_documents, self.pb_cancel_2)
        QWidget.setTabOrder(self.pb_cancel_2, self.pb_back_to_contractors)
        QWidget.setTabOrder(self.pb_back_to_contractors, self.lw_document)
        QWidget.setTabOrder(self.lw_document, self.pb_accept)
        QWidget.setTabOrder(self.pb_accept, self.pb_cancel_3)
        QWidget.setTabOrder(self.pb_cancel_3, self.pb_back_to_contracts)

        self.retranslateUi(ContractorDialog)

        self.stw_main.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ContractorDialog)
    # setupUi

    def retranslateUi(self, ContractorDialog):
        ContractorDialog.setWindowTitle(QCoreApplication.translate("ContractorDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u044b \u0438 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u044b", None))
        self.lbl_steps.setText(QCoreApplication.translate("ContractorDialog", u"\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442 \u2192 \u0414\u043e\u0433\u043e\u0432\u043e\u0440 \u2192 \u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442", None))
        self.label.setText(QCoreApplication.translate("ContractorDialog", u"\u0412\u044b\u0431\u043e\u0440 \u043a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u0430:", None))
        self.le_filter.setPlaceholderText(QCoreApplication.translate("ContractorDialog", u"\u041f\u043e\u0438\u0441\u043a\u2026", None))
        self.pb_cancel.setText(QCoreApplication.translate("ContractorDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_continue_to_contracts.setText(QCoreApplication.translate("ContractorDialog", u"\u0414\u0430\u043b\u0435\u0435", None))
        self.pb_back_to_contractors.setText(QCoreApplication.translate("ContractorDialog", u"\u041d\u0430\u0437\u0430\u0434", None))
        self.pb_cancel_2.setText(QCoreApplication.translate("ContractorDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_continue_to_documents.setText(QCoreApplication.translate("ContractorDialog", u"\u0414\u0430\u043b\u0435\u0435", None))
        self.label_2.setText(QCoreApplication.translate("ContractorDialog", u"\u0412\u044b\u0431\u043e\u0440 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430:", None))
        self.pb_back_to_contracts.setText(QCoreApplication.translate("ContractorDialog", u"\u041d\u0430\u0437\u0430\u0434", None))
        self.pb_cancel_3.setText(QCoreApplication.translate("ContractorDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_accept.setText(QCoreApplication.translate("ContractorDialog", u"\u041e\u0442\u043a\u0440\u044b\u0442\u044c", None))
        self.label_3.setText(QCoreApplication.translate("ContractorDialog", u"\u0412\u044b\u0431\u043e\u0440 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430:", None))
    # retranslateUi

