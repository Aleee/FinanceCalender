from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from base.dbhandler import DBHandler

Migration = str | Callable[["DBHandler"], None]

CSV_SETTINGS_KEYS: tuple[str, ...] = (
    "CSVparser/columnstoparse", "CSVparser/knownunp", "CSVparser/nomatchpatterns", "CSVparser/patterns",
    "CSVparser/responsible", "CSVparser/rowperiod", "CSVparser/rowtransactionstart",
)


TRAILING_CHARS = "char(10) || char(13) || char(9) || ' '"


class MigrationError(Exception):
    pass


def migrate_2_to_3(dbh: "DBHandler") -> None:
    settings = dbh.settings_handler.settings
    keys = [key for key in settings.allKeys() if key in CSV_SETTINGS_KEYS or key.startswith("Calendar/")]
    for key in keys:
        if dbh.get_setting(key, None) is not None:
            continue
        value = settings.value(key, "")
        if isinstance(value, list):
            value = ",".join(value)
        if not dbh.set_setting(key, value):
            raise MigrationError(f"Не удалось перенести настройку {key} из settings.ini в базу данных")
    dbh.after_commit_actions.append(lambda: remove_settings_keys(settings, keys))


def remove_settings_keys(settings, keys: list[str]) -> None:
    for key in keys:
        settings.remove(key)
    settings.sync()


MIGRATIONS: dict[int, list[Migration]] = {
    3: [migrate_2_to_3],
    4: [f"ALTER TABLE event DROP COLUMN {column}" for column in ("remainamount", "todayshare", "lastpaymentdate", "filterflags")]
       + [f"UPDATE event SET {column} = rtrim({column}, {TRAILING_CHARS}) WHERE {column} <> rtrim({column}, {TRAILING_CHARS})"
          for column in ("receiver", "name", "descr", "notes", "receivernocase")],
}
