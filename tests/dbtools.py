import sqlite3
from pathlib import Path

from base.migrations import CHANGELOG_DATA_TABLES, changelog_triggers

EVENT_DDL = """
CREATE TABLE "event" (
    "receiver"  TEXT,
    "id"  INTEGER NOT NULL,
    "type"  INTEGER,
    "contractdocument_id"  INTEGER,
    "category"  INTEGER,
    "subcategory"  INTEGER,
    "name"  TEXT,
    "totalamount"  TEXT,
    "nds"  INTEGER,
    "duedate"  TEXT,
    "createdate"  TEXT,
    "paymenttype"  INTEGER,
    "descr"  TEXT,
    "responsible"  TEXT,
    "notes"  TEXT,
    "featured"  INTEGER,
    "hidden"  INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT)
)
"""

PRE_V7_EVENT_DDL = EVENT_DDL.replace('"hidden"  INTEGER,', '"hidden"  INTEGER,\n    "receivernocase"  TEXT,')

LEGACY_EVENT_DDL = """
CREATE TABLE "event" (
    "receiver"  TEXT,
    "id"  INTEGER NOT NULL,
    "type"  INTEGER,
    "contractdocument_id"  INTEGER,
    "category"  INTEGER,
    "subcategory"  INTEGER,
    "name"  TEXT,
    "remainamount"  TEXT,
    "totalamount"  TEXT,
    "nds"  INTEGER,
    "duedate"  TEXT,
    "createdate"  TEXT,
    "paymenttype"  INTEGER,
    "descr"  TEXT,
    "responsible"  TEXT,
    "notes"  TEXT,
    "todayshare"  TEXT,
    "lastpaymentdate"  TEXT,
    "filterflags"  INTEGER,
    "featured"  INTEGER,
    "hidden"  INTEGER,
    "receivernocase"  TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
)
"""

PAYMENT_DDL = """
CREATE TABLE "payment" (
    "id"  INTEGER NOT NULL,
    "eventid"  INT,
    "paymentdate"  TEXT,
    "sum"  TEXT,
    "createdate"  TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
)
"""

META_DDL = 'CREATE TABLE "meta" ("key" TEXT, "value" TEXT)'

OTHER_TABLES_DDL = [
    'CREATE TABLE "contractor" ("id" INTEGER NOT NULL UNIQUE, "name" TEXT, "archived" INTEGER NOT NULL DEFAULT 0, PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contract" ("id" INTEGER NOT NULL UNIQUE, "contractor_id" INTEGER, "name" TEXT, "date" TEXT, '
    '"archived" INTEGER NOT NULL DEFAULT 0, PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contractdocument" ("id" INTEGER NOT NULL UNIQUE, "contract_id" INTEGER, "document_type" INTEGER, '
    '"document_name" TEXT, "description" TEXT, "position_id" INTEGER, "monthly" INTEGER NOT NULL DEFAULT 0, "monthlyamount" TEXT, "monthlyname" TEXT, '
    'PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contractpaymentterm" ("document_id" INTEGER, "payment_type" TEXT NOT NULL, "days_count" INTEGER DEFAULT 0, '
    '"days_type" TEXT, "has_calendar_condition" BOOLEAN DEFAULT FALSE, "month_day" INTEGER, "month_type" TEXT, PRIMARY KEY("document_id"))',
    'CREATE TABLE "contractsavedvalues" ("contractdocumentid" INTEGER PRIMARY KEY, "receiver" TEXT, "category" INTEGER, '
    '"subcategory" INTEGER, "name" TEXT, "nds" INTEGER, "paymenttype" INTEGER, "descr" TEXT, "responsible" INTEGER, "hidden" INTEGER)',
    'CREATE TABLE "personal" ("id" INTEGER NOT NULL, "name" TEXT, "department" INTEGER, "position" INTEGER, "archived" INTEGER, PRIMARY KEY("id"))',
    'CREATE TABLE "position" ("id" INTEGER, "department" INTEGER, "name" TEXT, PRIMARY KEY("id"))',
    'CREATE TABLE "department" ("id" INTEGER NOT NULL, "name" TEXT NOT NULL, PRIMARY KEY("id"))',
    'CREATE TABLE "finplan" ("year" INTEGER, "category" INTEGER, ' + ", ".join(f'"m{month}" INTEGER' for month in range(1, 13)) + ")",
    'CREATE TABLE "fulfillmentdata" ("startdate" TEXT, "enddate" TEXT, "10000" INTEGER, "21000" INTEGER, "22000" INTEGER, '
    '"23100" INTEGER, "23200" INTEGER, UNIQUE("enddate", "startdate"))',
    'CREATE TABLE "contractdocumenttype" ("id" INTEGER, "name" TEXT)',
]


