import re
from dataclasses import dataclass, field
from typing import Any

from base.formatting import dec_strcommaspace, str_decimal
from base.liability import CATEGORY_NAMES, PAYMENTTYPE_NAMES

Row = dict[str, Any]

DETAILED_TABLES = ("event", "payment")
TABLE_DERIVED_COLUMNS = {"event": ("responsible_name",), "payment": ("event_title",)}
DERIVED_COLUMNS = ("responsible_name", "event_title")
NAME_COLUMNS = {"responsible": "responsible_name"}
AMOUNT_COLUMNS = ("totalamount", "sum", "paid")
BOOL_COLUMNS = ("featured", "hidden")
VALUE_NAMES = {"category": CATEGORY_NAMES, "paymenttype": PAYMENTTYPE_NAMES}
ROW_TITLES = {"event": "Платеж", "payment": "Оплата"}
MAX_VALUE_LENGTH = 60

COLUMN_TITLES: dict[str, str] = {
    "receiver": "получатель", "name": "наименование", "totalamount": "сумма", "duedate": "срок оплаты", "descr": "основание",
    "notes": "заметки", "category": "категория", "subcategory": "подкатегория", "nds": "НДС", "paymenttype": "вид платежа",
    "responsible": "ответственный", "featured": "на контроле", "hidden": "скрытый платеж", "type": "тип",
    "contractdocument_id": "документ договора", "createdate": "дата создания", "paymentdate": "дата оплаты", "sum": "сумма",
    "eventid": "платеж",
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


def format_value(value: Any, column: str = "") -> str:
    if value is None or value == "":
        return "—"
    if column in BOOL_COLUMNS:
        return "нет" if str(value) in ("0", "False") else "да"
    if column in AMOUNT_COLUMNS:
        amount = str_decimal(str(value))
        if amount is not None:
            return dec_strcommaspace(amount)
    names = VALUE_NAMES.get(column)
    if names is not None and str(value).isdigit() and int(value) in names:
        return " ".join(names[int(value)].split())
    if column == "nds":
        return f"{value}%"
    text: str = str(value).replace("\n", " ")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text = f"{text[8:]}.{text[5:7]}.{text[:4]}"
    return text if len(text) <= MAX_VALUE_LENGTH else text[:MAX_VALUE_LENGTH] + "…"


def column_title(column: str) -> str:
    title: str = COLUMN_TITLES.get(column, column)
    return title[:1].upper() + title[1:]


def display_value(row: Row, column: str) -> str:
    name = row.get(NAME_COLUMNS.get(column, ""))
    return format_value(row[column] if name is None else name, column)


def describe_row(table: str, row: Row) -> str:
    if table == "event":
        return f"{format_value(row['receiver'])} — {format_value(row['name'])}, {format_value(row['totalamount'], 'totalamount')}, срок {format_value(row['duedate'])}"
    return f"{format_value(row.get('event_title'))}: {format_value(row['sum'], 'sum')} от {format_value(row['paymentdate'])}"


def describe_other_table(table: str, counts: tuple[int, int]) -> str:
    only_new, only_old = counts
    return f"{TABLE_TITLES.get(table, table).capitalize()}: новых или изменённых строк {only_new}, исчезнувших или прежних {only_old}"


def changed_columns(old_row: Row, new_row: Row) -> list[str]:
    return [column for column in new_row if column not in DERIVED_COLUMNS and new_row[column] != old_row[column]]


def field_changes(old_row: Row, new_row: Row) -> list[tuple[str, str, str]]:
    return [(column_title(column), display_value(old_row, column), display_value(new_row, column))
            for column in changed_columns(old_row, new_row)]


@dataclass
class Conflict:
    title: str
    topic: str
    mine: str
    theirs: str


@dataclass
class MergePlan:
    updates: dict[str, list[tuple[int, list[str]]]] = field(default_factory=dict)
    deletes: dict[str, list[int]] = field(default_factory=dict)
    conflicts: list[Conflict] = field(default_factory=list)


def plan_merge(my_changes: DbDiff, their_changes: DbDiff) -> MergePlan:
    plan = MergePlan()
    if my_changes.other_tables:
        plan.conflicts.append(Conflict("Другие данные", "Изменены также", ", ".join(TABLE_TITLES.get(table, table) for table in my_changes.other_tables), ""))
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
                plan.conflicts.append(Conflict(title, ROW_TITLES[table], "правка", "удаление"))
                continue
            if row_id in their_changed:
                their_old, their_new = their_changed[row_id]
                their_columns = changed_columns(their_old, their_new)
                plan.conflicts.extend(
                    Conflict(title, column_title(column), display_value(new_row, column), display_value(their_new, column))
                    for column in columns if column in their_columns and their_new[column] != new_row[column])
                columns = [column for column in columns if column not in their_columns]
            if columns:
                plan.updates[table].append((row_id, columns))
        for row in mine.removed:
            if row["id"] in their_removed:
                continue
            if row["id"] in their_changed:
                plan.conflicts.append(Conflict(describe_row(table, row), ROW_TITLES[table], "удаление", "правка"))
            else:
                plan.deletes[table].append(row["id"])
    their_payments = their_changes.tables.get("payment", empty).added + [new_row for _, new_row in their_changes.tables.get("payment", empty).changed]
    for row in their_payments:
        if row["eventid"] in plan.deletes["event"]:
            plan.conflicts.append(Conflict(describe_row("payment", row), ROW_TITLES["payment"], "платеж удалён", "добавлена или изменена"))
    their_removed_events = {row["id"] for row in their_changes.tables.get("event", empty).removed}
    my_payments = my_changes.tables.get("payment", empty).added + [new_row for _, new_row in my_changes.tables.get("payment", empty).changed]
    for row in my_payments:
        if row["eventid"] in their_removed_events:
            plan.conflicts.append(Conflict(describe_row("payment", row), ROW_TITLES["payment"], "добавлена или изменена", "платеж удалён"))
    return plan


def format_warnings(warnings: MergeWarnings) -> list[str]:
    lines: list[str] = []
    lines.extend(f"Возможный дубль платежа: {describe_row('event', row)}" for row in warnings.duplicate_events)
    lines.extend(f"Возможный дубль оплаты: {describe_row('payment', row)}" for row in warnings.duplicate_payments)
    lines.extend(f"Оплачено больше суммы платежа: {describe_row('event', row)}, оплачено {format_value(row['paid'], 'paid')}"
                 for row in warnings.overpaid_events)
    return lines
