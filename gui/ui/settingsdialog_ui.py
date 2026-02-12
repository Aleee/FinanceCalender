# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settingsdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QWidget)

from gui.commonwidgets.colorpushbutton import ColorPushButton
import resources_rc

class Ui_settingsdialog(object):
    def setupUi(self, settingsdialog):
        if not settingsdialog.objectName():
            settingsdialog.setObjectName(u"settingsdialog")
        settingsdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        settingsdialog.resize(622, 500)
        self.gridLayout = QGridLayout(settingsdialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_ok = QPushButton(settingsdialog)
        self.pb_ok.setObjectName(u"pb_ok")

        self.horizontalLayout.addWidget(self.pb_ok)

        self.pb_cancel = QPushButton(settingsdialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout.addWidget(self.pb_cancel)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)

        self.stw = QStackedWidget(settingsdialog)
        self.stw.setObjectName(u"stw")
        self.pg_common = QWidget()
        self.pg_common.setObjectName(u"pg_common")
        self.gridLayout_11 = QGridLayout(self.pg_common)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_11.addItem(self.verticalSpacer_3, 3, 0, 1, 1)

        self.groupBox = QGroupBox(self.pg_common)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.rb_fontsize_1 = QRadioButton(self.groupBox)
        self.rb_fontsize_1.setObjectName(u"rb_fontsize_1")
        self.rb_fontsize_1.setChecked(True)

        self.horizontalLayout_2.addWidget(self.rb_fontsize_1)

        self.rb_fontsize_2 = QRadioButton(self.groupBox)
        self.rb_fontsize_2.setObjectName(u"rb_fontsize_2")

        self.horizontalLayout_2.addWidget(self.rb_fontsize_2)

        self.rb_fontsize_3 = QRadioButton(self.groupBox)
        self.rb_fontsize_3.setObjectName(u"rb_fontsize_3")

        self.horizontalLayout_2.addWidget(self.rb_fontsize_3)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)


        self.gridLayout_11.addWidget(self.groupBox, 0, 0, 1, 1)

        self.groupBox_9 = QGroupBox(self.pg_common)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.gridLayout_13 = QGridLayout(self.groupBox_9)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gridLayout_13.setVerticalSpacing(2)
        self.cmb_loadpaid = QComboBox(self.groupBox_9)
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.setObjectName(u"cmb_loadpaid")

        self.gridLayout_13.addWidget(self.cmb_loadpaid, 0, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox_9)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_13.addWidget(self.label_2, 0, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_13.addItem(self.horizontalSpacer_2, 0, 3, 1, 1)

        self.la_paidloadtooltip = QLabel(self.groupBox_9)
        self.la_paidloadtooltip.setObjectName(u"la_paidloadtooltip")

        self.gridLayout_13.addWidget(self.la_paidloadtooltip, 0, 4, 1, 1)


        self.gridLayout_11.addWidget(self.groupBox_9, 1, 0, 2, 1)

        self.stw.addWidget(self.pg_common)
        self.pg_appear = QWidget()
        self.pg_appear.setObjectName(u"pg_appear")
        self.gridLayout_2 = QGridLayout(self.pg_appear)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.groupBox_5 = QGroupBox(self.pg_appear)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_8 = QGridLayout(self.groupBox_5)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.chb_formatboldheader = QCheckBox(self.groupBox_5)
        self.chb_formatboldheader.setObjectName(u"chb_formatboldheader")

        self.gridLayout_8.addWidget(self.chb_formatboldheader, 0, 0, 1, 2)

        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_8.addWidget(self.label_7, 2, 1, 1, 1)

        self.pb_backgroundsectionheader = ColorPushButton(self.groupBox_5)
        self.pb_backgroundsectionheader.setObjectName(u"pb_backgroundsectionheader")
        self.pb_backgroundsectionheader.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_8.addWidget(self.pb_backgroundsectionheader, 2, 0, 1, 1)

        self.label_6 = QLabel(self.groupBox_5)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_8.addWidget(self.label_6, 1, 1, 1, 1)

        self.label_10 = QLabel(self.groupBox_5)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_8.addWidget(self.label_10, 3, 1, 1, 1)

        self.pb_foregroundsectionheader = ColorPushButton(self.groupBox_5)
        self.pb_foregroundsectionheader.setObjectName(u"pb_foregroundsectionheader")
        self.pb_foregroundsectionheader.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_8.addWidget(self.pb_foregroundsectionheader, 1, 0, 1, 1)

        self.pb_foregroundsubsectionheader = ColorPushButton(self.groupBox_5)
        self.pb_foregroundsubsectionheader.setObjectName(u"pb_foregroundsubsectionheader")
        self.pb_foregroundsubsectionheader.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_8.addWidget(self.pb_foregroundsubsectionheader, 3, 0, 1, 1)

        self.pb_backgroundsubsectionheader = ColorPushButton(self.groupBox_5)
        self.pb_backgroundsubsectionheader.setObjectName(u"pb_backgroundsubsectionheader")
        self.pb_backgroundsubsectionheader.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_8.addWidget(self.pb_backgroundsubsectionheader, 4, 0, 1, 1)

        self.label_11 = QLabel(self.groupBox_5)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_8.addWidget(self.label_11, 4, 1, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_5, 4, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.pg_appear)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_7 = QGridLayout(self.groupBox_4)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.pb_backgroundtoday = ColorPushButton(self.groupBox_4)
        self.pb_backgroundtoday.setObjectName(u"pb_backgroundtoday")
        self.pb_backgroundtoday.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_7.addWidget(self.pb_backgroundtoday, 2, 0, 1, 1)

        self.chb_formatboldtoday = QCheckBox(self.groupBox_4)
        self.chb_formatboldtoday.setObjectName(u"chb_formatboldtoday")

        self.gridLayout_7.addWidget(self.chb_formatboldtoday, 0, 0, 1, 2)

        self.label_3 = QLabel(self.groupBox_4)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_7.addWidget(self.label_3, 2, 1, 1, 1)

        self.pb_foregroundtoday = ColorPushButton(self.groupBox_4)
        self.pb_foregroundtoday.setObjectName(u"pb_foregroundtoday")
        self.pb_foregroundtoday.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_7.addWidget(self.pb_foregroundtoday, 1, 0, 1, 1)

        self.label_5 = QLabel(self.groupBox_4)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_7.addWidget(self.label_5, 1, 1, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_4, 1, 1, 1, 1)

        self.groupBox_6 = QGroupBox(self.pg_appear)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_9 = QGridLayout(self.groupBox_6)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.label_8 = QLabel(self.groupBox_6)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout_9.addWidget(self.label_8, 1, 1, 1, 1)

        self.pb_foregroundsectionfooter = ColorPushButton(self.groupBox_6)
        self.pb_foregroundsectionfooter.setObjectName(u"pb_foregroundsectionfooter")
        self.pb_foregroundsectionfooter.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_9.addWidget(self.pb_foregroundsectionfooter, 1, 0, 1, 1)

        self.pb_foregroundsubsectionfooter = ColorPushButton(self.groupBox_6)
        self.pb_foregroundsubsectionfooter.setObjectName(u"pb_foregroundsubsectionfooter")
        self.pb_foregroundsubsectionfooter.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_9.addWidget(self.pb_foregroundsubsectionfooter, 3, 0, 1, 1)

        self.pb_backgroundsectionfooter = ColorPushButton(self.groupBox_6)
        self.pb_backgroundsectionfooter.setObjectName(u"pb_backgroundsectionfooter")
        self.pb_backgroundsectionfooter.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_9.addWidget(self.pb_backgroundsectionfooter, 2, 0, 1, 1)

        self.chb_formatboldfooter = QCheckBox(self.groupBox_6)
        self.chb_formatboldfooter.setObjectName(u"chb_formatboldfooter")

        self.gridLayout_9.addWidget(self.chb_formatboldfooter, 0, 0, 1, 2)

        self.label_9 = QLabel(self.groupBox_6)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_9.addWidget(self.label_9, 2, 1, 1, 1)

        self.pb_backgroundsubsectionfooter = ColorPushButton(self.groupBox_6)
        self.pb_backgroundsubsectionfooter.setObjectName(u"pb_backgroundsubsectionfooter")
        self.pb_backgroundsubsectionfooter.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_9.addWidget(self.pb_backgroundsubsectionfooter, 4, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_6)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_9.addWidget(self.label_12, 3, 1, 1, 1)

        self.label_13 = QLabel(self.groupBox_6)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_9.addWidget(self.label_13, 4, 1, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_6, 4, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 5, 0, 1, 1)

        self.groupBox_3 = QGroupBox(self.pg_appear)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_6 = QGridLayout(self.groupBox_3)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label = QLabel(self.groupBox_3)
        self.label.setObjectName(u"label")

        self.gridLayout_6.addWidget(self.label, 2, 1, 1, 2)

        self.pb_backgrounddue = ColorPushButton(self.groupBox_3)
        self.pb_backgrounddue.setObjectName(u"pb_backgrounddue")
        self.pb_backgrounddue.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_6.addWidget(self.pb_backgrounddue, 2, 0, 1, 1)

        self.pb_foregrounddue = ColorPushButton(self.groupBox_3)
        self.pb_foregrounddue.setObjectName(u"pb_foregrounddue")
        self.pb_foregrounddue.setMaximumSize(QSize(30, 16777215))

        self.gridLayout_6.addWidget(self.pb_foregrounddue, 1, 0, 1, 1)

        self.chb_formatbolddue = QCheckBox(self.groupBox_3)
        self.chb_formatbolddue.setObjectName(u"chb_formatbolddue")

        self.gridLayout_6.addWidget(self.chb_formatbolddue, 0, 0, 1, 3)

        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_6.addWidget(self.label_4, 1, 1, 1, 2)


        self.gridLayout_2.addWidget(self.groupBox_3, 1, 0, 1, 1)

        self.groupBox_8 = QGroupBox(self.pg_appear)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.gridLayout_12 = QGridLayout(self.groupBox_8)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.chb_zebrastyle = QCheckBox(self.groupBox_8)
        self.chb_zebrastyle.setObjectName(u"chb_zebrastyle")

        self.gridLayout_12.addWidget(self.chb_zebrastyle, 1, 0, 1, 1)

        self.chb_verticalgrid = QCheckBox(self.groupBox_8)
        self.chb_verticalgrid.setObjectName(u"chb_verticalgrid")

        self.gridLayout_12.addWidget(self.chb_verticalgrid, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_8, 0, 0, 1, 2)

        self.stw.addWidget(self.pg_appear)
        self.pg_storage = QWidget()
        self.pg_storage.setObjectName(u"pg_storage")
        self.gridLayout_4 = QGridLayout(self.pg_storage)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.groupBox_2 = QGroupBox(self.pg_storage)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_5 = QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.chb_dataintable_totalamount = QCheckBox(self.groupBox_2)
        self.chb_dataintable_totalamount.setObjectName(u"chb_dataintable_totalamount")
        self.chb_dataintable_totalamount.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_totalamount, 0, 0, 1, 1)

        self.chb_dataintable_paymenttype = QCheckBox(self.groupBox_2)
        self.chb_dataintable_paymenttype.setObjectName(u"chb_dataintable_paymenttype")
        self.chb_dataintable_paymenttype.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_paymenttype, 0, 1, 1, 1)

        self.chb_dataintable_responsible = QCheckBox(self.groupBox_2)
        self.chb_dataintable_responsible.setObjectName(u"chb_dataintable_responsible")
        self.chb_dataintable_responsible.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_responsible, 2, 1, 1, 1)

        self.chb_dataintable_descr = QCheckBox(self.groupBox_2)
        self.chb_dataintable_descr.setObjectName(u"chb_dataintable_descr")
        self.chb_dataintable_descr.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_descr, 2, 0, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_2, 0, 0, 1, 2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer_2, 3, 0, 1, 1)

        self.groupBox_7 = QGroupBox(self.pg_storage)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.gridLayout_10 = QGridLayout(self.groupBox_7)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.chb_datainfo_totalamount = QCheckBox(self.groupBox_7)
        self.chb_datainfo_totalamount.setObjectName(u"chb_datainfo_totalamount")

        self.gridLayout_10.addWidget(self.chb_datainfo_totalamount, 0, 0, 1, 1)

        self.chb_datainfo_paymenttype = QCheckBox(self.groupBox_7)
        self.chb_datainfo_paymenttype.setObjectName(u"chb_datainfo_paymenttype")

        self.gridLayout_10.addWidget(self.chb_datainfo_paymenttype, 0, 1, 1, 1)

        self.chb_datainfo_percentage = QCheckBox(self.groupBox_7)
        self.chb_datainfo_percentage.setObjectName(u"chb_datainfo_percentage")

        self.gridLayout_10.addWidget(self.chb_datainfo_percentage, 3, 0, 1, 1)

        self.chb_datainfo_descr = QCheckBox(self.groupBox_7)
        self.chb_datainfo_descr.setObjectName(u"chb_datainfo_descr")

        self.gridLayout_10.addWidget(self.chb_datainfo_descr, 1, 0, 1, 1)

        self.chb_datainfo_responsible = QCheckBox(self.groupBox_7)
        self.chb_datainfo_responsible.setObjectName(u"chb_datainfo_responsible")

        self.gridLayout_10.addWidget(self.chb_datainfo_responsible, 1, 1, 1, 1)

        self.chb_datainfo_createdate = QCheckBox(self.groupBox_7)
        self.chb_datainfo_createdate.setObjectName(u"chb_datainfo_createdate")

        self.gridLayout_10.addWidget(self.chb_datainfo_createdate, 3, 1, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_7, 1, 0, 1, 2)

        self.groupBox_10 = QGroupBox(self.pg_storage)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.gridLayout_14 = QGridLayout(self.groupBox_10)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.pb_exportpath = QPushButton(self.groupBox_10)
        self.pb_exportpath.setObjectName(u"pb_exportpath")
        self.pb_exportpath.setMinimumSize(QSize(90, 0))
        self.pb_exportpath.setMaximumSize(QSize(90, 16777215))

        self.gridLayout_14.addWidget(self.pb_exportpath, 2, 2, 1, 1)

        self.chb_frozenheader = QCheckBox(self.groupBox_10)
        self.chb_frozenheader.setObjectName(u"chb_frozenheader")

        self.gridLayout_14.addWidget(self.chb_frozenheader, 0, 0, 1, 2)

        self.label_15 = QLabel(self.groupBox_10)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_14.addWidget(self.label_15, 1, 0, 1, 1)

        self.le_exportpath = QLineEdit(self.groupBox_10)
        self.le_exportpath.setObjectName(u"le_exportpath")
        self.le_exportpath.setEnabled(True)
        self.le_exportpath.setReadOnly(True)

        self.gridLayout_14.addWidget(self.le_exportpath, 2, 0, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_10, 2, 0, 1, 2)

        self.stw.addWidget(self.pg_storage)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.gridLayout_15 = QGridLayout(self.page)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.groupBox_11 = QGroupBox(self.page)
        self.groupBox_11.setObjectName(u"groupBox_11")
        self.gridLayout_16 = QGridLayout(self.groupBox_11)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.cmb_autosave = QComboBox(self.groupBox_11)
        self.cmb_autosave.addItem("")
        self.cmb_autosave.addItem("")
        self.cmb_autosave.addItem("")
        self.cmb_autosave.addItem("")
        self.cmb_autosave.addItem("")
        self.cmb_autosave.setObjectName(u"cmb_autosave")
        self.cmb_autosave.setMinimumSize(QSize(120, 0))

        self.gridLayout_16.addWidget(self.cmb_autosave, 0, 1, 1, 1)

        self.label_16 = QLabel(self.groupBox_11)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_16.addWidget(self.label_16, 0, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_16.addItem(self.horizontalSpacer_3, 0, 2, 1, 1)


        self.gridLayout_15.addWidget(self.groupBox_11, 0, 0, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_15.addItem(self.verticalSpacer_4, 3, 0, 1, 1)

        self.groupBox_12 = QGroupBox(self.page)
        self.groupBox_12.setObjectName(u"groupBox_12")
        self.gridLayout_17 = QGridLayout(self.groupBox_12)
        self.gridLayout_17.setObjectName(u"gridLayout_17")
        self.label_17 = QLabel(self.groupBox_12)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_17.addWidget(self.label_17, 0, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_18 = QLabel(self.groupBox_12)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_3.addWidget(self.label_18)

        self.horizontalSpacer_5 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)

        self.cmb_backupautodelete = QComboBox(self.groupBox_12)
        self.cmb_backupautodelete.addItem("")
        self.cmb_backupautodelete.addItem("")
        self.cmb_backupautodelete.addItem("")
        self.cmb_backupautodelete.addItem("")
        self.cmb_backupautodelete.setObjectName(u"cmb_backupautodelete")
        self.cmb_backupautodelete.setMinimumSize(QSize(90, 0))
        self.cmb_backupautodelete.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout_3.addWidget(self.cmb_backupautodelete)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.gridLayout_17.addLayout(self.horizontalLayout_3, 2, 0, 1, 3)

        self.le_backuppath = QLineEdit(self.groupBox_12)
        self.le_backuppath.setObjectName(u"le_backuppath")

        self.gridLayout_17.addWidget(self.le_backuppath, 1, 0, 1, 2)

        self.pb_backuppath = QPushButton(self.groupBox_12)
        self.pb_backuppath.setObjectName(u"pb_backuppath")

        self.gridLayout_17.addWidget(self.pb_backuppath, 1, 2, 1, 1)


        self.gridLayout_15.addWidget(self.groupBox_12, 1, 0, 1, 1)

        self.groupBox_13 = QGroupBox(self.page)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_13)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pb_restorefrombackup = QPushButton(self.groupBox_13)
        self.pb_restorefrombackup.setObjectName(u"pb_restorefrombackup")

        self.horizontalLayout_4.addWidget(self.pb_restorefrombackup)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.gridLayout_15.addWidget(self.groupBox_13, 2, 0, 1, 1)

        self.stw.addWidget(self.page)

        self.gridLayout.addWidget(self.stw, 0, 1, 1, 1)

        self.lw_menu = QListWidget(settingsdialog)
        icon = QIcon()
        icon.addFile(u":/icon-settings/designer/icons/generalsettings.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem.setIcon(icon);
        icon1 = QIcon()
        icon1.addFile(u":/icon-settings/designer/icons/appearance.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem1.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem1.setIcon(icon1);
        icon2 = QIcon()
        icon2.addFile(u":/icon-settings/designer/icons/table.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem2.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem2.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u":/icon-settings/designer/icons/storage.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem3.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem3.setIcon(icon3);
        self.lw_menu.setObjectName(u"lw_menu")
        self.lw_menu.setMinimumSize(QSize(170, 0))
        self.lw_menu.setMaximumSize(QSize(170, 16777215))
        self.lw_menu.setSupportedDragActions(Qt.DropAction.IgnoreAction)

        self.gridLayout.addWidget(self.lw_menu, 0, 0, 1, 1)


        self.retranslateUi(settingsdialog)

        self.stw.setCurrentIndex(1)
        self.lw_menu.setCurrentRow(-1)


        QMetaObject.connectSlotsByName(settingsdialog)
    # setupUi

    def retranslateUi(self, settingsdialog):
        settingsdialog.setWindowTitle(QCoreApplication.translate("settingsdialog", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.pb_ok.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u041a", None))
        self.pb_cancel.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.groupBox.setTitle(QCoreApplication.translate("settingsdialog", u"\u0420\u0430\u0437\u043c\u0435\u0440 \u0448\u0440\u0438\u0444\u0442\u0430", None))
        self.rb_fontsize_1.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u044b\u0447\u043d\u044b\u0439", None))
        self.rb_fontsize_2.setText(QCoreApplication.translate("settingsdialog", u"\u0411\u043e\u043b\u044c\u0448\u043e\u0439", None))
        self.rb_fontsize_3.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0433\u0440\u043e\u043c\u043d\u044b\u0439", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("settingsdialog", u"\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.cmb_loadpaid.setItemText(0, QCoreApplication.translate("settingsdialog", u"\u043e\u0434\u0438\u043d \u043c\u0435\u0441\u044f\u0446", None))
        self.cmb_loadpaid.setItemText(1, QCoreApplication.translate("settingsdialog", u"\u0442\u0440\u0438 \u043c\u0435\u0441\u044f\u0446\u0430", None))
        self.cmb_loadpaid.setItemText(2, QCoreApplication.translate("settingsdialog", u"\u043f\u043e\u043b\u0433\u043e\u0434\u0430", None))
        self.cmb_loadpaid.setItemText(3, QCoreApplication.translate("settingsdialog", u"\u043e\u0434\u0438\u043d \u0433\u043e\u0434", None))
        self.cmb_loadpaid.setItemText(4, QCoreApplication.translate("settingsdialog", u"\u0432\u0441\u0435 \u0432\u0440\u0435\u043c\u044f", None))

        self.label_2.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u044c \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438 \u0437\u0430  ", None))
#if QT_CONFIG(tooltip)
        self.la_paidloadtooltip.setToolTip(QCoreApplication.translate("settingsdialog", u"<html><head/><body><p>\u041e\u0442\u0441\u0447\u0435\u0442 \u0432\u0435\u0434\u0435\u0442\u0441\u044f \u0441 \u0434\u0430\u0442\u044b \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u043f\u043b\u0430\u0442\u0435\u0436\u0430</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.la_paidloadtooltip.setText(QCoreApplication.translate("settingsdialog", u"  ?  ", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438", None))
        self.chb_formatboldheader.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_7.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.pb_backgroundsectionheader.setText("")
        self.label_6.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.label_10.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 \u043f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.pb_foregroundsectionheader.setText("")
        self.pb_foregroundsubsectionheader.setText("")
        self.pb_backgroundsubsectionheader.setText("")
        self.label_11.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 \u043f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u0441\u0435\u0433\u043e\u0434\u043d\u044f\u0448\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.pb_backgroundtoday.setText("")
        self.chb_formatboldtoday.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_3.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 ", None))
        self.pb_foregroundtoday.setText("")
        self.label_5.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u0441\u0442\u0440\u043e\u043a\u0438 \u0438\u0442\u043e\u0433\u043e\u0432", None))
        self.label_8.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.pb_foregroundsectionfooter.setText("")
        self.pb_foregroundsubsectionfooter.setText("")
        self.pb_backgroundsectionfooter.setText("")
        self.chb_formatboldfooter.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_9.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.pb_backgroundsubsectionfooter.setText("")
        self.label_12.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 \u043f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.label_13.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 \u043f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.label.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 ", None))
        self.pb_backgrounddue.setText("")
        self.pb_foregrounddue.setText("")
        self.chb_formatbolddue.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_4.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 ", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442 \u0441\u0442\u0440\u043e\u043a", None))
        self.chb_zebrastyle.setText(QCoreApplication.translate("settingsdialog", u"\u0427\u0435\u0440\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 \u0441\u0442\u0440\u043e\u043a", None))
        self.chb_verticalgrid.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u0435\u0440\u0442\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0435 \u0433\u0440\u0430\u043d\u0438\u0446\u044b", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("settingsdialog", u"\u0414\u0430\u043d\u043d\u044b\u0435 \u0432 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u0435", None))
        self.chb_dataintable_totalamount.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_dataintable_paymenttype.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_dataintable_responsible.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0435 \u043b\u0438\u0446\u043e", None))
        self.chb_dataintable_descr.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("settingsdialog", u"\u0414\u0430\u043d\u043d\u044b\u0435 \u0432 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u043e\u043d\u043d\u043e\u0439 \u043f\u0430\u043d\u0435\u043b\u0438", None))
        self.chb_datainfo_totalamount.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_datainfo_paymenttype.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_datainfo_percentage.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043f\u043e\u0433\u0430\u0448\u0435\u043d\u0438\u044f", None))
        self.chb_datainfo_descr.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_datainfo_responsible.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0435 \u043b\u0438\u0446\u043e", None))
        self.chb_datainfo_createdate.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u0430\u0442\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("settingsdialog", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u044d\u043a\u0441\u043f\u043e\u0440\u0442\u0430", None))
        self.pb_exportpath.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", None))
        self.chb_frozenheader.setText(QCoreApplication.translate("settingsdialog", u"\u0417\u0430\u043a\u0440\u0435\u043f\u043b\u044f\u0442\u044c \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u0447\u043d\u0443\u044e \u0447\u0430\u0441\u0442\u044c \u0432 XLSX-\u0444\u0430\u0439\u043b\u0435", None))
        self.label_15.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u043f\u043a\u0430 \u0434\u043b\u044f \u044d\u043a\u0441\u043f\u043e\u0440\u0442\u0430 \u0444\u0430\u0439\u043b\u043e\u0432:", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("settingsdialog", u"\u0410\u0432\u0442\u043e\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435", None))
        self.cmb_autosave.setItemText(0, QCoreApplication.translate("settingsdialog", u"5 \u043c\u0438\u043d\u0443\u0442", None))
        self.cmb_autosave.setItemText(1, QCoreApplication.translate("settingsdialog", u"15 \u043c\u0438\u043d\u0443\u0442", None))
        self.cmb_autosave.setItemText(2, QCoreApplication.translate("settingsdialog", u"30 \u043c\u0438\u043d\u0443\u0442", None))
        self.cmb_autosave.setItemText(3, QCoreApplication.translate("settingsdialog", u"1 \u0447\u0430\u0441", None))
        self.cmb_autosave.setItemText(4, QCoreApplication.translate("settingsdialog", u"3 \u0447\u0430\u0441\u0430", None))

        self.label_16.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b \u0430\u0432\u0442\u043e\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f: ", None))
        self.groupBox_12.setTitle(QCoreApplication.translate("settingsdialog", u"\u0420\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0435 \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.label_17.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u043f\u043a\u0430 \u0434\u043b\u044f \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0433\u043e \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f:", None))
        self.label_18.setText(QCoreApplication.translate("settingsdialog", u"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u0435 \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u044b\u0445 \u043a\u043e\u043f\u0438\u0439:", None))
        self.cmb_backupautodelete.setItemText(0, QCoreApplication.translate("settingsdialog", u"1 \u043d\u0435\u0434\u0435\u043b\u044f", None))
        self.cmb_backupautodelete.setItemText(1, QCoreApplication.translate("settingsdialog", u"1 \u043c\u0435\u0441\u044f\u0446", None))
        self.cmb_backupautodelete.setItemText(2, QCoreApplication.translate("settingsdialog", u"6 \u043c\u0435\u0441\u044f\u0446\u0435\u0432", None))
        self.cmb_backupautodelete.setItemText(3, QCoreApplication.translate("settingsdialog", u"\u043d\u0438\u043a\u043e\u0433\u0434\u0430", None))

        self.pb_backuppath.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("settingsdialog", u"\u0412\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435", None))
        self.pb_restorefrombackup.setText(QCoreApplication.translate("settingsdialog", u"  \u0412\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0438\u0437 \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0439 \u043a\u043e\u043f\u0438\u0438  ", None))

        __sortingEnabled = self.lw_menu.isSortingEnabled()
        self.lw_menu.setSortingEnabled(False)
        ___qlistwidgetitem = self.lw_menu.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u0449\u0438\u0435", None));
        ___qlistwidgetitem1 = self.lw_menu.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435", None));
        ___qlistwidgetitem2 = self.lw_menu.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("settingsdialog", u"\u0422\u0430\u0431\u043b\u0438\u0446\u0430", None));
        ___qlistwidgetitem3 = self.lw_menu.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("settingsdialog", u"\u0425\u0440\u0430\u043d\u0435\u043d\u0438\u0435", None));
        self.lw_menu.setSortingEnabled(__sortingEnabled)

    # retranslateUi

