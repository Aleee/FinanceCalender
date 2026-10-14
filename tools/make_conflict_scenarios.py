import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from base.paths import db_path
from base.sync import MasterInfo
from base.version import APP_VERSION

OUTPUT_DIR = PROJECT_DIR / "conflict_scenarios"
TODAY = datetime.now().strftime("%Y-%m-%d")


@dataclass
class Picks:
    open_a: int
    open_b: int
    paid_a: int
    paid_b: int
    payment_a: int


@dataclass
class Scenario:
    slug: str
    title: str
    local_text: str
    master_text: str
    expected: str
    expected_text: str
    local: Callable[[sqlite3.Connection, Picks], None]
    master: Callable[[sqlite3.Connection, Picks], None]
    warnings: tuple[str, ...] = ()


def money(value: str, delta: str) -> str:
    return str((Decimal(value) + Decimal(delta)).quantize(Decimal("0.01")))


def total_of(con: sqlite3.Connection, event_id: int) -> str:
    return con.execute("SELECT totalamount FROM event WHERE id = ?", (event_id,)).fetchone()[0]


def add_payment(con: sqlite3.Connection, event_id: int, amount: str) -> None:
    con.execute("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (?, ?, ?, ?)", (event_id, TODAY, amount, TODAY))


def add_full_payment(con: sqlite3.Connection, event_id: int) -> None:
    add_payment(con, event_id, total_of(con, event_id))


def add_event(con: sqlite3.Connection, template_id: int, name: str) -> None:
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM event WHERE id = ?", (template_id,)).fetchone()
    con.row_factory = None
    columns = [column for column in row.keys() if column != "id"]
    values = [name if column == "name" else row[column] for column in columns]
    con.execute(f"INSERT INTO event ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})", values)


def set_event_total(con: sqlite3.Connection, event_id: int, delta: str) -> None:
    con.execute("UPDATE event SET totalamount = ? WHERE id = ?", (money(total_of(con, event_id), delta), event_id))


def set_event_notes(con: sqlite3.Connection, event_id: int, notes: str) -> None:
    con.execute("UPDATE event SET notes = ? WHERE id = ?", (notes, event_id))


def delete_event(con: sqlite3.Connection, event_id: int) -> None:
    con.execute("DELETE FROM payment WHERE eventid = ?", (event_id,))
    con.execute("DELETE FROM event WHERE id = ?", (event_id,))


def shift_payment(con: sqlite3.Connection, payment_id: int, delta: str) -> None:
    current = con.execute("SELECT sum FROM payment WHERE id = ?", (payment_id,)).fetchone()[0]
    con.execute("UPDATE payment SET sum = ? WHERE id = ?", (money(current, delta), payment_id))


