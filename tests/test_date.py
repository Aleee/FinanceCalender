from datetime import date

import pytest
from PySide6.QtCore import QDate

from base.date import date_str, str_date


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
