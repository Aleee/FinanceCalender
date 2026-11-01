from gui.chart import MoneyAxis, WholeNumberAxis, chart_font


def test_axis_shortens_millions(qapp):
    axis = MoneyAxis(orientation="left")
    assert axis.tickStrings([0, 200000, 1400000, 1500000], 1, 1) == ["0", "0,2 млн", "1,4 млн", "1,5 млн"]
    assert WholeNumberAxis(orientation="left").tickStrings([0, 2000000], 1, 1) == ["0", "2 млн"]


def test_axis_keeps_full_numbers_below_million(qapp):
    assert MoneyAxis(orientation="left").tickStrings([0, 5000, 120000], 1, 1) == ["0", "5 000", "120 000"]


def test_chart_font_uses_application_family(qapp):
    from PySide6.QtWidgets import QApplication
    font = chart_font(10)
    assert font.family() == QApplication.font().family()
    assert font.pointSize() == 10
