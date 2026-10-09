from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from base.dbhandler import DBHandler

Migration = str | Callable[["DBHandler"], None]

CSV_SETTINGS_KEYS: tuple[str, ...] = (
    "CSVparser/columnstoparse", "CSVparser/knownunp", "CSVparser/nomatchpatterns", "CSVparser/patterns",
    "CSVparser/responsible", "CSVparser/rowperiod", "CSVparser/rowtransactionstart",
)


TRAILING_CHARS = "char(10) || char(13) || char(9) || ' '"

DATA_TABLES: tuple[str, ...] = (
    "event", "payment", "contractor", "contract", "contractdocument", "contractpaymentterm", "contractsavedvalues",
    "personal", "position", "department", "finplan", "fulfillmentdata", "contractdocumenttype",
)
SERVICE_META_KEYS: tuple[str, ...] = ("change_counter", "sync_token", "db_uuid", "db_version")
INCREASE_CHANGE_COUNTER = "UPDATE meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'change_counter'"


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


def change_counter_triggers() -> list[str]:
    service_keys = ", ".join(f"'{key}'" for key in SERVICE_META_KEYS)
    triggers = [f'CREATE TRIGGER trg_{table}_{action.lower()} AFTER {action} ON "{table}" BEGIN {INCREASE_CHANGE_COUNTER}; END'
                for table in DATA_TABLES for action in ("INSERT", "UPDATE", "DELETE")]
    triggers += [
        f"CREATE TRIGGER trg_meta_insert AFTER INSERT ON meta WHEN NEW.key NOT IN ({service_keys}) BEGIN {INCREASE_CHANGE_COUNTER}; END",
        f"CREATE TRIGGER trg_meta_update AFTER UPDATE ON meta WHEN NEW.key NOT IN ({service_keys}) AND OLD.value IS NOT NEW.value "
        f"BEGIN {INCREASE_CHANGE_COUNTER}; END",
        f"CREATE TRIGGER trg_meta_delete AFTER DELETE ON meta WHEN OLD.key NOT IN ({service_keys}) BEGIN {INCREASE_CHANGE_COUNTER}; END",
    ]
    return triggers


MIGRATIONS: dict[int, list[Migration]] = {
    3: [migrate_2_to_3],
    4: [f"ALTER TABLE event DROP COLUMN {column}" for column in ("remainamount", "todayshare", "lastpaymentdate", "filterflags")]
       + [f"UPDATE event SET {column} = rtrim({column}, {TRAILING_CHARS}) WHERE {column} <> rtrim({column}, {TRAILING_CHARS})"
          for column in ("receiver", "name", "descr", "notes", "receivernocase")],
    5: ["DELETE FROM meta WHERE rowid NOT IN (SELECT MIN(rowid) FROM meta GROUP BY key)",
        "CREATE UNIQUE INDEX idx_meta_key ON meta (key)",
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('db_uuid', lower(hex(randomblob(16))))",
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('sync_token', lower(hex(randomblob(16))))",
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('change_counter', '0')"]
       + change_counter_triggers(),
}
