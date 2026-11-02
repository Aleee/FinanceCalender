import os
import sys
from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import QDate

from base import paths
from base.date import date_str, str_date
from base.formatting import str_decimal


def test_date_str_qdate():
    assert date_str(QDate(2026, 10, 5)) == "2026-10-05"


def test_date_str_python_date():
    assert date_str(date(2026, 10, 5)) == "2026-10-05"


def test_date_str_invalid_qdate_is_empty():
    assert date_str(QDate()) == ""


@pytest.mark.parametrize("value", [None, "2026-10-05", 20261005])
def test_date_str_rejects_non_dates(value):
    with pytest.raises(TypeError):
        date_str(value)


def test_date_str_roundtrip():
    assert str_date(date_str(QDate(2026, 2, 28))) == QDate(2026, 2, 28)


@pytest.mark.parametrize("raw, expected", [
    ("1234.50", Decimal("1234.50")),
    ("1 234,50", Decimal("1234.50")),
    ("1 234,50", Decimal("1234.50")),
    ("1 234,50", Decimal("1234.50")),
    ("-20", Decimal("-20")),
    ("0", Decimal("0")),
])
def test_str_decimal_parses_numbers(raw, expected):
    assert str_decimal(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "12,5,5", "NaN", "nan", "Infinity", "-Infinity", "inf", None])
def test_str_decimal_rejects_non_numbers(raw):
    assert str_decimal(raw) is None


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