def build_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "01_merge_additions", "Оба добавили разные оплаты и новые платежи",
            "оплата на полную сумму платежа A; новый платёж «ТЕСТ: мой новый платёж»",
            "оплата на полную сумму платежа B; новый платёж «ТЕСТ: чужой новый платёж»",
            "merge", "автослияние; окно «Пока вы работали…», предупреждений нет; ваш платёж и оплата получат новые номера",
            lambda c, p: (add_full_payment(c, p.open_a), add_event(c, p.open_a, "ТЕСТ: мой новый платёж")),
            lambda c, p: (add_full_payment(c, p.open_b), add_event(c, p.open_a, "ТЕСТ: чужой новый платёж"))),
        Scenario(
            "02_merge_different_columns", "Разные поля одного платежа",
            "изменены заметки платежа C",
            "изменена сумма платежа C (+100.00)",
            "merge", "автослияние; у платежа C и ваша заметка, и чужая сумма",
            lambda c, p: set_event_notes(c, p.paid_a, "ТЕСТ: моя заметка"),
            lambda c, p: set_event_total(c, p.paid_a, "100.00")),
        Scenario(
            "03_merge_duplicate_payment", "Одна и та же оплата внесена обоими",
            "оплата на полную сумму платежа A",
            "такая же оплата (та же дата и сумма) платежа A",
            "merge", "автослияние с блоком «Проверьте»: возможный дубль оплаты и оплачено больше суммы платежа",
            lambda c, p: add_full_payment(c, p.open_a),
            lambda c, p: add_full_payment(c, p.open_a),
            ("duplicate_payments", "overpaid_events")),
        Scenario(
            "04_merge_duplicate_event", "Одинаковый новый платёж у обоих",
            "новый платёж «ТЕСТ: одинаковый платёж»",
            "тот же новый платёж «ТЕСТ: одинаковый платёж»",
            "merge", "автослияние с предупреждением: возможный дубль платежа; в таблице будет два одинаковых платежа",
            lambda c, p: add_event(c, p.open_a, "ТЕСТ: одинаковый платёж"),
            lambda c, p: add_event(c, p.open_a, "ТЕСТ: одинаковый платёж"),
            ("duplicate_events",)),
        Scenario(
            "05_conflict_same_amount", "Сумма одного платежа изменена по-разному",
            "сумма платежа A +50.00",
            "сумма платежа A +70.00",
            "conflict", "конфликт; причина «сумма — у вас …, в общей базе …»",
            lambda c, p: set_event_total(c, p.open_a, "50.00"),
            lambda c, p: set_event_total(c, p.open_a, "70.00")),
        Scenario(
            "06_conflict_edit_vs_delete", "Я изменил платёж, другой его удалил",
            "заметка платежа D изменена",
            "платёж D удалён вместе с оплатами",
            "conflict", "конфликт; причина «изменено у вас, удалено в общей базе»",
            lambda c, p: set_event_notes(c, p.paid_b, "ТЕСТ: правка удалённого платежа"),
            lambda c, p: delete_event(c, p.paid_b)),
        Scenario(
            "07_conflict_delete_vs_payment", "Я удалил платёж, другой добавил к нему оплату",
            "платёж C удалён вместе с оплатами",
            "к платежу C добавлена оплата 1.00",
            "conflict", "конфликт; причина «платеж удалён у вас, а в общей базе к нему есть оплата»",
            lambda c, p: delete_event(c, p.paid_a),
            lambda c, p: add_payment(c, p.paid_a, "1.00")),
        Scenario(
            "08_conflict_payment_to_deleted", "Я добавил оплату к платежу, который другой удалил",
            "оплата на полную сумму платежа A",
            "платёж A удалён",
            "conflict", "конфликт; причина «платеж удалён в общей базе»",
            lambda c, p: add_full_payment(c, p.open_a),
            lambda c, p: delete_event(c, p.open_a)),
        Scenario(
            "09_conflict_other_table", "Я менял не только платежи и оплаты",
            "добавлен контрагент «ТЕСТ: контрагент» и оплата платежа A",
            "новый платёж «ТЕСТ: чужой платёж»",
            "conflict", "конфликт; причина «Вы изменили также: контрагенты» (автослияние таблицу контрагентов не трогает)",
            lambda c, p: (c.execute("INSERT INTO contractor (name) VALUES ('ТЕСТ: контрагент')"), add_full_payment(c, p.open_a)),
            lambda c, p: add_event(c, p.open_a, "ТЕСТ: чужой платёж")),
        Scenario(
            "10_conflict_payment_sum", "Сумма одной оплаты изменена по-разному",
            "сумма оплаты платежа C +1.00",
            "сумма той же оплаты +2.00",
            "conflict", "конфликт; причина «сумма — у вас …, в общей базе …» по оплате",
            lambda c, p: shift_payment(c, p.payment_a, "1.00"),
            lambda c, p: shift_payment(c, p.payment_a, "2.00")),
    ]


def pick(con: sqlite3.Connection) -> Picks:
    open_events = [row[0] for row in con.execute(
        "SELECT id FROM event WHERE hidden = 0 AND CAST(totalamount AS REAL) > 0 "
        "AND id NOT IN (SELECT eventid FROM payment WHERE eventid IS NOT NULL) ORDER BY id DESC LIMIT 2")]
    paid_events = [row for row in con.execute(
        "SELECT e.id, MAX(p.id) FROM event e JOIN payment p ON p.eventid = e.id "
        "WHERE e.hidden = 0 GROUP BY e.id HAVING COUNT(*) = 1 ORDER BY e.id DESC LIMIT 2")]
    if len(open_events) < 2 or len(paid_events) < 2:
        raise SystemExit("В базе не хватает платежей для сценариев: нужны два без оплат и два с одной оплатой")
    return Picks(open_events[0], open_events[1], paid_events[0][0], paid_events[1][0], paid_events[0][1])


def set_meta(con: sqlite3.Connection, **values: str) -> None:
    for key, value in values.items():
        con.execute("UPDATE meta SET value = ? WHERE key = ?", (value, key))


