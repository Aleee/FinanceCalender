import sys

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QLineEdit, QWidget

from gui import shortcuts


def as_text(keys: list[QKeySequence]) -> list[str]:
    return [key.toString() for key in keys]


def test_windows_keys_and_texts_unchanged(qapp, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert as_text(shortcuts.delete_keys()) == ["Del"]
    assert as_text(shortcuts.help_keys()) == ["F1"]
    assert shortcuts.native_text("Удалить платеж (Del), Ctrl+N") == "Удалить платеж (Del), Ctrl+N"


def test_mac_adds_backspace_and_help_keys(qapp, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert as_text(shortcuts.delete_keys()) == ["Del", "Backspace"]
    assert len(shortcuts.help_keys()) == 2


def test_mac_hint_replaces_del_and_keeps_other_text(qapp, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert shortcuts.native_text("Удалить платеж (Del)") == "Удалить платеж (⌫)"
    assert shortcuts.native_text("Правка (F2 или двойной клик), Delete") == "Правка (F2 или двойной клик), Delete"


def test_mac_hint_matches_key_combinations(qapp, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    matches = [m.group() for m in shortcuts.SHORTCUT_IN_TEXT.finditer(
        "Новый (Ctrl+N), (Ctrl+Shift+K), (Ctrl+,), (Ctrl+←), Ctrl+Zoom")]
    assert matches == ["Ctrl+N", "Ctrl+Shift+K", "Ctrl+,", "Ctrl+←"]


def test_add_mac_keys_only_on_mac(qapp, monkeypatch):
    action = QAction()
    action.setShortcut(QKeySequence("F5"))
    monkeypatch.setattr(sys, "platform", "win32")
    shortcuts.add_mac_keys(action, "Ctrl+Shift+R")
    assert as_text(action.shortcuts()) == ["F5"]
    monkeypatch.setattr(sys, "platform", "darwin")
    shortcuts.add_mac_keys(action, "Ctrl+Shift+R")
    assert len(action.shortcuts()) == 2


def test_localize_hints_updates_tooltips_and_placeholders_on_mac(qapp, monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    root = QWidget()
    edit = QLineEdit(root)
    edit.setPlaceholderText("Поиск (Del)")
    action = QAction(root)
    action.setToolTip("Удалить (Del)")
    root.setToolTip("Окно (Del)")
    shortcuts.localize_shortcut_hints(root)
    assert edit.placeholderText() == "Поиск (⌫)"
    assert action.toolTip() == "Удалить (⌫)"
    assert root.toolTip() == "Окно (⌫)"
