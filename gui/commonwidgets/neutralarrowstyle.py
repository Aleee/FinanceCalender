from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QProxyStyle, QStyle, QStyleOption, QStyleOptionToolButton, QToolButton


class NeutralArrowStyle(QProxyStyle):
    NEUTRAL_ARROW_WIDGETS: tuple[str, ...] = ("tb_sync",)
    WIDE_ARROW_WIDTH: int = 22
    TOOLBAR_ARROW_WIDGETS: tuple[str, ...] = ("tb_dropdown",)
    TOOLBAR_ARROW_WIDTH: int = 16
    TOOLBAR_ARROW_MARGIN: int = 3
    ICON_ONLY_ARROW_WIDTH: int = 8
    ICON_ONLY_ARROW_MARGIN: int = -2

    def __init__(self):
        super().__init__("fusion")

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_DialogButtonLayout:
            return QDialogButtonBox.ButtonLayout.MacLayout.value
        return super().styleHint(hint, option, widget, returnData)

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QStyle.PixelMetric.PM_MenuButtonIndicator and widget is not None:
            if widget.objectName() in self.NEUTRAL_ARROW_WIDGETS:
                return self.WIDE_ARROW_WIDTH
            if widget.objectName() in self.TOOLBAR_ARROW_WIDGETS:
                if self.is_icon_only(widget):
                    return self.ICON_ONLY_ARROW_WIDTH
                return self.TOOLBAR_ARROW_WIDTH
        return super().pixelMetric(metric, option, widget)

    @staticmethod
    def is_icon_only(widget: QToolButton) -> bool:
        return isinstance(widget, QToolButton) and widget.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly

    def drawControl(self, element, option, painter, widget=None):
        if (element == QStyle.ControlElement.CE_ToolButtonLabel and isinstance(widget, QToolButton)
                and widget.objectName() in self.TOOLBAR_ARROW_WIDGETS
                and widget.popupMode() == QToolButton.ToolButtonPopupMode.InstantPopup
                and self.is_icon_only(widget)):
            option = QStyleOptionToolButton(option)
            option.rect = option.rect.adjusted(0, 0, -self.ICON_ONLY_ARROW_WIDTH, 0)
        super().drawControl(element, option, painter, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        if (element == QStyle.PrimitiveElement.PE_IndicatorArrowDown and isinstance(widget, QToolButton)
                and widget.objectName() in self.TOOLBAR_ARROW_WIDGETS
                and widget.popupMode() == QToolButton.ToolButtonPopupMode.InstantPopup):
            option = QStyleOption(option)
            arrow_width: int = self.TOOLBAR_ARROW_WIDTH
            arrow_height: int = option.rect.height()
            arrow_top: int = self.TOOLBAR_ARROW_MARGIN
            arrow_margin: int = self.TOOLBAR_ARROW_MARGIN
            if self.is_icon_only(widget):
                arrow_height = self.TOOLBAR_ARROW_WIDTH
                arrow_top = (widget.height() - arrow_height) // 2
                arrow_margin = self.ICON_ONLY_ARROW_MARGIN
            option.rect = QRect(widget.width() - arrow_width - arrow_margin,
                                arrow_top, arrow_width, arrow_height)
        if (element == QStyle.PrimitiveElement.PE_IndicatorArrowDown and widget is not None
                and widget.objectName() in self.NEUTRAL_ARROW_WIDGETS):
            option = QStyleOption(option)
            option.palette = QApplication.palette()
        super().drawPrimitive(element, option, painter, widget)
