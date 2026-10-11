from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle, QStyleOption, QToolButton


class NeutralArrowStyle(QProxyStyle):
    NEUTRAL_ARROW_WIDGETS: tuple[str, ...] = ("tb_sync",)
    WIDE_ARROW_WIDTH: int = 22
    TOOLBAR_ARROW_WIDGETS: tuple[str, ...] = ("tb_dropdown",)
    TOOLBAR_ARROW_WIDTH: int = 16
    TOOLBAR_ARROW_MARGIN: int = 3

    def __init__(self):
        super().__init__("fusion")

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PixelMetric.PM_MenuButtonIndicator and widget is not None:
            if widget.objectName() in self.NEUTRAL_ARROW_WIDGETS:
                return self.WIDE_ARROW_WIDTH
            if widget.objectName() in self.TOOLBAR_ARROW_WIDGETS:
                return self.TOOLBAR_ARROW_WIDTH
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        if (element == QStyle.PrimitiveElement.PE_IndicatorArrowDown and isinstance(widget, QToolButton)
                and widget.objectName() in self.TOOLBAR_ARROW_WIDGETS
                and widget.popupMode() == QToolButton.ToolButtonPopupMode.InstantPopup):
            option = QStyleOption(option)
            option.rect = QRect(widget.width() - option.rect.width() - self.TOOLBAR_ARROW_MARGIN,
                                self.TOOLBAR_ARROW_MARGIN, option.rect.width(), option.rect.height())
        if (element == QStyle.PrimitiveElement.PE_IndicatorArrowDown and widget is not None
                and widget.objectName() in self.NEUTRAL_ARROW_WIDGETS):
            option = QStyleOption(option)
            option.palette = QApplication.palette()
        super().drawPrimitive(element, option, painter, widget)
