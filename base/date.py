from datetime import datetime, date
from typing import Optional

from PySide6.QtCore import QDate, QDateTime

import lovely_logger as log

MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
             "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

def get_date_diff(start_date: QDate, end_date: QDate) -> int:
    return start_date.daysTo(end_date)


def days_to_weekend(from_date: QDate) -> int:
    current_day_of_week: int = from_date.dayOfWeek()
    return 7 - current_day_of_week if current_day_of_week != 7 else 0


def days_to_month(from_date: QDate) -> int:
    return from_date.daysInMonth() - from_date.day()


def str_date(string: Optional[str], python_date: bool = False) -> QDate | date:
    try:
        if python_date:
            return datetime.strptime(string, "%Y-%m-%d").date()
        else:
            result = QDate.fromString(string, "yyyy-MM-dd")
            # Пустая строка - легитимное "дата не задана" (например, Col.INCURRENCEDATE),
            # а не ошибка, поэтому логируем только непустые нераспознанные строки
            if not result.isValid() and string:
                raise ValueError(string)
            return result
    except (ValueError, TypeError):
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
        else:
            return "<DATE CONVERSION ERROR>"
    except ValueError:
        log.e(f"Не удалось преобразовать дату ({date_obj}) в строку")
        return "<DATE CONVERSION ERROR>"


def date_purestr(qdate: QDate, short: bool = False) -> str:
    return qdate.toString("ddMMyy") if short else qdate.toString("ddMMyyyy")


def date_displstr(qdate: QDate | QDateTime) -> str:
    if isinstance(qdate, QDate):
        return qdate.toString("dd.MM.yyyy")
    elif isinstance(qdate, QDateTime):
        return qdate.toString("dd.MM.yyyy HH:mm")
    else:
        return ""


def first_date_of_month(qdate: QDate) -> QDate:
    return QDate(qdate.year(), qdate.month(), 1)


def last_date_of_month(qdate: QDate) -> QDate:
    return QDate(qdate.year(), qdate.month(), qdate.daysInMonth())
