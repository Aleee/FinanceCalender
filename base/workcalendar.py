from typing import Dict, List

from PySide6.QtCore import QDate, QSettings

CALENDAR_CATEGORIES: tuple = ("holidays", "workbank", "worknonbank")

# Дни недели (QDate.dayOfWeek(): 1 = Пн ... 7 = Вс), допустимые для каждой категории
ALLOWED_WEEKDAYS: Dict[str, set] = {
    "holidays": {1, 2, 3, 4, 5},
    "workbank": {6, 7},
    "worknonbank": {6, 7},
}

WEEKDAY_ABBR: Dict[int, str] = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}


def _settings_key(year: int, category: str) -> str:
    return f"Calendar/{year}/{category}"


def load_calendar_exceptions(settings: QSettings, year: int) -> Dict[str, List[QDate]]:
    result: Dict[str, List[QDate]] = {}
    for category in CALENDAR_CATEGORIES:
        raw_value = settings.value(_settings_key(year, category), "")
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


def save_calendar_exceptions(settings: QSettings, year: int, data: Dict[str, List[QDate]]) -> None:
    for category in CALENDAR_CATEGORIES:
        dates = sorted(data.get(category, []))
        raw_value = ",".join(date.toString("yyyy-MM-dd") for date in dates)
        settings.setValue(_settings_key(year, category), raw_value)


def is_working_day(settings: QSettings, date: QDate) -> bool:
    year_data = load_calendar_exceptions(settings, date.year())
    if date in year_data["holidays"]:
        return False
    if date in year_data["workbank"] or date in year_data["worknonbank"]:
        return True
    return date.dayOfWeek() not in (6, 7)

def is_bank_day(settings: QSettings, date: QDate) -> bool:
    year_data = load_calendar_exceptions(settings, date.year())
    if date in year_data["holidays"] or date in year_data["worknonbank"]:
        return False
    if date in year_data["workbank"]:
        return True
    return date.dayOfWeek() not in (6, 7)
