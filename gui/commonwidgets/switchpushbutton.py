from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton


class SwitchPushButton(QPushButton):

    DEFAULT_STYLE: str = "border-width: 0px; text-align: left; color: black;"
    HIDDENFILTER_STYLE: str = "border-width: 0px; text-align: left; color: #ff3d3d;"
    switch_status_changed = Signal(bool)

    def __init__(self, parent=None):
        super(SwitchPushButton, self).__init__(parent)
        self.switchstate: bool = True
        self.label_off: str = ""
        self.label_on: str = ""

        self.clicked.connect(lambda: self.set_switch_state(not self.switchstate))

    def set_button_label(self, label_off: str, label_on: str) -> None:
        self.label_off = label_off
        self.label_on = label_on

    def switch_state(self) -> bool:
        return self.switchstate

    def set_switch_state(self, switch_state: bool) -> None:
        self.switchstate = switch_state
        self.setText(self.label_on if self.switchstate else self.label_off)
        self.switch_status_changed.emit(switch_state)

    def change_style_on_hiding_activefilter(self, switch_state: bool, filter_active: bool) -> None:
        if not switch_state and filter_active:
            self.setStyleSheet(self.HIDDENFILTER_STYLE)
        else:
            self.setStyleSheet(self.DEFAULT_STYLE)
