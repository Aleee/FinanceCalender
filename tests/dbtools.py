import sqlite3
from pathlib import Path

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
    "receivernocase"  TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
)
"""

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
    'CREATE TABLE "contractor" ("id" INTEGER NOT NULL UNIQUE, "name" TEXT, PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contract" ("id" INTEGER NOT NULL UNIQUE, "contractor_id" INTEGER, "name" TEXT, "date" TEXT, PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contractdocument" ("id" INTEGER NOT NULL UNIQUE, "contract_id" INTEGER, "document_type" INTEGER, '
    '"document_name" TEXT, "description" TEXT, "position_id" INTEGER, PRIMARY KEY("id" AUTOINCREMENT))',
    'CREATE TABLE "contractpaymentterm" ("document_id" INTEGER, "payment_type" TEXT NOT NULL, "days_count" INTEGER DEFAULT 0)',
    'CREATE TABLE "contractsavedvalues" ("contract_id" INTEGER, "category" INTEGER, "name" TEXT)',
    'CREATE TABLE "personal" ("id" INTEGER NOT NULL, "name" TEXT, "department" INTEGER, "position" INTEGER, "archived" INTEGER, PRIMARY KEY("id"))',
    'CREATE TABLE "position" ("id" INTEGER, "department" INTEGER, "name" TEXT, PRIMARY KEY("id"))',
    'CREATE TABLE "department" ("id" INTEGER NOT NULL, "name" TEXT NOT NULL, PRIMARY KEY("id"))',
    'CREATE TABLE "finplan" ("year" INTEGER, "category" INTEGER, "m1" INTEGER)',
    'CREATE TABLE "fulfillmentdata" ("startdate" TEXT, "enddate" TEXT, "10000" INTEGER, UNIQUE("enddate", "startdate"))',
    'CREATE TABLE "contractdocumenttype" ("id" INTEGER, "name" TEXT)',
]


def create_db(path: Path, version: int, meta: dict[str, str] | None = None, legacy_event: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        for ddl in (LEGACY_EVENT_DDL if legacy_event else EVENT_DDL, PAYMENT_DDL, META_DDL, *OTHER_TABLES_DDL):
            con.execute(ddl)
        rows = {"db_version": str(version), **(meta or {})}
        con.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", rows.items())
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
