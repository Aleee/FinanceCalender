import re
from dataclasses import dataclass, field
from typing import Any

from base.formatting import dec_strcommaspace, str_decimal
from base.liability import CATEGORY_NAMES, PAYMENTTYPE_NAMES
from gui.finplanmodel import FinPlanTableModel

Row = dict[str, Any]

DETAILED_TABLES = ("contractor", "contract", "contractdocument", "contractpaymentterm", "contractsavedvalues", "event", "payment",
                   "finplan", "fulfillmentdata")
KEY_COLUMNS = {"finplan": ("year", "category"), "fulfillmentdata": ("startdate", "enddate")}
TABLE_KEYS = {"contractpaymentterm": "document_id", "contractsavedvalues": "contractdocumentid", **dict.fromkeys(KEY_COLUMNS, "rowkey")}
REFERENCES = {
    "contract": {"contractor_id": "contractor"},
    "contractdocument": {"contract_id": "contract", "position_id": "position"},
    "contractpaymentterm": {"document_id": "contractdocument"},
    "contractsavedvalues": {"contractdocumentid": "contractdocument"},
    "event": {"contractdocument_id": "contractdocument"},
    "payment": {"eventid": "event"},
}
DOCUMENT_DERIVED_COLUMNS = ("contractor_name", "contract_number", "contract_date", "document_title")
TABLE_DERIVED_COLUMNS = {
    "contract": ("contractor_name",),
    "contractdocument": DOCUMENT_DERIVED_COLUMNS[:3],
    "contractpaymentterm": DOCUMENT_DERIVED_COLUMNS,
    "contractsavedvalues": DOCUMENT_DERIVED_COLUMNS + ("responsible_name",),
    "event": ("responsible_name",),
    "payment": ("event_title",),
    "finplan": ("rowkey",),
    "fulfillmentdata": ("rowkey",),
}
DERIVED_COLUMNS = tuple({column for columns in TABLE_DERIVED_COLUMNS.values() for column in columns})
NAME_COLUMNS = {"responsible": "responsible_name", "contractor_id": "contractor_name"}
MONTH_COLUMNS = {f"m{number}": name.lower() for number, name in enumerate(FinPlanTableModel.HORIZONTAL_HEADER_LABELS[1:], 1)}
CATEGORY_COLUMNS = {str(category): definition.title for category, definition in FinPlanTableModel.FINPLAN_STRUCTURE.items()}
AMOUNT_COLUMNS = ("totalamount", "sum", "paid", *MONTH_COLUMNS, *CATEGORY_COLUMNS)
BOOL_COLUMNS = ("featured", "hidden", "has_calendar_condition")
VALUE_NAMES = {"category": CATEGORY_NAMES, "paymenttype": PAYMENTTYPE_NAMES}
ROW_TITLES = {"contractor": "Контрагент", "contract": "Договор", "contractdocument": "Документ", "contractpaymentterm": "Сроки оплаты",
              "contractsavedvalues": "Сохранённые значения", "event": "Платеж", "payment": "Оплата", "finplan": "Финплан",
              "fulfillmentdata": "Исполнение"}
MAX_VALUE_LENGTH = 60

COLUMN_TITLES: dict[str, str] = {
    "receiver": "получатель", "name": "наименование", "totalamount": "сумма", "duedate": "срок оплаты", "descr": "основание",
    "notes": "заметки", "category": "категория", "subcategory": "подкатегория", "nds": "НДС", "paymenttype": "вид платежа",
    "responsible": "ответственный", "featured": "на контроле", "hidden": "скрытый платеж", "type": "тип",
    "contractdocument_id": "документ договора", "createdate": "дата создания", "paymentdate": "дата оплаты", "sum": "сумма",
    "eventid": "платеж", "contractor_id": "контрагент", "contract_id": "договор", "date": "дата", "document_type": "тип документа",
    "document_name": "название документа", "description": "описание", "position_id": "должность", "payment_type": "вид срока оплаты",
    "days_count": "количество дней", "days_type": "вид дней", "has_calendar_condition": "календарное условие",
    "month_day": "число месяца", "month_type": "вид месяца", "year": "год", "startdate": "начало периода", "enddate": "конец периода",
    **MONTH_COLUMNS, **CATEGORY_COLUMNS,
}

TABLE_TITLES: dict[str, str] = {
    "contractor": "контрагенты", "contract": "договоры", "contractdocument": "документы договоров",
    "contractpaymentterm": "сроки оплаты по договорам", "contractsavedvalues": "сохранённые значения договоров",
    "contractdocumenttype": "типы документов", "department": "отделы", "position": "должности", "personal": "сотрудники",
    "finplan": "финансовый план", "fulfillmentdata": "данные об исполнении", "meta": "настройки",
}


def table_key(table: str) -> str:
    return TABLE_KEYS.get(table, "id")


def key_sql(table: str, source: str) -> str:
    columns = KEY_COLUMNS.get(table)
    if columns is None:
        return f'{source}."{table_key(table)}"'
    return " || '/' || ".join(f"COALESCE({source}.\"{column}\", '')" for column in columns)


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
        return [row[table_key(table)] for row in self.tables[table].added] if table in self.tables else []


