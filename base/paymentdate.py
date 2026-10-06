from PySide6.QtCore import QDate, QSettings

from base.contract import ContractDocumentData, PaymentDueType, DaysType, MonthType
from base.workcalendar import is_working_day, is_bank_day

_MONTH_SHIFT = {MonthType.CURRENT: 0, MonthType.NEXT: 1, MonthType.PREVIOUS: -1}


def fixed_date(period_year: int, period_month: int, month_day: int | None, month_type: MonthType | None) -> QDate:
    if month_day is None or month_type is None:
        raise ValueError("Для фиксированной даты платежа не заданы month_day/month_type")
    first = QDate(period_year, period_month, 1).addMonths(_MONTH_SHIFT[month_type])
    return QDate(first.year(), first.month(), min(max(int(month_day), 1), first.daysInMonth()))


def next_working_day(settings: QSettings, day: QDate) -> QDate:
    while not is_working_day(settings, day):
        day = day.addDays(1)
    return day


def add_days(settings: QSettings, start: QDate, count: int, days_type: DaysType) -> QDate:
    if count < 0:
        return start.addDays(count)
    if days_type == DaysType.CALENDAR:
        return next_working_day(settings, start.addDays(count))
    is_valid_day = is_working_day if days_type == DaysType.WORKING else is_bank_day
    day, left = start, count
    while left > 0:
        day = day.addDays(1)
        if is_valid_day(settings, day):
            left -= 1
    return day


def calculate_payment_date(settings: QSettings, terms: ContractDocumentData, trigger_date: QDate,
                           period_year: int, period_month: int) -> QDate | None:
    if terms.payment_type == PaymentDueType.FIXED:
        result = next_working_day(settings, fixed_date(period_year, period_month, terms.month_day, terms.month_type))

    elif terms.payment_type == PaymentDueType.RELATIVE:
        if terms.days_type is None:
            return None
        result = add_days(settings, trigger_date, terms.days_count, terms.days_type)
        # Дополнительное календарное условие: платёж не позднее указанной даты
        if terms.has_calendar_condition and terms.month_day and terms.month_type:
            limit = fixed_date(period_year, period_month, terms.month_day, terms.month_type)
            result = min(result, next_working_day(settings, limit))

    else:
        return None

    return result
