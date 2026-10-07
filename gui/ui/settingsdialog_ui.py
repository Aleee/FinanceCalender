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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListView,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from gui.commonwidgets.colorpushbutton import ColorPushButton
import resources_rc

class Ui_settingsdialog(object):
    def setupUi(self, settingsdialog):
        if not settingsdialog.objectName():
            settingsdialog.setObjectName(u"settingsdialog")
        settingsdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        settingsdialog.resize(622, 530)
        self.gridLayout = QGridLayout(settingsdialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pb_cancel = QPushButton(settingsdialog)
        self.pb_cancel.setObjectName(u"pb_cancel")

        self.horizontalLayout.addWidget(self.pb_cancel)

        self.pb_ok = QPushButton(settingsdialog)
        self.pb_ok.setObjectName(u"pb_ok")

        self.horizontalLayout.addWidget(self.pb_ok)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)

        self.stw = QStackedWidget(settingsdialog)
        self.stw.setObjectName(u"stw")
        self.pg_common = QWidget()
        self.pg_common.setObjectName(u"pg_common")
        self.gridLayout_11 = QGridLayout(self.pg_common)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.groupBox_9 = QGroupBox(self.pg_common)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.gridLayout_13 = QGridLayout(self.groupBox_9)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_16 = QLabel(self.groupBox_9)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_6.addWidget(self.label_16)

        self.horizontalSpacer_8 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_8)

        self.cmb_csv_responsible = QComboBox(self.groupBox_9)
        self.cmb_csv_responsible.setObjectName(u"cmb_csv_responsible")

        self.horizontalLayout_6.addWidget(self.cmb_csv_responsible)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_9)


        self.gridLayout_13.addLayout(self.horizontalLayout_6, 8, 0, 1, 3)

        self.spb_csv_rowfirsttransaction = QSpinBox(self.groupBox_9)
        self.spb_csv_rowfirsttransaction.setObjectName(u"spb_csv_rowfirsttransaction")
        self.spb_csv_rowfirsttransaction.setMinimumSize(QSize(30, 0))
        self.spb_csv_rowfirsttransaction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spb_csv_rowfirsttransaction.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.gridLayout_13.addWidget(self.spb_csv_rowfirsttransaction, 1, 1, 1, 1)

        self.spb_csv_rowperiod = QSpinBox(self.groupBox_9)
        self.spb_csv_rowperiod.setObjectName(u"spb_csv_rowperiod")
        self.spb_csv_rowperiod.setMinimumSize(QSize(30, 0))
        self.spb_csv_rowperiod.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spb_csv_rowperiod.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.gridLayout_13.addWidget(self.spb_csv_rowperiod, 0, 1, 1, 1)

        self.te_csv_patterns = QPlainTextEdit(self.groupBox_9)
        self.te_csv_patterns.setObjectName(u"te_csv_patterns")

        self.gridLayout_13.addWidget(self.te_csv_patterns, 7, 0, 1, 3)

        self.label_20 = QLabel(self.groupBox_9)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_13.addWidget(self.label_20, 4, 0, 1, 1)

        self.label_19 = QLabel(self.groupBox_9)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_13.addWidget(self.label_19, 2, 0, 1, 3)

        self.le_csv_unp = QLineEdit(self.groupBox_9)
        self.le_csv_unp.setObjectName(u"le_csv_unp")

        self.gridLayout_13.addWidget(self.le_csv_unp, 5, 0, 1, 3)

        self.le_csv_columns = QLineEdit(self.groupBox_9)
        self.le_csv_columns.setObjectName(u"le_csv_columns")

        self.gridLayout_13.addWidget(self.le_csv_columns, 3, 0, 1, 3)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_13.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)

        self.label_15 = QLabel(self.groupBox_9)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_13.addWidget(self.label_15, 1, 0, 1, 1)

        self.label_2 = QLabel(self.groupBox_9)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_13.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_22 = QLabel(self.groupBox_9)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_13.addWidget(self.label_22, 6, 0, 1, 1)


        self.gridLayout_11.addWidget(self.groupBox_9, 0, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_11.addItem(self.verticalSpacer_3, 3, 0, 1, 1)

        self.groupBox_15 = QGroupBox(self.pg_common)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.gridLayout_24 = QGridLayout(self.groupBox_15)
        self.gridLayout_24.setObjectName(u"gridLayout_24")
        self.te_csv_nomatchpatterns = QPlainTextEdit(self.groupBox_15)
        self.te_csv_nomatchpatterns.setObjectName(u"te_csv_nomatchpatterns")

        self.gridLayout_24.addWidget(self.te_csv_nomatchpatterns, 1, 0, 1, 1)

        self.label_24 = QLabel(self.groupBox_15)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout_24.addWidget(self.label_24, 0, 0, 1, 1)


        self.gridLayout_11.addWidget(self.groupBox_15, 1, 0, 1, 1)

        self.stw.addWidget(self.pg_common)
        self.pg_appear = QWidget()
        self.pg_appear.setObjectName(u"pg_appear")
        self.gridLayout_2 = QGridLayout(self.pg_appear)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.groupBox = QGroupBox(self.pg_appear)
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


        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 2)

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


        self.gridLayout_2.addWidget(self.groupBox_3, 2, 0, 1, 1)

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


        self.gridLayout_2.addWidget(self.groupBox_4, 2, 1, 1, 1)

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


        self.gridLayout_2.addWidget(self.groupBox_5, 3, 0, 1, 1)

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


        self.gridLayout_2.addWidget(self.groupBox_6, 3, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.groupBox_8 = QGroupBox(self.pg_appear)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.gridLayout_12 = QGridLayout(self.groupBox_8)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.chb_verticalgrid = QCheckBox(self.groupBox_8)
        self.chb_verticalgrid.setObjectName(u"chb_verticalgrid")

        self.gridLayout_12.addWidget(self.chb_verticalgrid, 0, 0, 1, 1)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_12.addItem(self.horizontalSpacer_15, 0, 1, 1, 1)

        self.pb_format_reset = QPushButton(self.groupBox_8)
        self.pb_format_reset.setObjectName(u"pb_format_reset")

        self.gridLayout_12.addWidget(self.pb_format_reset, 0, 2, 1, 1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_28 = QLabel(self.groupBox_8)
        self.label_28.setObjectName(u"label_28")

        self.horizontalLayout_12.addWidget(self.label_28)

        self.la_preview_due = QLabel(self.groupBox_8)
        self.la_preview_due.setObjectName(u"la_preview_due")

        self.horizontalLayout_12.addWidget(self.la_preview_due)

        self.la_preview_today = QLabel(self.groupBox_8)
        self.la_preview_today.setObjectName(u"la_preview_today")

        self.horizontalLayout_12.addWidget(self.la_preview_today)

        self.la_preview_header = QLabel(self.groupBox_8)
        self.la_preview_header.setObjectName(u"la_preview_header")

        self.horizontalLayout_12.addWidget(self.la_preview_header)

        self.la_preview_footer = QLabel(self.groupBox_8)
        self.la_preview_footer.setObjectName(u"la_preview_footer")

        self.horizontalLayout_12.addWidget(self.la_preview_footer)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_16)


        self.gridLayout_12.addLayout(self.horizontalLayout_12, 1, 0, 1, 3)


        self.gridLayout_2.addWidget(self.groupBox_8, 1, 0, 1, 2)

        self.stw.addWidget(self.pg_appear)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.gridLayout_20 = QGridLayout(self.page_2)
        self.gridLayout_20.setObjectName(u"gridLayout_20")
        self.gridLayout_21 = QGridLayout()
        self.gridLayout_21.setObjectName(u"gridLayout_21")
        self.label_27 = QLabel(self.page_2)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)
        self.label_27.setWordWrap(True)

        self.gridLayout_21.addWidget(self.label_27, 0, 3, 1, 1)

        self.label_25 = QLabel(self.page_2)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)
        self.label_25.setWordWrap(True)

        self.gridLayout_21.addWidget(self.label_25, 0, 2, 1, 1)

        self.label_26 = QLabel(self.page_2)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)

        self.gridLayout_21.addWidget(self.label_26, 0, 1, 1, 1)

        self.lw_calender_worknonbankdays = QListWidget(self.page_2)
        self.lw_calender_worknonbankdays.setObjectName(u"lw_calender_worknonbankdays")

        self.gridLayout_21.addWidget(self.lw_calender_worknonbankdays, 1, 3, 1, 1)

        self.lw_calender_workbankdays = QListWidget(self.page_2)
        self.lw_calender_workbankdays.setObjectName(u"lw_calender_workbankdays")

        self.gridLayout_21.addWidget(self.lw_calender_workbankdays, 1, 2, 1, 1)

        self.lw_calender_weekdays = QListWidget(self.page_2)
        self.lw_calender_weekdays.setObjectName(u"lw_calender_weekdays")

        self.gridLayout_21.addWidget(self.lw_calender_weekdays, 1, 1, 1, 1)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_10)

        self.pb_calender_remove_week = QPushButton(self.page_2)
        self.pb_calender_remove_week.setObjectName(u"pb_calender_remove_week")
        self.pb_calender_remove_week.setMaximumSize(QSize(30, 30))
        icon = QIcon()
        icon.addFile(u":/designer/icons/remove.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_calender_remove_week.setIcon(icon)

        self.horizontalLayout_9.addWidget(self.pb_calender_remove_week)

        self.pb_calender_add_week = QPushButton(self.page_2)
        self.pb_calender_add_week.setObjectName(u"pb_calender_add_week")
        self.pb_calender_add_week.setMaximumSize(QSize(30, 30))
        icon1 = QIcon()
        icon1.addFile(u":/designer/icons/add.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_calender_add_week.setIcon(icon1)

        self.horizontalLayout_9.addWidget(self.pb_calender_add_week)


        self.gridLayout_21.addLayout(self.horizontalLayout_9, 2, 1, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_11)

        self.pb_calender_remove_workbank = QPushButton(self.page_2)
        self.pb_calender_remove_workbank.setObjectName(u"pb_calender_remove_workbank")
        self.pb_calender_remove_workbank.setMaximumSize(QSize(30, 30))
        self.pb_calender_remove_workbank.setIcon(icon)

        self.horizontalLayout_10.addWidget(self.pb_calender_remove_workbank)

        self.pb_calender_add_workbank = QPushButton(self.page_2)
        self.pb_calender_add_workbank.setObjectName(u"pb_calender_add_workbank")
        self.pb_calender_add_workbank.setMaximumSize(QSize(30, 30))
        self.pb_calender_add_workbank.setIcon(icon1)

        self.horizontalLayout_10.addWidget(self.pb_calender_add_workbank)


        self.gridLayout_21.addLayout(self.horizontalLayout_10, 2, 2, 1, 1)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_12)

        self.pb_calender_remove_worknobank = QPushButton(self.page_2)
        self.pb_calender_remove_worknobank.setObjectName(u"pb_calender_remove_worknobank")
        self.pb_calender_remove_worknobank.setMaximumSize(QSize(30, 30))
        self.pb_calender_remove_worknobank.setIcon(icon)

        self.horizontalLayout_11.addWidget(self.pb_calender_remove_worknobank)

        self.pb_calender_add_worknobank = QPushButton(self.page_2)
        self.pb_calender_add_worknobank.setObjectName(u"pb_calender_add_worknobank")
        self.pb_calender_add_worknobank.setMaximumSize(QSize(30, 30))
        self.pb_calender_add_worknobank.setIcon(icon1)

        self.horizontalLayout_11.addWidget(self.pb_calender_add_worknobank)


        self.gridLayout_21.addLayout(self.horizontalLayout_11, 2, 3, 1, 1)


        self.gridLayout_20.addLayout(self.gridLayout_21, 5, 0, 1, 2)

        self.line = QFrame(self.page_2)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_20.addWidget(self.line, 3, 0, 1, 2)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_23 = QLabel(self.page_2)
        self.label_23.setObjectName(u"label_23")

        self.horizontalLayout_7.addWidget(self.label_23)

        self.horizontalSpacer_14 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_14)

        self.cmb_calender_year = QComboBox(self.page_2)
        self.cmb_calender_year.setObjectName(u"cmb_calender_year")

        self.horizontalLayout_7.addWidget(self.cmb_calender_year)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_13)


        self.gridLayout_20.addLayout(self.horizontalLayout_7, 1, 0, 1, 2)

        self.verticalSpacer_8 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_20.addItem(self.verticalSpacer_8, 2, 0, 1, 1)

        self.stw.addWidget(self.page_2)
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

        self.chb_dataintable_descr = QCheckBox(self.groupBox_2)
        self.chb_dataintable_descr.setObjectName(u"chb_dataintable_descr")
        self.chb_dataintable_descr.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_descr, 2, 0, 1, 1)

        self.chb_dataintable_responsible = QCheckBox(self.groupBox_2)
        self.chb_dataintable_responsible.setObjectName(u"chb_dataintable_responsible")
        self.chb_dataintable_responsible.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_responsible, 2, 1, 1, 1)

        self.chb_dataintable_paymenttype = QCheckBox(self.groupBox_2)
        self.chb_dataintable_paymenttype.setObjectName(u"chb_dataintable_paymenttype")
        self.chb_dataintable_paymenttype.setChecked(True)

        self.gridLayout_5.addWidget(self.chb_dataintable_paymenttype, 3, 0, 1, 1)

        self.chb_dataintable_createdate = QCheckBox(self.groupBox_2)
        self.chb_dataintable_createdate.setObjectName(u"chb_dataintable_createdate")

        self.gridLayout_5.addWidget(self.chb_dataintable_createdate, 0, 1, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_2, 0, 0, 1, 1)

        self.groupBox_11 = QGroupBox(self.pg_storage)
        self.groupBox_11.setObjectName(u"groupBox_11")
        self.gridLayout_16 = QGridLayout(self.groupBox_11)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.gridLayout_16.setVerticalSpacing(2)
        self.cmb_loadpaid = QComboBox(self.groupBox_11)
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.addItem("")
        self.cmb_loadpaid.setObjectName(u"cmb_loadpaid")

        self.gridLayout_16.addWidget(self.cmb_loadpaid, 0, 1, 1, 1)

        self.label_14 = QLabel(self.groupBox_11)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_16.addWidget(self.label_14, 0, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_16.addItem(self.horizontalSpacer_3, 0, 3, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_11, 1, 0, 1, 1)

        self.groupBox_10 = QGroupBox(self.pg_storage)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.gridLayout_14 = QGridLayout(self.groupBox_10)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.chb_frozenheader = QCheckBox(self.groupBox_10)
        self.chb_frozenheader.setObjectName(u"chb_frozenheader")

        self.gridLayout_14.addWidget(self.chb_frozenheader, 0, 0, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_10, 2, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer_2, 3, 0, 1, 1)

        self.stw.addWidget(self.pg_storage)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.gridLayout_18 = QGridLayout(self.page)
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.tw_personal = QTabWidget(self.page)
        self.tw_personal.setObjectName(u"tw_personal")
        self.tab_employees = QWidget()
        self.tab_employees.setObjectName(u"tab_employees")
        self.gridLayout_26 = QGridLayout(self.tab_employees)
        self.gridLayout_26.setObjectName(u"gridLayout_26")
        self.pb_pers_current = QPushButton(self.tab_employees)
        self.pb_pers_current.setObjectName(u"pb_pers_current")
        self.pb_pers_current.setCheckable(True)
        self.pb_pers_current.setChecked(True)
        self.pb_pers_current.setAutoExclusive(True)

        self.gridLayout_26.addWidget(self.pb_pers_current, 0, 0, 1, 1)

        self.pb_pers_hist = QPushButton(self.tab_employees)
        self.pb_pers_hist.setObjectName(u"pb_pers_hist")
        self.pb_pers_hist.setCheckable(True)
        self.pb_pers_hist.setAutoExclusive(True)

        self.gridLayout_26.addWidget(self.pb_pers_hist, 0, 1, 1, 1)

        self.lv_personal = QListView(self.tab_employees)
        self.lv_personal.setObjectName(u"lv_personal")

        self.gridLayout_26.addWidget(self.lv_personal, 1, 0, 1, 2)

        self.gridLayout_19 = QGridLayout()
        self.gridLayout_19.setObjectName(u"gridLayout_19")
        self.label_21 = QLabel(self.tab_employees)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_19.addWidget(self.label_21, 0, 0, 1, 1)

        self.pb_pers_add = QPushButton(self.tab_employees)
        self.pb_pers_add.setObjectName(u"pb_pers_add")

        self.gridLayout_19.addWidget(self.pb_pers_add, 6, 0, 1, 1)

        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_19.addItem(self.verticalSpacer_6, 3, 0, 1, 1)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_19.addItem(self.horizontalSpacer_7, 4, 1, 1, 1)

        self.pb_pers_rename = QPushButton(self.tab_employees)
        self.pb_pers_rename.setObjectName(u"pb_pers_rename")
        self.pb_pers_rename.setEnabled(False)

        self.gridLayout_19.addWidget(self.pb_pers_rename, 5, 0, 1, 1)

        self.cmb_pers_dept = QComboBox(self.tab_employees)
        self.cmb_pers_dept.setObjectName(u"cmb_pers_dept")
        self.cmb_pers_dept.setEnabled(False)
        self.cmb_pers_dept.setMinimumSize(QSize(200, 0))

        self.gridLayout_19.addWidget(self.cmb_pers_dept, 1, 0, 1, 2)

        self.pb_pers_changetype = QPushButton(self.tab_employees)
        self.pb_pers_changetype.setObjectName(u"pb_pers_changetype")
        self.pb_pers_changetype.setEnabled(False)

        self.gridLayout_19.addWidget(self.pb_pers_changetype, 4, 0, 1, 1)

        self.cmb_pers_position = QComboBox(self.tab_employees)
        self.cmb_pers_position.setObjectName(u"cmb_pers_position")
        self.cmb_pers_position.setEnabled(False)

        self.gridLayout_19.addWidget(self.cmb_pers_position, 2, 0, 1, 2)


        self.gridLayout_26.addLayout(self.gridLayout_19, 1, 2, 1, 1)

        self.tw_personal.addTab(self.tab_employees, "")
        self.tab_positions = QWidget()
        self.tab_positions.setObjectName(u"tab_positions")
        self.gridLayout_22 = QGridLayout(self.tab_positions)
        self.gridLayout_22.setObjectName(u"gridLayout_22")
        self.groupBox_14 = QGroupBox(self.tab_positions)
        self.groupBox_14.setObjectName(u"groupBox_14")
        self.gridLayout_23 = QGridLayout(self.groupBox_14)
        self.gridLayout_23.setObjectName(u"gridLayout_23")
        self.lw_positions = QListWidget(self.groupBox_14)
        self.lw_positions.setObjectName(u"lw_positions")

        self.gridLayout_23.addWidget(self.lw_positions, 1, 0, 3, 1)

        self.pb_position_add = QPushButton(self.groupBox_14)
        self.pb_position_add.setObjectName(u"pb_position_add")

        self.gridLayout_23.addWidget(self.pb_position_add, 3, 1, 1, 1)

        self.pb_position_remove = QPushButton(self.groupBox_14)
        self.pb_position_remove.setObjectName(u"pb_position_remove")
        self.pb_position_remove.setEnabled(False)

        self.gridLayout_23.addWidget(self.pb_position_remove, 1, 1, 1, 1)

        self.pb_position_rename = QPushButton(self.groupBox_14)
        self.pb_position_rename.setObjectName(u"pb_position_rename")
        self.pb_position_rename.setEnabled(False)

        self.gridLayout_23.addWidget(self.pb_position_rename, 2, 1, 1, 1)

        self.cmb_positions_department = QComboBox(self.groupBox_14)
        self.cmb_positions_department.setObjectName(u"cmb_positions_department")

        self.gridLayout_23.addWidget(self.cmb_positions_department, 0, 0, 1, 1)

        self.la_positions_note = QLabel(self.groupBox_14)
        self.la_positions_note.setObjectName(u"la_positions_note")
        self.la_positions_note.setEnabled(False)
        self.la_positions_note.setWordWrap(True)

        self.gridLayout_23.addWidget(self.la_positions_note, 4, 0, 1, 2)


        self.gridLayout_22.addWidget(self.groupBox_14, 0, 0, 1, 1)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_22.addItem(self.verticalSpacer_9, 1, 0, 1, 1)

        self.tw_personal.addTab(self.tab_positions, "")

        self.gridLayout_18.addWidget(self.tw_personal, 0, 0, 1, 1)

        self.stw.addWidget(self.page)
        self.pg_other = QWidget()
        self.pg_other.setObjectName(u"pg_other")
        self.gridLayout_15 = QGridLayout(self.pg_other)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_15.addItem(self.verticalSpacer_4, 2, 0, 1, 1)

        self.groupBox_13 = QGroupBox(self.pg_other)
        self.groupBox_13.setObjectName(u"groupBox_13")
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_13)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pb_restorefrombackup = QPushButton(self.groupBox_13)
        self.pb_restorefrombackup.setObjectName(u"pb_restorefrombackup")

        self.horizontalLayout_4.addWidget(self.pb_restorefrombackup)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.gridLayout_15.addWidget(self.groupBox_13, 1, 0, 1, 1)

        self.groupBox_12 = QGroupBox(self.pg_other)
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
        self.cmb_backupautodelete.setObjectName(u"cmb_backupautodelete")
        self.cmb_backupautodelete.setMinimumSize(QSize(90, 0))
        self.cmb_backupautodelete.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout_3.addWidget(self.cmb_backupautodelete)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.gridLayout_17.addLayout(self.horizontalLayout_3, 2, 0, 1, 3)

        self.le_backuppath = QLineEdit(self.groupBox_12)
        self.le_backuppath.setObjectName(u"le_backuppath")
        self.le_backuppath.setReadOnly(True)

        self.gridLayout_17.addWidget(self.le_backuppath, 1, 0, 1, 2)

        self.pb_backuppath = QPushButton(self.groupBox_12)
        self.pb_backuppath.setObjectName(u"pb_backuppath")

        self.gridLayout_17.addWidget(self.pb_backuppath, 1, 2, 1, 1)


        self.gridLayout_15.addWidget(self.groupBox_12, 0, 0, 1, 1)

        self.stw.addWidget(self.pg_other)
        self.pg_build = QWidget()
        self.pg_build.setObjectName(u"pg_build")
        self.gridLayout_25 = QGridLayout(self.pg_build)
        self.gridLayout_25.setObjectName(u"gridLayout_25")
        self.groupBox_16 = QGroupBox(self.pg_build)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.horizontalLayout_about = QHBoxLayout(self.groupBox_16)
        self.horizontalLayout_about.setSpacing(16)
        self.horizontalLayout_about.setObjectName(u"horizontalLayout_about")
        self.horizontalLayout_about.setContentsMargins(12, 12, 12, 12)
        self.la_appicon = QLabel(self.groupBox_16)
        self.la_appicon.setObjectName(u"la_appicon")
        self.la_appicon.setMinimumSize(QSize(64, 64))
        self.la_appicon.setMaximumSize(QSize(64, 64))
        self.la_appicon.setPixmap(QPixmap(u":/icon-app/designer/icons/app.png"))
        self.la_appicon.setScaledContents(True)

        self.horizontalLayout_about.addWidget(self.la_appicon)

        self.gridLayout_10 = QGridLayout()
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setVerticalSpacing(0)
        self.la_appdescr = QLabel(self.groupBox_16)
        self.la_appdescr.setObjectName(u"la_appdescr")
        self.la_appdescr.setStyleSheet(u"color: #808080;")

        self.gridLayout_10.addWidget(self.la_appdescr, 1, 0, 1, 2)

        self.la_buildnumber = QLabel(self.groupBox_16)
        self.la_buildnumber.setObjectName(u"la_buildnumber")
        self.la_buildnumber.setStyleSheet(u"background-color: #e8f0f8; color: #2c5c8a; border: 1px solid #c5d6e8; border-radius: 10px; padding: 2px 10px; font-weight: 600;")
        self.la_buildnumber.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.gridLayout_10.addWidget(self.la_buildnumber, 3, 0, 1, 1)

        self.la_dbnumber = QLabel(self.groupBox_16)
        self.la_dbnumber.setObjectName(u"la_dbnumber")
        self.la_dbnumber.setStyleSheet(u"background-color: #e8f0f8; color: #2c5c8a; border: 1px solid #c5d6e8; border-radius: 10px; padding: 2px 10px; font-weight: 600;")
        self.la_dbnumber.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.gridLayout_10.addWidget(self.la_dbnumber, 3, 1, 1, 1)

        self.la_appname = QLabel(self.groupBox_16)
        self.la_appname.setObjectName(u"la_appname")
        self.la_appname.setStyleSheet(u"font-size: 14pt; font-weight: 700; color: #2c5c8a;")
        self.la_appname.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft)

        self.gridLayout_10.addWidget(self.la_appname, 0, 0, 1, 2)

        self.verticalSpacer_5 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_10.addItem(self.verticalSpacer_5, 2, 0, 1, 1)


        self.horizontalLayout_about.addLayout(self.gridLayout_10)

        self.horizontalSpacer_about = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_about.addItem(self.horizontalSpacer_about)


        self.gridLayout_25.addWidget(self.groupBox_16, 0, 0, 1, 1)

        self.gb_updates = QGroupBox(self.pg_build)
        self.gb_updates.setObjectName(u"gb_updates")
        self.horizontalLayout_updates = QHBoxLayout(self.gb_updates)
        self.horizontalLayout_updates.setObjectName(u"horizontalLayout_updates")
        self.la_updatestatus = QLabel(self.gb_updates)
        self.la_updatestatus.setObjectName(u"la_updatestatus")
        self.la_updatestatus.setWordWrap(True)

        self.horizontalLayout_updates.addWidget(self.la_updatestatus)

        self.horizontalSpacer_17 = QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_updates.addItem(self.horizontalSpacer_17)

        self.pb_checkupdates = QPushButton(self.gb_updates)
        self.pb_checkupdates.setObjectName(u"pb_checkupdates")

        self.horizontalLayout_updates.addWidget(self.pb_checkupdates)


        self.gridLayout_25.addWidget(self.gb_updates, 1, 0, 1, 1)

        self.gb_hotkeys = QGroupBox(self.pg_build)
        self.gb_hotkeys.setObjectName(u"gb_hotkeys")
        self.verticalLayout_hotkeys = QVBoxLayout(self.gb_hotkeys)
        self.verticalLayout_hotkeys.setObjectName(u"verticalLayout_hotkeys")
        self.la_hotkeys = QLabel(self.gb_hotkeys)
        self.la_hotkeys.setObjectName(u"la_hotkeys")
        self.la_hotkeys.setTextFormat(Qt.TextFormat.RichText)
        self.la_hotkeys.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_hotkeys.addWidget(self.la_hotkeys)


        self.gridLayout_25.addWidget(self.gb_hotkeys, 2, 0, 1, 1)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_25.addItem(self.verticalSpacer_10, 3, 0, 1, 1)

        self.stw.addWidget(self.pg_build)
        self.pg_misc = QWidget()
        self.pg_misc.setObjectName(u"pg_misc")
        self.stw.addWidget(self.pg_misc)

        self.gridLayout.addWidget(self.stw, 0, 1, 1, 1)

        self.lw_menu = QListWidget(settingsdialog)
        icon2 = QIcon()
        icon2.addFile(u":/icon-settings/designer/icons/appearance.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u":/icon-settings/designer/icons/table.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem1.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem1.setIcon(icon3);
        icon4 = QIcon()
        icon4.addFile(u":/designer/icons/calendar.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem2.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem2.setIcon(icon4);
        icon5 = QIcon()
        icon5.addFile(u":/designer/icons/csvparser.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem3.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem3.setIcon(icon5);
        icon6 = QIcon()
        icon6.addFile(u":/icon-settings/designer/icons/set_pers.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem4 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem4.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem4.setIcon(icon6);
        icon7 = QIcon()
        icon7.addFile(u":/icon-settings/designer/icons/storage.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem5 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem5.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem5.setIcon(icon7);
        icon8 = QIcon()
        icon8.addFile(u":/icon-settings/designer/icons/info.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem6 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem6.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem6.setIcon(icon8);
        icon9 = QIcon()
        icon9.addFile(u":/icon-settings/designer/icons/generalsettings.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem7 = QListWidgetItem(self.lw_menu)
        __qlistwidgetitem7.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem7.setIcon(icon9);
        self.lw_menu.setObjectName(u"lw_menu")
        self.lw_menu.setMinimumSize(QSize(170, 0))
        self.lw_menu.setMaximumSize(QSize(170, 16777215))
        self.lw_menu.setSupportedDragActions(Qt.DropAction.IgnoreAction)

        self.gridLayout.addWidget(self.lw_menu, 0, 0, 1, 1)


        self.retranslateUi(settingsdialog)

        self.stw.setCurrentIndex(6)
        self.tw_personal.setCurrentIndex(0)
        self.lw_menu.setCurrentRow(-1)


        QMetaObject.connectSlotsByName(settingsdialog)
    # setupUi

    def retranslateUi(self, settingsdialog):
        settingsdialog.setWindowTitle(QCoreApplication.translate("settingsdialog", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", None))
        self.pb_cancel.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.pb_ok.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u041a", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u0440\u0441\u0435\u0440 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0439", None))
        self.label_16.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0437\u0430 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438:", None))
        self.label_20.setText(QCoreApplication.translate("settingsdialog", u"\u0423\u041d\u041f \u0431\u0430\u043d\u043a\u043e\u0432:", None))
        self.label_19.setText(QCoreApplication.translate("settingsdialog", u"\u0421\u0442\u043e\u043b\u0431\u0446\u044b (\u0434\u0430\u0442\u0430, \u043a\u043e\u0434, \u0423\u041d\u041f, \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435, \u0441\u0443\u043c\u043c\u0430, \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435, \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c):", None))
        self.le_csv_columns.setInputMask(QCoreApplication.translate("settingsdialog", u"9,9,9,9,9,9,9", None))
        self.label_15.setText(QCoreApplication.translate("settingsdialog", u"\u041d\u043e\u043c\u0435\u0440 \u0441\u0442\u0440\u043e\u043a\u0438 \u0441 \u043f\u0435\u0440\u0432\u043e\u0439 \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0435\u0439:", None))
        self.label_2.setText(QCoreApplication.translate("settingsdialog", u"\u041d\u043e\u043c\u0435\u0440 \u0441\u0442\u0440\u043e\u043a\u0438 \u0441 \u0443\u043a\u0430\u0437\u0430\u043d\u0438\u0435\u043c \u043f\u0435\u0440\u0438\u043e\u0434\u0430:", None))
        self.label_22.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043f\u0430\u0442\u0442\u0435\u0440\u043d\u044b:", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u0440\u0441\u0435\u0440 \u043c\u043e\u0434\u0443\u043b\u044f \u0441\u0432\u0435\u0440\u043a\u0438", None))
        self.label_24.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0441\u043a\u043b\u044e\u0447\u0430\u044e\u0449\u0438\u0435 \u043f\u0430\u0442\u0442\u0435\u0440\u043d\u044b \u0434\u043b\u044f \u0432\u044b\u043f\u0438\u0441\u043a\u0438:", None))
        self.groupBox.setTitle(QCoreApplication.translate("settingsdialog", u"\u0420\u0430\u0437\u043c\u0435\u0440 \u0448\u0440\u0438\u0444\u0442\u0430", None))
        self.rb_fontsize_1.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u044b\u0447\u043d\u044b\u0439", None))
        self.rb_fontsize_2.setText(QCoreApplication.translate("settingsdialog", u"\u0411\u043e\u043b\u044c\u0448\u043e\u0439", None))
        self.rb_fontsize_3.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0433\u0440\u043e\u043c\u043d\u044b\u0439", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.label.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 ", None))
        self.pb_backgrounddue.setText("")
        self.pb_foregrounddue.setText("")
        self.chb_formatbolddue.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_4.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430 ", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442: \u0441\u0435\u0433\u043e\u0434\u043d\u044f\u0448\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.pb_backgroundtoday.setText("")
        self.chb_formatboldtoday.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u044b\u0434\u0435\u043b\u0438\u0442\u044c \u0436\u0438\u0440\u043d\u044b\u043c", None))
        self.label_3.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0437\u0430\u043b\u0438\u0432\u043a\u0438 ", None))
        self.pb_foregroundtoday.setText("")
        self.label_5.setText(QCoreApplication.translate("settingsdialog", u"\u0426\u0432\u0435\u0442 \u0442\u0435\u043a\u0441\u0442\u0430", None))
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
        self.groupBox_8.setTitle(QCoreApplication.translate("settingsdialog", u"\u0424\u043e\u0440\u043c\u0430\u0442 \u0441\u0442\u0440\u043e\u043a", None))
        self.chb_verticalgrid.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u0435\u0440\u0442\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0435 \u0433\u0440\u0430\u043d\u0438\u0446\u044b", None))
        self.pb_format_reset.setText(QCoreApplication.translate("settingsdialog", u"\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0444\u043e\u0440\u043c\u0430\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.label_28.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0440\u0438\u043c\u0435\u0440:", None))
        self.la_preview_due.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0439", None))
        self.la_preview_today.setText(QCoreApplication.translate("settingsdialog", u"\u0421\u0435\u0433\u043e\u0434\u043d\u044f\u0448\u043d\u0438\u0439", None))
        self.la_preview_header.setText(QCoreApplication.translate("settingsdialog", u"\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a", None))
        self.la_preview_footer.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0442\u043e\u0433", None))
        self.label_27.setText(QCoreApplication.translate("settingsdialog", u"\u0420\u0430\u0431\u043e\u0447\u0438\u0435 \u043d\u0435\u0431\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0435", None))
        self.label_25.setText(QCoreApplication.translate("settingsdialog", u"\u0420\u0430\u0431\u043e\u0447\u0438\u0435 \u0431\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0435", None))
        self.label_26.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0440\u0430\u0437\u0434\u043d\u0438\u0447\u043d\u044b\u0435", None))
        self.pb_calender_remove_week.setText("")
        self.pb_calender_add_week.setText("")
        self.pb_calender_remove_workbank.setText("")
        self.pb_calender_add_workbank.setText("")
        self.pb_calender_remove_worknobank.setText("")
        self.pb_calender_add_worknobank.setText("")
        self.label_23.setText(QCoreApplication.translate("settingsdialog", u"\u0413\u043e\u0434:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("settingsdialog", u"\u0414\u0430\u043d\u043d\u044b\u0435 \u0432 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u0435", None))
        self.chb_dataintable_totalamount.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_dataintable_descr.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_dataintable_responsible.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0435 \u043b\u0438\u0446\u043e", None))
        self.chb_dataintable_paymenttype.setText(QCoreApplication.translate("settingsdialog", u"\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
        self.chb_dataintable_createdate.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u0430\u0442\u0430 \u043f\u043e\u044f\u0432\u043b\u0435\u043d\u0438\u044f", None))
        self.groupBox_11.setTitle(QCoreApplication.translate("settingsdialog", u"\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", None))
        self.cmb_loadpaid.setItemText(0, QCoreApplication.translate("settingsdialog", u"\u0442\u0440\u0438 \u043c\u0435\u0441\u044f\u0446\u0430", None))
        self.cmb_loadpaid.setItemText(1, QCoreApplication.translate("settingsdialog", u"\u043f\u043e\u043b\u0433\u043e\u0434\u0430", None))
        self.cmb_loadpaid.setItemText(2, QCoreApplication.translate("settingsdialog", u"\u043e\u0434\u0438\u043d \u0433\u043e\u0434", None))
        self.cmb_loadpaid.setItemText(3, QCoreApplication.translate("settingsdialog", u"\u0432\u0441\u0435 \u0432\u0440\u0435\u043c\u044f", None))

#if QT_CONFIG(tooltip)
        self.cmb_loadpaid.setToolTip(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0441\u0447\u0435\u0442 \u0432\u0435\u0434\u0435\u0442\u0441\u044f \u0441 \u0434\u0430\u0442\u044b \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_14.setToolTip(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u0441\u0447\u0435\u0442 \u0432\u0435\u0434\u0435\u0442\u0441\u044f \u0441 \u0434\u0430\u0442\u044b \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u043f\u043b\u0430\u0442\u0435\u0436\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.label_14.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u0442\u044c \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438 \u0437\u0430  ", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("settingsdialog", u"\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0442\u0430\u0431\u043b\u0438\u0446\u044b", None))
        self.chb_frozenheader.setText(QCoreApplication.translate("settingsdialog", u"\u0417\u0430\u043a\u0440\u0435\u043f\u043b\u044f\u0442\u044c \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u0447\u043d\u0443\u044e \u0447\u0430\u0441\u0442\u044c \u0432 XLSX-\u0444\u0430\u0439\u043b\u0435", None))
        self.pb_pers_current.setText(QCoreApplication.translate("settingsdialog", u"\u0422\u0435\u043a\u0443\u0449\u0438\u0435", None))
        self.pb_pers_hist.setText(QCoreApplication.translate("settingsdialog", u"\u0410\u0440\u0445\u0438\u0432", None))
        self.label_21.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u0435: ", None))
        self.pb_pers_add.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", None))
        self.pb_pers_rename.setText(QCoreApplication.translate("settingsdialog", u" \u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u0442\u044c ", None))
        self.pb_pers_changetype.setText(QCoreApplication.translate("settingsdialog", u"\u0412 \u0430\u0440\u0445\u0438\u0432", None))
        self.tw_personal.setTabText(self.tw_personal.indexOf(self.tab_employees), QCoreApplication.translate("settingsdialog", u"\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438", None))
        self.groupBox_14.setTitle(QCoreApplication.translate("settingsdialog", u"\u041f\u0435\u0440\u0435\u0447\u0435\u043d\u044c \u0434\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0435\u0439", None))
        self.pb_position_add.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", None))
        self.pb_position_remove.setText(QCoreApplication.translate("settingsdialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
        self.pb_position_rename.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u0442\u044c", None))
        self.la_positions_note.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0432 \u043f\u0435\u0440\u0435\u0447\u043d\u0435 \u0434\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0435\u0439 \u0441\u043e\u0445\u0440\u0430\u043d\u044f\u044e\u0442\u0441\u044f \u0441\u0440\u0430\u0437\u0443", None))
        self.tw_personal.setTabText(self.tw_personal.indexOf(self.tab_positions), QCoreApplication.translate("settingsdialog", u"\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0438", None))
        self.groupBox_13.setTitle(QCoreApplication.translate("settingsdialog", u"\u0412\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435", None))
        self.pb_restorefrombackup.setText(QCoreApplication.translate("settingsdialog", u"  \u0412\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0438\u0437 \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0439 \u043a\u043e\u043f\u0438\u0438  ", None))
        self.groupBox_12.setTitle(QCoreApplication.translate("settingsdialog", u"\u0420\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0435 \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.label_17.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u043f\u043a\u0430 \u0434\u043b\u044f \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u043e\u0433\u043e \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f:", None))
        self.label_18.setText(QCoreApplication.translate("settingsdialog", u"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u0435 \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u044b\u0445 \u043a\u043e\u043f\u0438\u0439:", None))
        self.cmb_backupautodelete.setItemText(0, QCoreApplication.translate("settingsdialog", u"1 \u043c\u0435\u0441\u044f\u0446", None))
        self.cmb_backupautodelete.setItemText(1, QCoreApplication.translate("settingsdialog", u"6 \u043c\u0435\u0441\u044f\u0446\u0435\u0432", None))
        self.cmb_backupautodelete.setItemText(2, QCoreApplication.translate("settingsdialog", u"\u043d\u0438\u043a\u043e\u0433\u0434\u0430", None))

        self.pb_backuppath.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("settingsdialog", u"\u041e \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0435", None))
        self.la_appdescr.setText(QCoreApplication.translate("settingsdialog", u"\u0423\u0447\u0451\u0442 \u0438 \u043f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439", None))
        self.la_buildnumber.setText(QCoreApplication.translate("settingsdialog", u"<ver>", None))
        self.la_dbnumber.setText(QCoreApplication.translate("settingsdialog", u"<db ver>", None))
        self.la_appname.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u043b\u0430\u0442\u0435\u0436\u043d\u044b\u0439 \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c", None))
        self.gb_updates.setTitle(QCoreApplication.translate("settingsdialog", u"\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", None))
        self.la_updatestatus.setText(QCoreApplication.translate("settingsdialog", u"<status>", None))
        self.pb_checkupdates.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0441\u0435\u0439\u0447\u0430\u0441", None))
        self.gb_hotkeys.setTitle(QCoreApplication.translate("settingsdialog", u"\u0413\u043e\u0440\u044f\u0447\u0438\u0435 \u043a\u043b\u0430\u0432\u0438\u0448\u0438", None))

        __sortingEnabled = self.lw_menu.isSortingEnabled()
        self.lw_menu.setSortingEnabled(False)
        ___qlistwidgetitem = self.lw_menu.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("settingsdialog", u"\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435", None));
        ___qlistwidgetitem1 = self.lw_menu.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("settingsdialog", u"\u0422\u0430\u0431\u043b\u0438\u0446\u0430", None));
        ___qlistwidgetitem2 = self.lw_menu.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("settingsdialog", u"\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c", None));
        ___qlistwidgetitem3 = self.lw_menu.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0430\u0440\u0441\u0435\u0440 \u0432\u044b\u043f\u0438\u0441\u043a\u0438", None));
        ___qlistwidgetitem4 = self.lw_menu.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("settingsdialog", u"\u041f\u0435\u0440\u0441\u043e\u043d\u0430\u043b", None));
        ___qlistwidgetitem5 = self.lw_menu.item(5)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("settingsdialog", u"\u0425\u0440\u0430\u043d\u0435\u043d\u0438\u0435", None));
        ___qlistwidgetitem6 = self.lw_menu.item(6)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("settingsdialog", u"\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f", None));
        ___qlistwidgetitem7 = self.lw_menu.item(7)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("settingsdialog", u"\u0414\u0440\u0443\u0433\u043e\u0435", None));
        self.lw_menu.setSortingEnabled(__sortingEnabled)

    # retranslateUi