CHANGELOG_DDL = [
    'CREATE TABLE changelog (id INTEGER PRIMARY KEY, changed_at TEXT NOT NULL, author TEXT, machine TEXT, '
    'tablename TEXT NOT NULL, recordid INTEGER, action TEXT NOT NULL, field TEXT, oldvalue TEXT, newvalue TEXT)',
    'CREATE INDEX idx_changelog_record ON changelog (tablename, recordid)',
    'CREATE INDEX idx_changelog_time ON changelog (changed_at)',
]


def pre_v8_ddl(ddl: str) -> str:
    if ddl.startswith(('CREATE TABLE "contractor"', 'CREATE TABLE "contract" ')):
        return ddl.replace('"archived" INTEGER NOT NULL DEFAULT 0, ', '')
    return ddl


def pre_v6_ddl(ddl: str) -> str:
    if ddl.startswith('CREATE TABLE "contractsavedvalues"'):
        return ('CREATE TABLE "contractsavedvalues" ("contract_id" INTEGER, "category" INTEGER, "subcategory" INTEGER, "name" TEXT, '
                '"nds" INTEGER, "paymenttype" INTEGER, "descr" TEXT, "responsible" INTEGER, "hidden" INTEGER)')
    return ddl


def pre_v9_ddl(ddl: str) -> str:
    if ddl.startswith('CREATE TABLE "contractdocument"'):
        return ddl.replace('"monthly" INTEGER NOT NULL DEFAULT 0, "monthlyamount" TEXT, ', '')
    return ddl


def pre_v10_ddl(ddl: str) -> str:
    if ddl.startswith('CREATE TABLE "contractdocument"'):
        return ddl.replace('"monthlyname" TEXT, ', '')
    return ddl


def create_db(path: Path, version: int, meta: dict[str, str] | None = None, legacy_event: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        event_ddl = LEGACY_EVENT_DDL if legacy_event else PRE_V7_EVENT_DDL if 4 <= version < 7 else EVENT_DDL
        other_tables = OTHER_TABLES_DDL
        if version < 10:
            other_tables = [pre_v10_ddl(ddl) for ddl in other_tables]
        if version < 9:
            other_tables = [pre_v9_ddl(ddl) for ddl in other_tables]
        if version < 6:
            other_tables = [pre_v6_ddl(ddl) for ddl in other_tables]
        if version < 8:
            other_tables = [pre_v8_ddl(ddl) for ddl in other_tables]
        for ddl in (event_ddl, PAYMENT_DDL, META_DDL, *other_tables):
            con.execute(ddl)
        rows = {"db_version": str(version), **(meta or {})}
        con.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", rows.items())
        if version >= 11:
            for ddl in CHANGELOG_DDL:
                con.execute(ddl)
            for table in CHANGELOG_DATA_TABLES:
                columns = [row[1] for row in con.execute(f"PRAGMA table_info('{table}')")]
                for trigger in changelog_triggers(table, columns):
                    con.execute(trigger)
        con.commit()
    finally:
        con.close()
    return path


def fetch_all(path: Path, sql: str) -> list[tuple]:
    con = sqlite3.connect(path)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def read_meta(path: Path) -> dict[str, str]:
    return dict(fetch_all(path, "SELECT key, value FROM meta"))


def read_version(path: Path) -> int:
    return int(read_meta(path)["db_version"])


def table_columns(path: Path, table: str) -> list[str]:
    return [row[1] for row in fetch_all(path, f"PRAGMA table_info('{table}')")]


def schema(path: Path) -> list[tuple]:
    return fetch_all(path, "SELECT name, sql FROM sqlite_master ORDER BY name")
