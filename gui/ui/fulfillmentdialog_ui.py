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
    QSizePolicy, QWidget)

from gui.fulfillmentwidget import FulfillmentWidget

class Ui_FulfillmentDialog(object):
    def setupUi(self, FulfillmentDialog):
        if not FulfillmentDialog.objectName():
            FulfillmentDialog.setObjectName(u"FulfillmentDialog")
        FulfillmentDialog.resize(1040, 638)
        self.gridLayout = QGridLayout(FulfillmentDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tv_fulfillment = FulfillmentWidget(FulfillmentDialog)
        self.tv_fulfillment.setObjectName(u"tv_fulfillment")

        self.gridLayout.addWidget(self.tv_fulfillment, 0, 0, 1, 1)


        self.retranslateUi(FulfillmentDialog)

        QMetaObject.connectSlotsByName(FulfillmentDialog)
    # setupUi

    def retranslateUi(self, FulfillmentDialog):
        FulfillmentDialog.setWindowTitle(QCoreApplication.translate("FulfillmentDialog", u"\u0418\u0441\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u0444\u0438\u043d\u0430\u043d\u0441\u043e\u0432\u043e\u0433\u043e \u043f\u043b\u0430\u043d\u0430", None))
    # retranslateUi

