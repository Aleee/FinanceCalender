from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from base.dbhandler import DBHandler

Migration = str | Callable[["DBHandler"], None]

CSV_SETTINGS_KEYS: tuple[str, ...] = (
    "CSVparser/columnstoparse", "CSVparser/knownunp", "CSVparser/nomatchpatterns", "CSVparser/patterns",
    "CSVparser/responsible", "CSVparser/rowperiod", "CSVparser/rowtransactionstart",
)


class MigrationError(Exception):
    pass


def migrate_2_to_3(dbh: "DBHandler") -> None:
    settings = dbh.settings_handler.settings
    for key in settings.allKeys():
        if key not in CSV_SETTINGS_KEYS and not key.startswith("Calendar/"):
            continue
        if dbh.get_setting(key, None) is not None:
            continue
        value = settings.value(key, "")
        if isinstance(value, list):
            value = ",".join(value)
        if not dbh.set_setting(key, value):
            raise MigrationError(f"Не удалось перенести настройку {key} из settings.ini в базу данных")


# Ключ - версия БД, до которой поднимает миграция. Элемент списка - SQL-запрос или функция от DBHandler
MIGRATIONS: dict[int, list[Migration]] = {
    3: [migrate_2_to_3],
}
