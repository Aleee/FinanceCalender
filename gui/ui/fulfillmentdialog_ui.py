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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHeaderView,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)

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

        self.gridLayout.addWidget(self.pb_exportxls, 2, 1, 1, 1)

        self.tv_fulfillment = FulfillmentWidget(FulfillmentDialog)
        self.tv_fulfillment.setObjectName(u"tv_fulfillment")

        self.gridLayout.addWidget(self.tv_fulfillment, 0, 0, 1, 4)

        self.pb_close = QPushButton(FulfillmentDialog)
        self.pb_close.setObjectName(u"pb_close")

        self.gridLayout.addWidget(self.pb_close, 2, 3, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 0, 1, 1)

        self.pb_exportpdf = QPushButton(FulfillmentDialog)
        self.pb_exportpdf.setObjectName(u"pb_exportpdf")

        self.gridLayout.addWidget(self.pb_exportpdf, 2, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 3, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)


        self.retranslateUi(FulfillmentDialog)

        self.pb_close.setDefault(True)


        QMetaObject.connectSlotsByName(FulfillmentDialog)
    # setupUi

    def retranslateUi(self, FulfillmentDialog):
        FulfillmentDialog.setWindowTitle(QCoreApplication.translate("FulfillmentDialog", u"\u0418\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0433\u043e \u043f\u043b\u0430\u043d\u0430", None))
        self.pb_exportxls.setText(QCoreApplication.translate("FulfillmentDialog", u" \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 XLS ", None))
        self.pb_close.setText(QCoreApplication.translate("FulfillmentDialog", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
        self.pb_exportpdf.setText(QCoreApplication.translate("FulfillmentDialog", u" \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0432 PDF ", None))
    # retranslateUi

