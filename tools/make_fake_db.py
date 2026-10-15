import random
import sqlite3
import sys
import uuid
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
sys.stdout.reconfigure(encoding="utf-8")

from base.liability import CATEGORY_NAMES, LiabilityCategory

SOURCE_DB = PROJECT_DIR / "data" / "db" / "db.db"
FAKE_DB = PROJECT_DIR / "tests" / "fakedata" / "db" / "db.db"

COPY_AS_IS = ["contractdocumenttype", "department", "position", "finplan", "fulfillmentdata", "contractpaymentterm"]
KEEP_META_PREFIXES = ("Calendar/",)

rng = random.Random(2026)


class Names:
    def __init__(self, template: str):
        self.template = template
        self.mapping: dict[str, str] = {}

    def __call__(self, real: str | None) -> str | None:
        if not real:
            return real
        if real not in self.mapping:
            self.mapping[real] = self.template.format(len(self.mapping) + 1)
        return self.mapping[real]


def category_name(category: int) -> str:
    try:
        return CATEGORY_NAMES[LiabilityCategory(category)]
    except (ValueError, KeyError):
        return "Прочее"


def money(value: float) -> str:
    return f"{value:.2f}"


def create_schema(src: sqlite3.Connection, dst: sqlite3.Connection) -> list[str]:
    triggers = []
    rows = src.execute("SELECT type, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'").fetchall()
    for kind, sql in rows:
        if kind == "trigger":
            triggers.append(sql)
        else:
            dst.execute(sql)
    return triggers


def copy_table(src: sqlite3.Connection, dst: sqlite3.Connection, table: str) -> None:
    rows = src.execute(f'SELECT * FROM "{table}"').fetchall()
    if rows:
        marks = ", ".join("?" * len(rows[0]))
        dst.executemany(f'INSERT INTO "{table}" VALUES ({marks})', rows)


def fill_meta(src: sqlite3.Connection, dst: sqlite3.Connection) -> None:
    version = src.execute("SELECT value FROM meta WHERE key = 'db_version'").fetchone()[0]
    rows = [("db_version", version), ("db_uuid", uuid.uuid4().hex), ("sync_token", uuid.uuid4().hex), ("change_counter", "0")]
    for key, value in src.execute("SELECT key, value FROM meta"):
        if key.startswith(KEEP_META_PREFIXES):
            rows.append((key, value))
    dst.executemany("INSERT INTO meta VALUES (?, ?)", rows)


def fill_people(src: sqlite3.Connection, dst: sqlite3.Connection) -> None:
    for number, (person_id, _, department, position, archived) in enumerate(src.execute("SELECT * FROM personal"), start=1):
        dst.execute("INSERT INTO personal VALUES (?, ?, ?, ?, ?)", (person_id, f"Сотрудник {number}", department, position, archived))


def fill_contracts(src: sqlite3.Connection, dst: sqlite3.Connection, contractor_name: Names) -> None:
    for contractor_id, name in src.execute("SELECT id, name FROM contractor"):
        dst.execute("INSERT INTO contractor VALUES (?, ?)", (contractor_id, contractor_name(name)))
    for contract_id, contractor_id, _, contract_date in src.execute("SELECT * FROM contract"):
        dst.execute("INSERT INTO contract VALUES (?, ?, ?, ?)", (contract_id, contractor_id, f"Д-{contract_id}/{(contract_date or '2025')[:4]}", contract_date))
    for document_id, contract_id, document_type, _, _, position_id in src.execute("SELECT * FROM contractdocument"):
        dst.execute("INSERT INTO contractdocument VALUES (?, ?, ?, ?, ?, ?)",
                    (document_id, contract_id, document_type, f"Документ {document_id}", f"Условия оплаты по документу {document_id}", position_id))


def fill_events(src: sqlite3.Connection, dst: sqlite3.Connection, receiver_name: Names) -> None:
    columns = [row[1] for row in dst.execute('PRAGMA table_info("event")')]
    scale: dict[int, float] = {}
    for row in src.execute("SELECT * FROM event ORDER BY id"):
        event = dict(zip(columns, row))
        if event["type"] == 2:
            factor = rng.uniform(0.7, 1.3)
            scale[event["id"]] = factor
            event["receiver"] = receiver_name(event["receiver"])
            event["name"] = f"{category_name(event['category'])}, позиция {event['id']}" if event["name"] else event["name"]
            if event["totalamount"] not in (None, ""):
                event["totalamount"] = money(round(float(event["totalamount"]) * factor, 2))
            if event["descr"]:
                event["descr"] = f"Счет № {rng.randint(100, 9999)} от {event['createdate'] or event['duedate']}"
            if event["notes"]:
                event["notes"] = "Тестовая заметка"
            if "receivernocase" in event and event["receiver"]:
                event["receivernocase"] = event["receiver"].lower()
        dst.execute(f'INSERT INTO event ({", ".join(columns)}) VALUES ({", ".join("?" * len(columns))})', list(event.values()))
    for payment_id, event_id, payment_date, amount, create_date in src.execute("SELECT * FROM payment ORDER BY id"):
        new_amount = money(round(float(amount) * scale.get(event_id, 1.0), 2)) if amount not in (None, "") else amount
        dst.execute("INSERT INTO payment VALUES (?, ?, ?, ?, ?)", (payment_id, event_id, payment_date, new_amount, create_date))


def main() -> None:
    if FAKE_DB.exists():
        FAKE_DB.unlink()
    FAKE_DB.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{SOURCE_DB.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(FAKE_DB)
    try:
        triggers = create_schema(src, dst)
        fill_meta(src, dst)
        for table in COPY_AS_IS:
            copy_table(src, dst, table)
        fill_people(src, dst)
        receiver_name = Names("ООО «Контрагент {}»")
        fill_contracts(src, dst, receiver_name)
        fill_events(src, dst, receiver_name)
        for sql in triggers:
            dst.execute(sql)
        dst.commit()
        counts = {t: dst.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in ("event", "payment", "contractor", "contract", "contractdocument", "personal")}
        check = dst.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        src.close()
        dst.close()
    print(f"Фейковая база создана: {FAKE_DB}")
    print(f"Проверка: {check}, записей: {counts}")


if __name__ == "__main__":
    main()
