from PySide6.QtCore import QDate, QDateTime


def get_current_date():
    return QDate.currentDate()


def get_date_diff(start_date, end_date) -> int:
    return start_date.daysTo(end_date)


def days_to_weekend(from_date) -> int:
    current_day_of_week: int = from_date.dayOfWeek()
    days_to_add: int = 0
    if current_day_of_week != 7:
        days_to_add = 7 - current_day_of_week
    week_end: QDate = from_date.addDays(days_to_add)
    return get_date_diff(from_date, week_end)


def days_to_month(from_date) -> int:
    days: int = from_date.daysInMonth()
    month_end: QDate = QDate(from_date.year(), from_date.month(), days)
    return get_date_diff(from_date, month_end)


def str_date(string) -> QDate:
    return QDate.fromString(string, "yyyy-MM-dd")


def date_str(date) -> str:
    return date.toString("yyyy-MM-dd")


def date_purestr(date) -> str:
    return date.toString("ddMMyyyy")


def date_displstr(date) -> str:
    return date.toString("dd.MM.yyyy")


def first_date_of_month(date) -> QDate:
    return QDate(date.year(), date.month(), 1)


def last_date_of_month(date) -> QDate:
    return QDate(date.year(), date.month(), date.daysInMonth())
