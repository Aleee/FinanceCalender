from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractSpinBox, QCheckBox, QComboBox, QLineEdit, QPlainTextEdit, QRadioButton, QTextEdit,
                               QWidget)


def make_read_only(root: QWidget, keep: tuple[QWidget, ...] = ()) -> None:
    for widget in root.findChildren(QWidget):
        if widget in keep:
            continue
        if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)):
            widget.setReadOnly(True)
        elif isinstance(widget, QAbstractSpinBox):
            widget.setReadOnly(True)
            widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            block_input(widget)
        elif isinstance(widget, (QComboBox, QCheckBox, QRadioButton)):
            block_input(widget)


def block_input(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
