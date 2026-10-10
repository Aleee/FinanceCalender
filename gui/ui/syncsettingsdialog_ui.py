# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'syncsettingsdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
    QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_SyncSettingsDialog(object):
    def setupUi(self, SyncSettingsDialog):
        if not SyncSettingsDialog.objectName():
            SyncSettingsDialog.setObjectName(u"SyncSettingsDialog")
        SyncSettingsDialog.resize(480, 360)
        self.verticalLayout = QVBoxLayout(SyncSettingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fl_main = QFormLayout()
        self.fl_main.setObjectName(u"fl_main")
        self.chb_enabled = QCheckBox(SyncSettingsDialog)
        self.chb_enabled.setObjectName(u"chb_enabled")

        self.fl_main.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.chb_enabled)

        self.label_channel = QLabel(SyncSettingsDialog)
        self.label_channel.setObjectName(u"label_channel")

        self.fl_main.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_channel)

        self.cmb_channel = QComboBox(SyncSettingsDialog)
        self.cmb_channel.addItem("")
        self.cmb_channel.addItem("")
        self.cmb_channel.setObjectName(u"cmb_channel")

        self.fl_main.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cmb_channel)

        self.label_token = QLabel(SyncSettingsDialog)
        self.label_token.setObjectName(u"label_token")

        self.fl_main.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_token)

        self.le_token = QLineEdit(SyncSettingsDialog)
        self.le_token.setObjectName(u"le_token")
        self.le_token.setEchoMode(QLineEdit.EchoMode.Password)

        self.fl_main.setWidget(2, QFormLayout.ItemRole.FieldRole, self.le_token)

        self.label_tokenexpires = QLabel(SyncSettingsDialog)
        self.label_tokenexpires.setObjectName(u"label_tokenexpires")

        self.fl_main.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_tokenexpires)

        self.de_tokenexpires = QDateEdit(SyncSettingsDialog)
        self.de_tokenexpires.setObjectName(u"de_tokenexpires")
        self.de_tokenexpires.setCalendarPopup(True)
        self.de_tokenexpires.setMinimumDate(QDate(2000, 1, 1))

        self.fl_main.setWidget(3, QFormLayout.ItemRole.FieldRole, self.de_tokenexpires)

        self.label_diskfolder = QLabel(SyncSettingsDialog)
        self.label_diskfolder.setObjectName(u"label_diskfolder")

        self.fl_main.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_diskfolder)

        self.le_diskfolder = QLineEdit(SyncSettingsDialog)
        self.le_diskfolder.setObjectName(u"le_diskfolder")

        self.fl_main.setWidget(4, QFormLayout.ItemRole.FieldRole, self.le_diskfolder)

        self.pb_check = QPushButton(SyncSettingsDialog)
        self.pb_check.setObjectName(u"pb_check")

        self.fl_main.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.pb_check)

        self.label_folder = QLabel(SyncSettingsDialog)
        self.label_folder.setObjectName(u"label_folder")

        self.fl_main.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_folder)

        self.hl_folder = QHBoxLayout()
        self.hl_folder.setObjectName(u"hl_folder")
        self.le_folder = QLineEdit(SyncSettingsDialog)
        self.le_folder.setObjectName(u"le_folder")

        self.hl_folder.addWidget(self.le_folder)

        self.pb_folder = QPushButton(SyncSettingsDialog)
        self.pb_folder.setObjectName(u"pb_folder")

        self.hl_folder.addWidget(self.pb_folder)


        self.fl_main.setLayout(6, QFormLayout.ItemRole.FieldRole, self.hl_folder)

        self.label_author = QLabel(SyncSettingsDialog)
        self.label_author.setObjectName(u"label_author")

        self.fl_main.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_author)

        self.le_author = QLineEdit(SyncSettingsDialog)
        self.le_author.setObjectName(u"le_author")

        self.fl_main.setWidget(7, QFormLayout.ItemRole.FieldRole, self.le_author)

        self.label_interval = QLabel(SyncSettingsDialog)
        self.label_interval.setObjectName(u"label_interval")

        self.fl_main.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_interval)

        self.spb_interval = QSpinBox(SyncSettingsDialog)
        self.spb_interval.setObjectName(u"spb_interval")
        self.spb_interval.setMinimum(1)
        self.spb_interval.setMaximum(60)

        self.fl_main.setWidget(8, QFormLayout.ItemRole.FieldRole, self.spb_interval)

        self.label_keepdays = QLabel(SyncSettingsDialog)
        self.label_keepdays.setObjectName(u"label_keepdays")

        self.fl_main.setWidget(9, QFormLayout.ItemRole.LabelRole, self.label_keepdays)

        self.spb_keepdays = QSpinBox(SyncSettingsDialog)
        self.spb_keepdays.setObjectName(u"spb_keepdays")
        self.spb_keepdays.setMinimum(1)
        self.spb_keepdays.setMaximum(365)

        self.fl_main.setWidget(9, QFormLayout.ItemRole.FieldRole, self.spb_keepdays)


        self.verticalLayout.addLayout(self.fl_main)

        self.hl_buttons = QHBoxLayout()
        self.hl_buttons.setObjectName(u"hl_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_buttons.addItem(self.horizontalSpacer)

        self.pb_ok = QPushButton(SyncSettingsDialog)
        self.pb_ok.setObjectName(u"pb_ok")

        self.hl_buttons.addWidget(self.pb_ok)

        self.pb_cancel = QPushButton(SyncSettingsDialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.hl_buttons.addWidget(self.pb_cancel)


        self.verticalLayout.addLayout(self.hl_buttons)


        self.retranslateUi(SyncSettingsDialog)

        QMetaObject.connectSlotsByName(SyncSettingsDialog)
    # setupUi

    def retranslateUi(self, SyncSettingsDialog):
        SyncSettingsDialog.setWindowTitle(QCoreApplication.translate("SyncSettingsDialog", u"\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f", None))
        self.chb_enabled.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044e", None))
        self.label_channel.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0421\u043f\u043e\u0441\u043e\u0431 \u043e\u0431\u043c\u0435\u043d\u0430:", None))
        self.cmb_channel.setItemText(0, QCoreApplication.translate("SyncSettingsDialog", u"\u042f\u043d\u0434\u0435\u043a\u0441.\u0414\u0438\u0441\u043a", None))
        self.cmb_channel.setItemText(1, QCoreApplication.translate("SyncSettingsDialog", u"\u041f\u0430\u043f\u043a\u0430", None))

        self.label_token.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0422\u043e\u043a\u0435\u043d \u042f\u043d\u0434\u0435\u043a\u0441\u0430:", None))
        self.label_tokenexpires.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0422\u043e\u043a\u0435\u043d \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u0435\u0442 \u0434\u043e:", None))
        self.de_tokenexpires.setSpecialValueText(QCoreApplication.translate("SyncSettingsDialog", u"\u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d", None))
        self.de_tokenexpires.setDisplayFormat(QCoreApplication.translate("SyncSettingsDialog", u"dd.MM.yyyy", None))
        self.label_diskfolder.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u041f\u0430\u043f\u043a\u0430 \u043d\u0430 \u0414\u0438\u0441\u043a\u0435:", None))
        self.pb_check.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435", None))
        self.label_folder.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u041f\u0430\u043f\u043a\u0430 \u043e\u0431\u043c\u0435\u043d\u0430:", None))
        self.pb_folder.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c", None))
        self.label_author.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0418\u043c\u044f \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f:", None))
        self.label_interval.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0442\u044c \u043e\u0431\u0449\u0443\u044e \u0431\u0430\u0437\u0443 \u043a\u0430\u0436\u0434\u044b\u0435:", None))
        self.spb_interval.setSuffix(QCoreApplication.translate("SyncSettingsDialog", u" \u043c\u0438\u043d", None))
        self.label_keepdays.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u0425\u0440\u0430\u043d\u0438\u0442\u044c \u0435\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u044b\u0435 \u043a\u043e\u043f\u0438\u0438 \u043e\u0431\u0449\u0435\u0439 \u0431\u0430\u0437\u044b:", None))
        self.spb_keepdays.setSuffix(QCoreApplication.translate("SyncSettingsDialog", u" \u0434\u043d", None))
        self.pb_ok.setText(QCoreApplication.translate("SyncSettingsDialog", u"OK", None))
        self.pb_cancel.setText(QCoreApplication.translate("SyncSettingsDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

