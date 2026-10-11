import os
import sys

from base import paths


def test_data_dir_inside_app_dir_by_default():
    assert paths.data_dir() == os.path.join(paths.app_dir(), "data")


def test_data_dir_on_frozen_macos(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    expected = os.path.expanduser("~/Library/Application Support/FinanceCalender")
    assert paths.storage_dir() == expected
    assert paths.data_dir() == os.path.join(expected, "data")


def test_data_dir_on_frozen_windows(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    assert paths.storage_dir() == paths.app_dir()


def test_stored_path_relative_to_storage_dir(monkeypatch):
    monkeypatch.setattr(paths, "storage_dir", lambda: os.path.abspath("storage"))
    full = os.path.join(os.path.abspath("storage"), "data", "backup")
    stored = paths.to_stored_path(full)
    assert stored == os.path.join("data", "backup")
    assert paths.from_stored_path(stored) == full
