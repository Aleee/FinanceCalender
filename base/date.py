from datetime import datetime, date
from typing import Optional

from PySide6.QtCore import QDate, QDateTime

import lovely_logger as log

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


def str_date(string, python_date: bool = False) -> Optional[QDate|date]:
    try:
        if python_date:
            return datetime.strptime(string, "%Y-%m-%d").date()
        else:
            return QDate.fromString(string, "yyyy-MM-dd")
    except ValueError:
        log.e(f"Не удалось преобразовать строку ({string}) в дату (python_date = {int(python_date)})")
        if python_date:
            return date(2000, 1, 1)
        else:
            return QDate(2000, 1, 1)

def date_str(date_obj: Optional[QDate | date]) -> str:
    try:
        if isinstance(date_obj, QDate):
            return date_obj.toString("yyyy-MM-dd")
        elif isinstance(date_obj, date):
            return date_obj.isoformat()
    except ValueError:
        return "<DATE CONVERSION ERROR>"


def date_purestr(date, short: bool = False) -> str:
    return date.toString("ddMMyy") if short else date.toString("ddMMyyyy")


def date_displstr(date) -> str:
    if isinstance(date, QDate):
        return date.toString("dd.MM.yyyy")
    elif isinstance(date, QDateTime):
        return date.toString("dd.MM.yyyy HH:mm")
    else:
        return ""


def first_date_of_month(date) -> QDate:
    return QDate(date.year(), date.month(), 1)


def last_date_of_month(date) -> QDate:
    return QDate(date.year(), date.month(), date.daysInMonth())


