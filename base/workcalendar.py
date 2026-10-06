from typing import Dict, List

from PySide6.QtCore import QDate

CALENDAR_CATEGORIES: tuple[str, ...] = ("holidays", "workbank", "worknonbank")

# Дни недели (QDate.dayOfWeek(): 1 = Пн ... 7 = Вс), допустимые для каждой категории
ALLOWED_WEEKDAYS: Dict[str, set[int]] = {
    "holidays": {1, 2, 3, 4, 5},
    "workbank": {6, 7},
    "worknonbank": {6, 7},
}

WEEKDAY_ABBR: Dict[int, str] = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}

# Кэш уже распарсенных исключений по годам: is_working_day/is_bank_day вызывают
# load_calendar_exceptions на каждый день при переборе дат, а без кэша каждый такой
# вызов заново читал бы БД и парсил строки на весь год. Инвалидируется в
# save_calendar_exceptions — единственном месте, где эти настройки меняются.
_exceptions_cache: Dict[int, Dict[str, List[QDate]]] = {}


def clear_calendar_cache() -> None:
    _exceptions_cache.clear()


def _settings_key(year: int, category: str) -> str:
    return f"Calendar/{year}/{category}"


def _read_calendar_exceptions(dbh, year: int) -> Dict[str, List[QDate]]:
    result: Dict[str, List[QDate]] = {}
    for category in CALENDAR_CATEGORIES:
        raw_value = dbh.get_setting(_settings_key(year, category))
        dates: List[QDate] = []
        if raw_value:
            for date_str in str(raw_value).split(","):
                date_str = date_str.strip()
                if not date_str:
                    continue
                date = QDate.fromString(date_str, "yyyy-MM-dd")
                if date.isValid():
                    dates.append(date)
        dates.sort()
        result[category] = dates
    return result


def load_calendar_exceptions(dbh, year: int) -> Dict[str, List[QDate]]:
    cached = _exceptions_cache.get(year)
    if cached is None:
        cached = _read_calendar_exceptions(dbh, year)
        _exceptions_cache[year] = cached
    # Возвращаем копию списков: вызывающий код (диалог настроек) мутирует
    # результат в процессе редактирования, это не должно портить кэш до сохранения
    return {category: list(dates) for category, dates in cached.items()}


def save_calendar_exceptions(dbh, year: int, data: Dict[str, List[QDate]]) -> None:
    for category in CALENDAR_CATEGORIES:
        dates = sorted(data.get(category, []))
        raw_value = ",".join(date.toString("yyyy-MM-dd") for date in dates)
        dbh.set_setting(_settings_key(year, category), raw_value)
    _exceptions_cache.pop(year, None)


def is_working_day(dbh, date: QDate) -> bool:
    year_data = load_calendar_exceptions(dbh, date.year())
    if date in year_data["holidays"]:
        return False
    if date in year_data["workbank"] or date in year_data["worknonbank"]:
        return True
    return date.dayOfWeek() not in (6, 7)

def is_bank_day(dbh, date: QDate) -> bool:
    year_data = load_calendar_exceptions(dbh, date.year())
    if date in year_data["holidays"] or date in year_data["worknonbank"]:
        return False
    if date in year_data["workbank"]:
        return True
    return date.dayOfWeek() not in (6, 7)
