from decimal import Decimal

import pytest

from base.formatting import str_decimal


@pytest.mark.parametrize("raw, expected", [
    ("1234.50", Decimal("1234.50")),
    ("1234,50", Decimal("1234.50")),
    ("1 234,50", Decimal("1234.50")),
    ("-20", Decimal("-20")),
    ("0", Decimal("0")),
])
def test_str_decimal_parses_numbers(raw, expected):
    assert str_decimal(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "12,5,5", "NaN", "nan", "Infinity", "-Infinity", "inf", None])
def test_str_decimal_rejects_non_numbers(raw):
    assert str_decimal(raw) is None
