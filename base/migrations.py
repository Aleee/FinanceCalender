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
CHANGELOG_TABLE = "changelog"
CHANGELOG_DATA_TABLES: tuple[str, ...] = ("event", "payment")
CHANGELOG_ACTIONS: tuple[str, ...] = ("insert", "update", "delete")
CHANGELOG_AUTHOR_KEY = "changelog_author"
CHANGELOG_MACHINE_KEY = "changelog_machine"
SERVICE_META_KEYS: tuple[str, ...] = ("change_counter", "sync_token", "db_uuid", "db_version",
                                      CHANGELOG_AUTHOR_KEY, CHANGELOG_MACHINE_KEY)
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


def table_change_counter_triggers(table: str) -> list[str]:
    return [f'CREATE TRIGGER trg_{table}_{action.lower()} AFTER {action} ON "{table}" BEGIN {INCREASE_CHANGE_COUNTER}; END'
            for action in ("INSERT", "UPDATE", "DELETE")]


def meta_change_counter_triggers() -> list[str]:
    service_keys = ", ".join(f"'{key}'" for key in SERVICE_META_KEYS)
    return [
        f"CREATE TRIGGER trg_meta_insert AFTER INSERT ON meta WHEN NEW.key NOT IN ({service_keys}) BEGIN {INCREASE_CHANGE_COUNTER}; END",
        f"CREATE TRIGGER trg_meta_update AFTER UPDATE ON meta WHEN NEW.key NOT IN ({service_keys}) AND OLD.value IS NOT NEW.value "
        f"BEGIN {INCREASE_CHANGE_COUNTER}; END",
        f"CREATE TRIGGER trg_meta_delete AFTER DELETE ON meta WHEN OLD.key NOT IN ({service_keys}) BEGIN {INCREASE_CHANGE_COUNTER}; END",
    ]


def change_counter_triggers() -> list[str]:
    triggers = [trigger for table in DATA_TABLES for trigger in table_change_counter_triggers(table)]
    return triggers + meta_change_counter_triggers()


def changelog_row(table: str, action: str, record_id: str, field: str, old_value: str, new_value: str, condition: str = "") -> str:
    return (f"INSERT INTO {CHANGELOG_TABLE} (changed_at, author, machine, tablename, recordid, action, field, oldvalue, newvalue) "
            f"SELECT strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'), "
            f"(SELECT value FROM meta WHERE key = '{CHANGELOG_AUTHOR_KEY}'), (SELECT value FROM meta WHERE key = '{CHANGELOG_MACHINE_KEY}'), "
            f"'{table}', {record_id}, '{action}', {field}, {old_value}, {new_value}{condition}")


def changelog_triggers(table: str, columns: list[str]) -> list[str]:
    def snapshot(row: str) -> str:
        return "json_object(" + ", ".join(f"'{column}', {row}.\"{column}\"" for column in columns) + ")"

    updates = " ".join(
        changelog_row(table, "update", "NEW.id", f"'{column}'", f'OLD."{column}"', f'NEW."{column}"',
                      f' WHERE OLD."{column}" IS NOT NEW."{column}"') + ";"
        for column in columns if column != "id")
    bodies = {
        "insert": changelog_row(table, "insert", "NEW.id", "NULL", "NULL", snapshot("NEW")) + ";",
        "update": updates,
        "delete": changelog_row(table, "delete", "OLD.id", "NULL", snapshot("OLD"), "NULL") + ";",
    }
    return [f'CREATE TRIGGER trg_{table}_log_{action} AFTER {action.upper()} ON "{table}" BEGIN {bodies[action]} END'
            for action in CHANGELOG_ACTIONS]


def rebuild_changelog_triggers(dbh: "DBHandler") -> None:
    dbh.rebuild_changelog_triggers()


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
    6: ["DROP TABLE contractsavedvalues",
        'CREATE TABLE "contractsavedvalues" ("contractdocumentid" INTEGER PRIMARY KEY, "receiver" TEXT, "category" INTEGER, '
        '"subcategory" INTEGER, "name" TEXT, "nds" INTEGER, "paymenttype" INTEGER, "descr" TEXT, "responsible" INTEGER, "hidden" INTEGER)']
       + table_change_counter_triggers("contractsavedvalues"),
    7: ["ALTER TABLE event DROP COLUMN receivernocase"],
    8: ["ALTER TABLE contractor ADD COLUMN archived INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE contract ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"],
    9: ["ALTER TABLE contractdocument ADD COLUMN monthly INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE contractdocument ADD COLUMN monthlyamount TEXT"],
    10: ["ALTER TABLE contractdocument ADD COLUMN monthlyname TEXT"],
    11: [f"CREATE TABLE {CHANGELOG_TABLE} (id INTEGER PRIMARY KEY, changed_at TEXT NOT NULL, author TEXT, machine TEXT, "
         f"tablename TEXT NOT NULL, recordid INTEGER, action TEXT NOT NULL, field TEXT, oldvalue TEXT, newvalue TEXT)",
         f"CREATE INDEX idx_{CHANGELOG_TABLE}_record ON {CHANGELOG_TABLE} (tablename, recordid)",
         f"CREATE INDEX idx_{CHANGELOG_TABLE}_time ON {CHANGELOG_TABLE} (changed_at)",
         "DROP TRIGGER IF EXISTS trg_meta_insert", "DROP TRIGGER IF EXISTS trg_meta_update", "DROP TRIGGER IF EXISTS trg_meta_delete"]
        + meta_change_counter_triggers() + [rebuild_changelog_triggers],
}
