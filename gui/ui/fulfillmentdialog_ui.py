# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fulfillmentdialog.ui'
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
    QHeaderView, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

from gui.fulfillmentwidget import FulfillmentWidget

class Ui_FulfillmentDialog(object):
    def setupUi(self, FulfillmentDialog):
        if not FulfillmentDialog.objectName():
            FulfillmentDialog.setObjectName(u"FulfillmentDialog")
        FulfillmentDialog.resize(1040, 629)
        self.gridLayout = QGridLayout(FulfillmentDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pb_exportxls = QPushButton(FulfillmentDialog)
        self.pb_exportxls.setObjectName(u"pb_exportxls")

        self.gridLayout.addWidget(self.pb_exportxls, 2, 2, 1, 1)

        self.tv_fulfillment = FulfillmentWidget(FulfillmentDialog)
        self.tv_fulfillment.setObjectName(u"tv_fulfillment")

        self.gridLayout.addWidget(self.tv_fulfillment, 0, 0, 1, 5)

        self.pb_close = QPushButton(FulfillmentDialog)
        self.pb_close.setObjectName(u"pb_close")

        self.gridLayout.addWidget(self.pb_close, 2, 4, 1, 1)

        self.cb_highlight = QCheckBox(FulfillmentDialog)
        self.cb_highlight.setObjectName(u"cb_highlight")
        self.cb_highlight.setChecked(True)

        self.gridLayout.addWidget(self.cb_highlight, 2, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 1, 1, 1)

        self.pb_exportpdf = QPushButton(FulfillmentDialog)
        self.pb_exportpdf.setObjectName(u"pb_exportpdf")

        self.gridLayout.addWidget(self.pb_exportpdf, 2, 3, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 3, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

        QWidget.setTabOrder(self.tv_fulfillment, self.cb_highlight)
        QWidget.setTabOrder(self.cb_highlight, self.pb_exportxls)
        QWidget.setTabOrder(self.pb_exportxls, self.pb_exportpdf)
        QWidget.setTabOrder(self.pb_exportpdf, self.pb_close)

        self.retranslateUi(FulfillmentDialog)

        self.pb_close.setDefault(True)


        QMetaObject.connectSlotsByName(FulfillmentDialog)
    # setupUi

    def retranslateUi(self, FulfillmentDialog):
        FulfillmentDialog.setWindowTitle(QCoreApplication.translate("FulfillmentDialog", u"\u0418\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0433\u043e \u043f\u043b\u0430\u043d\u0430", None))
        self.pb_exportxls.setText(QCoreApplication.translate("FulfillmentDialog", u" \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 XLS ", None))
        self.pb_close.setText(QCoreApplication.translate("FulfillmentDialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
#if QT_CONFIG(tooltip)
        self.cb_highlight.setToolTip(QCoreApplication.translate("FulfillmentDialog", u"\u0412\u044b\u0434\u0435\u043b\u044f\u0442\u044c \u0441\u0442\u0440\u043e\u043a\u0438, \u0433\u0434\u0435 \u0444\u0430\u043a\u0442 \u043f\u0440\u0435\u0432\u044b\u0448\u0430\u0435\u0442 \u043f\u043b\u0430\u043d \u0431\u043e\u043b\u0435\u0435 \u0447\u0435\u043c \u043d\u0430 10%: \u0440\u0430\u0441\u0445\u043e\u0434\u044b \u043a\u0440\u0430\u0441\u043d\u044b\u043c, \u043f\u043e\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u044f \u0437\u0435\u043b\u0451\u043d\u044b\u043c", None))
#endif // QT_CONFIG(tooltip)
        self.cb_highlight.setText(QCoreApplication.translate("FulfillmentDialog", u"\u041f\u043e\u0434\u0441\u0432\u0435\u0447\u0438\u0432\u0430\u0442\u044c \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u044f", None))
        self.pb_exportpdf.setText(QCoreApplication.translate("FulfillmentDialog", u" \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 PDF ", None))
    # retranslateUi

