import re
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QLineEdit, QWidget

SHORTCUT_IN_TEXT = re.compile(r"(?:(?:Ctrl|Shift|Alt)\+)+(?:Left|Right|[A-Z,←→])(?!\w)|(?<!\w)Del(?!\w)")
ARROW_NAMES = {"←": "Left", "→": "Right"}


def is_mac() -> bool:
    return sys.platform == "darwin"


def delete_keys() -> list[QKeySequence]:
    keys = [QKeySequence(Qt.Key.Key_Delete)]
    if is_mac():
        keys.append(QKeySequence(Qt.Key.Key_Backspace))
    return keys


def help_keys() -> list[QKeySequence]:
    keys = [QKeySequence("F1")]
    if is_mac():
        keys.append(QKeySequence(QKeySequence.StandardKey.HelpContents))
    return keys


def add_mac_keys(action: QAction, *keys: str) -> None:
    if is_mac():
        action.setShortcuts([*action.shortcuts(), *(QKeySequence(key) for key in keys)])


def native_text(text: str) -> str:
    if not is_mac():
        return text

    def replace(match: re.Match) -> str:
        key = match.group()
        if key == "Del":
            return "⌫"
        for arrow, name in ARROW_NAMES.items():
            key = key.replace(arrow, name)
        return QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)

    return SHORTCUT_IN_TEXT.sub(replace, text)


def localize_shortcut_hints(root: QWidget) -> None:
    if not is_mac():
        return
    for widget in (root, *root.findChildren(QWidget)):
        widget.setToolTip(native_text(widget.toolTip()))
        if isinstance(widget, QLineEdit):
            widget.setPlaceholderText(native_text(widget.placeholderText()))
    for action in root.findChildren(QAction):
        action.setToolTip(native_text(action.toolTip()))