@dataclass
class MergeWarnings:
    duplicate_contractors: list[Row] = field(default_factory=list)
    duplicate_contracts: list[Row] = field(default_factory=list)
    duplicate_documents: list[Row] = field(default_factory=list)
    duplicate_events: list[Row] = field(default_factory=list)
    duplicate_payments: list[Row] = field(default_factory=list)
    overpaid_events: list[Row] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.duplicate_contractors or self.duplicate_contracts or self.duplicate_documents
                    or self.duplicate_events or self.duplicate_payments or self.overpaid_events)


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


def describe_contract(contractor: Any, number: Any, date: Any) -> str:
    text = f"{format_value(contractor)} — № {number or ''}"
    return f"{text} от {format_value(date)}" if date else text


def describe_document(row: Row, name: Any) -> str:
    return f"{describe_contract(row['contractor_name'], row['contract_number'], row['contract_date'])} — {format_value(name)}"


def describe_row(table: str, row: Row) -> str:
    if table == "contractor":
        return format_value(row["name"])
    if table == "contract":
        return describe_contract(row["contractor_name"], row["name"], row["date"])
    if table == "contractdocument":
        return describe_document(row, row["document_name"])
    if table in ("contractpaymentterm", "contractsavedvalues"):
        return f"{ROW_TITLES[table]}: {describe_document(row, row['document_title'])}"
    if table == "finplan":
        definition = FinPlanTableModel.FINPLAN_STRUCTURE.get(row["category"])
        category = row["category"] if definition is None else f"{definition.row_label} {definition.title}"
        return f"Финплан {row['year']}: {category}"
    if table == "fulfillmentdata":
        return f"Исполнение за {format_value(row['startdate'])} — {format_value(row['enddate'])}"
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
    skip_added: dict[str, list[str]] = field(default_factory=dict)
    conflicts: list[Conflict] = field(default_factory=list)


def plan_merge(my_changes: DbDiff, their_changes: DbDiff) -> MergePlan:
    plan = MergePlan()
    if my_changes.other_tables:
        plan.conflicts.append(Conflict("Другие данные", "Изменены также", ", ".join(TABLE_TITLES.get(table, table) for table in my_changes.other_tables), ""))
    empty = TableDiff()
    for table in DETAILED_TABLES:
        key = table_key(table)
        mine, theirs = my_changes.tables.get(table, empty), their_changes.tables.get(table, empty)
        their_changed = {new_row[key]: (old_row, new_row) for old_row, new_row in theirs.changed}
        their_removed = {row[key] for row in theirs.removed}
        plan.updates[table], plan.deletes[table], plan.skip_added[table] = [], [], []
        if table in KEY_COLUMNS:
            their_added = {row[key]: row for row in theirs.added}
            for row in mine.added:
                if row[key] in their_added:
                    plan.skip_added[table].append(row[key])
                    plan.conflicts.extend(
                        Conflict(describe_row(table, row), column_title(column), display_value(row, column), display_value(their_added[row[key]], column))
                        for column in changed_columns(their_added[row[key]], row))
        if key in REFERENCES.get(table, {}):
            added_by_both = {row[key] for row in theirs.added} - set(my_changes.added_ids(REFERENCES[table][key]))
            plan.conflicts.extend(Conflict(describe_row(table, row), ROW_TITLES[table], "добавлено", "тоже добавлено")
                                  for row in mine.added if row[key] in added_by_both)
        for old_row, new_row in mine.changed:
            row_id, title = new_row[key], describe_row(table, new_row)
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
            if row[key] in their_removed:
                continue
            if row[key] in their_changed:
                plan.conflicts.append(Conflict(describe_row(table, row), ROW_TITLES[table], "удаление", "правка"))
            else:
                plan.deletes[table].append(row[key])
    for child, references in REFERENCES.items():
        for column, parent in references.items():
            if parent not in DETAILED_TABLES:
                continue
            deleted = f"{ROW_TITLES[parent].lower()} удалён"
            removed_parents = {row[table_key(parent)] for row in their_changes.tables.get(parent, empty).removed}
            for row in touched_rows(their_changes, child):
                if row.get(column) in plan.deletes[parent]:
                    plan.conflicts.append(Conflict(describe_row(child, row), ROW_TITLES[child], deleted, "добавлено или изменено"))
            for row in touched_rows(my_changes, child):
                if row.get(column) in removed_parents:
                    plan.conflicts.append(Conflict(describe_row(child, row), ROW_TITLES[child], "добавлено или изменено", deleted))
    return plan


def touched_rows(diff: DbDiff, table: str) -> list[Row]:
    table_diff = diff.tables.get(table, TableDiff())
    return table_diff.added + [new_row for _, new_row in table_diff.changed]


def format_warnings(warnings: MergeWarnings) -> list[str]:
    lines: list[str] = []
    lines.extend(f"Возможный дубль контрагента: {describe_row('contractor', row)}" for row in warnings.duplicate_contractors)
    lines.extend(f"Возможный дубль договора: {describe_row('contract', row)}" for row in warnings.duplicate_contracts)
    lines.extend(f"Возможный дубль документа: {describe_row('contractdocument', row)}" for row in warnings.duplicate_documents)
    lines.extend(f"Возможный дубль платежа: {describe_row('event', row)}" for row in warnings.duplicate_events)
    lines.extend(f"Возможный дубль оплаты: {describe_row('payment', row)}" for row in warnings.duplicate_payments)
    lines.extend(f"Оплачено больше суммы платежа: {describe_row('event', row)}, оплачено {format_value(row['paid'], 'paid')}"
                 for row in warnings.overpaid_events)
    return lines
