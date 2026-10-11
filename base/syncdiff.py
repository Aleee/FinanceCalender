import re
from dataclasses import dataclass, field
from typing import Any

Row = dict[str, Any]

DETAILED_TABLES = ("event", "payment")
IGNORED_COLUMNS = ("receivernocase",)
COMPANION_COLUMNS = {"receiver": "receivernocase"}
DERIVED_COLUMNS = ("event_title",)
MAX_LISTED_ROWS = 30
MAX_VALUE_LENGTH = 60

COLUMN_TITLES: dict[str, str] = {
    "receiver": "получатель", "name": "название", "totalamount": "сумма", "duedate": "срок", "descr": "описание",
    "notes": "заметки", "category": "категория", "subcategory": "подкатегория", "nds": "НДС", "paymenttype": "вид платежа",
    "responsible": "ответственный", "featured": "избранное", "hidden": "скрыто", "type": "тип",
    "contractdocument_id": "документ договора", "createdate": "дата создания", "paymentdate": "дата платежа", "sum": "сумма",
    "eventid": "событие",
}

TABLE_TITLES: dict[str, str] = {
    "contractor": "контрагенты", "contract": "договоры", "contractdocument": "документы договоров",
    "contractpaymentterm": "сроки оплаты по договорам", "contractsavedvalues": "сохранённые значения договоров",
    "contractdocumenttype": "типы документов", "department": "отделы", "position": "должности", "personal": "сотрудники",
    "finplan": "финансовый план", "fulfillmentdata": "данные об исполнении", "meta": "настройки",
}


@dataclass
class TableDiff:
    added: list[Row] = field(default_factory=list)
    removed: list[Row] = field(default_factory=list)
    changed: list[tuple[Row, Row]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


@dataclass
class DbDiff:
    tables: dict[str, TableDiff] = field(default_factory=dict)
    other_tables: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return all(table.is_empty for table in self.tables.values()) and not self.other_tables

    def added_ids(self, table: str) -> list[int]:
        return [row["id"] for row in self.tables[table].added] if table in self.tables else []


@dataclass
class MergeWarnings:
    duplicate_events: list[Row] = field(default_factory=list)
    duplicate_payments: list[Row] = field(default_factory=list)
    overpaid_events: list[Row] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.duplicate_events or self.duplicate_payments or self.overpaid_events)


def format_value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    text: str = str(value).replace("\n", " ")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text = f"{text[8:]}.{text[5:7]}.{text[:4]}"
    return text if len(text) <= MAX_VALUE_LENGTH else text[:MAX_VALUE_LENGTH] + "…"


def describe_row(table: str, row: Row) -> str:
    if table == "event":
        return f"{format_value(row['receiver'])} — {format_value(row['name'])}, {format_value(row['totalamount'])}, срок {format_value(row['duedate'])}"
    return f"{format_value(row.get('event_title'))}: {format_value(row['sum'])} от {format_value(row['paymentdate'])}"


def describe_changes(old_row: Row, new_row: Row) -> str:
    return "; ".join(f"{COLUMN_TITLES.get(column, column)}: {format_value(old_row[column])} → {format_value(new_row[column])}"
                     for column in new_row if column not in DERIVED_COLUMNS and new_row[column] != old_row[column])


def table_summary(table_diff: TableDiff) -> str:
    parts: list[str] = []
    for count, title in ((len(table_diff.added), "добавлено"), (len(table_diff.changed), "изменено"),
                         (len(table_diff.removed), "удалено")):
        if count:
            parts.append(f"{title} {count}")
    return ", ".join(parts)


def diff_summary(diff: DbDiff) -> str:
    lines: list[str] = []
    for table, title in (("event", "События"), ("payment", "Платежи")):
        table_diff: TableDiff | None = diff.tables.get(table)
        if table_diff is not None and not table_diff.is_empty:
            lines.append(f"{title}: {table_summary(table_diff)}")
    if diff.other_tables:
        lines.append("Изменены также: " + ", ".join(TABLE_TITLES.get(table, table) for table in diff.other_tables))
    return "\n".join(lines)


def list_rows(lines: list[str], prefix: str, rows: list[str]) -> None:
    lines.extend(f"  {prefix} {row}" for row in rows[:MAX_LISTED_ROWS])
    if len(rows) > MAX_LISTED_ROWS:
        lines.append(f"  … и ещё {len(rows) - MAX_LISTED_ROWS}")


