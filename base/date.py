from PySide6.QtCore import QDate, QDateTime


def get_current_date():
    return QDate.currentDate()


def get_date_diff(start_date, end_date):
    return start_date.daysTo(end_date)


def days_to_weekend(from_date):
    current_day_of_week = from_date.dayOfWeek()
    days_to_add = 0
    if current_day_of_week != 7:
        days_to_add = 7 - current_day_of_week
    week_end = from_date.addDays(days_to_add)
    return get_date_diff(from_date, week_end)


def days_to_month(from_date):
    days = from_date.daysInMonth()
    month_end = QDate(from_date.year(), from_date.month(), days)
    return get_date_diff(from_date, month_end)


def str_date(string):
    return QDate.fromString(string, "dd-MM-yyyy")


def date_str(date):
    return date.toString("dd-MM-yyyy")


def date_purestr(date):
    return date.toString("ddMMyyyy")


def date_displstr(date):
    return date.toString("dd.MM.yyyy")


def str_datetime(datetime):
    return QDateTime.fromString(datetime, "dd-MM-yyyy HH:mm:ss")


def datetime_str(datetime):
    return QDateTime.toString(datetime, "dd-MM-yyyy HH:mm:ss")