def meta_value(path: Path, key: str) -> str:
    con = sqlite3.connect(path)
    try:
        return con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()[0]
    finally:
        con.close()


def make_variant(base_file: Path, target: Path, edits: Callable[[sqlite3.Connection, Picks], None], picks: Picks,
                 sync_token: str | None, reset_counter: bool) -> None:
    shutil.copyfile(base_file, target)
    con = sqlite3.connect(target)
    edits(con, picks)
    if sync_token is not None:
        set_meta(con, sync_token=sync_token)
    if reset_counter:
        set_meta(con, change_counter="0")
    con.commit()
    con.close()


def describe_event(con: sqlite3.Connection, event_id: int) -> str:
    receiver, name, amount = con.execute("SELECT receiver, name, totalamount FROM event WHERE id = ?", (event_id,)).fetchone()
    return f"№{event_id} «{receiver} — {name}», сумма {amount}"


def write_readme(scenarios: list[Scenario], picks_text: str) -> None:
    lines = ["# Сценарии конфликтов синхронизации", "",
             "Файлы созданы `tools/make_conflict_scenarios.py` из копии вашей базы. Это тестовые данные, не загружайте их в рабочую "
             "общую базу и не отправляйте на рабочий Яндекс.Диск. После проверки папку можно удалить.", "",
             "Платежи в описаниях:", picks_text, "",
             "В каждой папке сценария:",
             "- `db.db` положить как `data/db/db.db` (ваша локальная база с правками);",
             "- `base.db` положить как `data/sync/base.db` (копия, какой база была при последней синхронизации);",
             "- `master.db` и `master.json` положить на сервер под этими же именами (общая база с чужими правками);",
             "- `описание.txt` что правили вы и другой пользователь и чего ждать.", "",
             "| Сценарий | Ваши правки | Чужие правки | Ожидается |", "|---|---|---|---|"]
    for scenario in scenarios:
        lines.append(f"| {scenario.slug} | {scenario.local_text} | {scenario.master_text} | {scenario.expected_text} |")
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Создание пар баз для ручной проверки конфликтов синхронизации")
    parser.add_argument("--source", default=db_path(), help="база, с которой делаются копии (по умолчанию data/db/db.db)")
    args = parser.parse_args()
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir()
    db_uuid = uuid.uuid4().hex
    scenarios = build_scenarios()
    manifest: list[dict] = []
    with tempfile.TemporaryDirectory(dir=PROJECT_DIR) as temp:
        clean = Path(temp) / "clean.db"
        source = sqlite3.connect(f"file:{Path(args.source).as_posix()}?mode=ro", uri=True)
        target = sqlite3.connect(clean)
        source.backup(target)
        source.close()
        picks = pick(target)
        set_meta(target, db_uuid=db_uuid, change_counter="0")
        picks_text = "\n".join(f"- {label}: {describe_event(target, event_id)}" for label, event_id in (
            ("A (без оплат)", picks.open_a), ("B (без оплат)", picks.open_b),
            ("C (одна оплата)", picks.paid_a), ("D (одна оплата)", picks.paid_b)))
        target.commit()
        target.close()
        for scenario in scenarios:
            folder = OUTPUT_DIR / scenario.slug
            folder.mkdir()
            base_token, master_token = uuid.uuid4().hex, uuid.uuid4().hex
            make_variant(clean, folder / "base.db", lambda c, p: None, picks, base_token, True)
            make_variant(clean, folder / "db.db", scenario.local, picks, base_token, False)
            make_variant(clean, folder / "master.db", scenario.master, picks, master_token, True)
            info = MasterInfo(db_uuid, master_token, int(meta_value(clean, "db_version")), "Тестовый пользователь", "TEST-PC",
                              datetime.now().isoformat(timespec="seconds"), APP_VERSION)
            (folder / "master.json").write_text(info.to_json(), encoding="utf-8")
            (folder / "описание.txt").write_text(
                f"{scenario.title}\n\nУ вас: {scenario.local_text}\nУ другого пользователя: {scenario.master_text}\n\n"
                f"Ожидается: {scenario.expected_text}\n", encoding="utf-8")
            manifest.append({"slug": scenario.slug, "expected": scenario.expected, "warnings": list(scenario.warnings)})
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(scenarios, picks_text)
    print(f"Создано сценариев: {len(scenarios)}, папка {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