@dataclass
class MergePlan:
    updates: dict[str, list[tuple[int, list[str]]]] = field(default_factory=dict)
    deletes: dict[str, list[int]] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)


def changed_columns(old_row: Row, new_row: Row) -> list[str]:
    return [column for column in new_row if column not in DERIVED_COLUMNS and new_row[column] != old_row[column]]


def plan_merge(my_changes: DbDiff, their_changes: DbDiff) -> MergePlan:
    plan = MergePlan()
    if my_changes.other_tables:
        plan.conflicts.append("Вы изменили также: " + ", ".join(TABLE_TITLES.get(table, table) for table in my_changes.other_tables))
    empty = TableDiff()
    for table in DETAILED_TABLES:
        mine, theirs = my_changes.tables.get(table, empty), their_changes.tables.get(table, empty)
        their_changed = {new_row["id"]: (old_row, new_row) for old_row, new_row in theirs.changed}
        their_removed = {row["id"] for row in theirs.removed}
        plan.updates[table], plan.deletes[table] = [], []
        for old_row, new_row in mine.changed:
            row_id, title = new_row["id"], describe_row(table, new_row)
            columns = changed_columns(old_row, new_row)
            if row_id in their_removed:
                plan.conflicts.append(f"{title}: изменено у вас, удалено в общей базе")
                continue
            if row_id in their_changed:
                their_old, their_new = their_changed[row_id]
                their_columns = changed_columns(their_old, their_new)
                plan.conflicts.extend(
                    f"{title}: {COLUMN_TITLES.get(column, column)} — у вас {format_value(new_row[column])}, "
                    f"в общей базе {format_value(their_new[column])}"
                    for column in columns if column in their_columns and their_new[column] != new_row[column])
                columns = [column for column in columns if column not in their_columns]
            columns += [COMPANION_COLUMNS[column] for column in columns if column in COMPANION_COLUMNS and table == "event"]
            if columns:
                plan.updates[table].append((row_id, columns))
        for row in mine.removed:
            if row["id"] in their_removed:
                continue
            if row["id"] in their_changed:
                plan.conflicts.append(f"{describe_row(table, row)}: удалено у вас, изменено в общей базе")
            else:
                plan.deletes[table].append(row["id"])
    their_payments = their_changes.tables.get("payment", empty).added + [new_row for _, new_row in their_changes.tables.get("payment", empty).changed]
    for row in their_payments:
        if row["eventid"] in plan.deletes["event"]:
            plan.conflicts.append(f"{describe_row('payment', row)}: событие удалено у вас, а в общей базе к нему есть платёж")
    their_removed_events = {row["id"] for row in their_changes.tables.get("event", empty).removed}
    my_payments = my_changes.tables.get("payment", empty).added + [new_row for _, new_row in my_changes.tables.get("payment", empty).changed]
    for row in my_payments:
        if row["eventid"] in their_removed_events:
            plan.conflicts.append(f"{describe_row('payment', row)}: событие удалено в общей базе")
    return plan


def format_warnings(warnings: MergeWarnings) -> list[str]:
    lines: list[str] = []
    lines.extend(f"Возможный дубль события: {describe_row('event', row)}" for row in warnings.duplicate_events)
    lines.extend(f"Возможный дубль платежа: {describe_row('payment', row)}" for row in warnings.duplicate_payments)
    lines.extend(f"Оплачено больше суммы события: {describe_row('event', row)}, оплачено {format_value(row['paid'])}"
                 for row in warnings.overpaid_events)
    return lines


def format_diff(diff: DbDiff) -> str:
    lines: list[str] = []
    for table, title in (("event", "События"), ("payment", "Платежи")):
        table_diff: TableDiff | None = diff.tables.get(table)
        if table_diff is None or table_diff.is_empty:
            continue
        lines.append(f"{title}: {table_summary(table_diff)}")
        list_rows(lines, "+", [describe_row(table, row) for row in table_diff.added])
        list_rows(lines, "~", [f"{describe_row(table, new_row)} ({describe_changes(old_row, new_row)})"
                               for old_row, new_row in table_diff.changed])
        list_rows(lines, "−", [describe_row(table, row) for row in table_diff.removed])
    for table, (only_new, only_old) in diff.other_tables.items():
        lines.append(f"{TABLE_TITLES.get(table, table).capitalize()}: новых или изменённых строк {only_new}, исчезнувших или прежних {only_old}")
    return "\n".join(lines)
