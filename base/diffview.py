from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from base.formatting import dec_strcommaspace, str_decimal
from base.syncdiff import DETAILED_TABLES, DbDiff, Row, ROW_TITLES, TableDiff, describe_row, field_changes, format_value, table_key, changed_columns

ADDED, CHANGED, REMOVED = "added", "changed", "removed"
ACTIONS = (ADDED, CHANGED, REMOVED)
ACTION_TITLES = {ADDED: "Добавлено", CHANGED: "Изменено", REMOVED: "Удалено"}
SECTION_TITLES = {"contractor": "Контрагенты", "contract": "Договоры", "contractdocument": "Документы договоров",
                  "contractpaymentterm": "Сроки оплаты документов", "contractsavedvalues": "Сохранённые значения документов",
                  "event": "Платежи", "payment": "Оплаты", "finplan": "Финансовый план", "fulfillmentdata": "Данные об исполнении"}
AMOUNT_COLUMNS = {"event": "totalamount", "payment": "sum"}
DATE_COLUMNS = {"event": "duedate", "payment": "paymentdate"}
SUMMED_TABLES = tuple(AMOUNT_COLUMNS)
PAID_KIND = "Платеж + оплата"


@dataclass
class DiffEntry:
    action: str
    table: str
    title: str
    amount: Decimal | None = None
    amount_text: str = ""
    date_text: str = ""
    date_sort: str = ""
    amount_changed: bool = False
    date_changed: bool = False
    changes: list[tuple[str, str, str]] = field(default_factory=list)
    author: str = ""
    changed_at: datetime | None = None
    event_id: int | None = None
    parent_id: int | None = None
    merged: list["DiffEntry"] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return PAID_KIND if self.merged else ROW_TITLES[self.table]

    @property
    def tables(self) -> set[str]:
        return {self.table} | {entry.table for entry in self.merged}

    @property
    def changes_text(self) -> str:
        return "; ".join(f"{title}: {old} → {new}" for title, old, new in self.changes)

    @property
    def details(self) -> str:
        if not self.merged:
            return self.changes_text
        return f"Оплачен полностью {max(self.merged, key=lambda entry: entry.date_sort).date_text}"

    @property
    def details_tooltip(self) -> str:
        if self.merged:
            return "\n".join(f"Оплата {entry.amount_text} от {entry.date_text}" for entry in self.merged)
        return "\n".join(f"{title}: {old} → {new}" for title, old, new in self.changes)


def entry_title(table: str, row: Row) -> str:
    if table == "event":
        return f"{format_value(row['receiver'])} — {format_value(row['name'])}"
    if table == "payment":
        return format_value(row.get("event_title"))
    return describe_row(table, row)


def parse_time(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_time(moment: datetime | None, now: datetime | None = None) -> str:
    if moment is None:
        return ""
    year = (now or datetime.now()).year
    return moment.strftime("%d.%m %H:%M" if moment.year == year else "%d.%m.%Y %H:%M")


def make_entry(action: str, table: str, row: Row, old_row: Row | None, table_diff: TableDiff, removed_events: set) -> DiffEntry:
    entry = DiffEntry(action, table, entry_title(table, row))
    amount_column, date_column = AMOUNT_COLUMNS.get(table), DATE_COLUMNS.get(table)
    if amount_column is not None:
        entry.amount = str_decimal(str(row[amount_column])) if row[amount_column] not in (None, "") else None
        entry.amount_text = format_value(row[amount_column], amount_column)
    if date_column is not None:
        entry.date_text = format_value(row[date_column])
        entry.date_sort = str(row[date_column] or "")
    if old_row is not None:
        entry.changes = field_changes(old_row, row)
        changed = changed_columns(old_row, row)
        entry.amount_changed, entry.date_changed = amount_column in changed, date_column in changed
    key = table_key(table)
    if key in row and row[key] in table_diff.origins:
        changed_at, entry.author = table_diff.origins[row[key]]
        entry.changed_at = parse_time(changed_at)
    entry.parent_id = row["id"] if table == "event" else row.get("eventid") if table == "payment" else None
    if action != REMOVED or table == "payment":
        entry.event_id = None if entry.parent_id in removed_events else entry.parent_id
    return entry


def build_entries(diff: DbDiff) -> list[DiffEntry]:
    event_diff = diff.tables.get("event")
    removed_events = {row["id"] for row in event_diff.removed} if event_diff is not None else set()
    entries: list[DiffEntry] = []
    for table in DETAILED_TABLES:
        table_diff = diff.tables.get(table)
        if table_diff is None:
            continue
        entries.extend(make_entry(ADDED, table, row, None, table_diff, removed_events) for row in table_diff.added)
        entries.extend(make_entry(CHANGED, table, new_row, old_row, table_diff, removed_events) for old_row, new_row in table_diff.changed)
        entries.extend(make_entry(REMOVED, table, row, None, table_diff, removed_events) for row in table_diff.removed)
    return merge_paid_entries(entries)


def merge_paid_entries(entries: list[DiffEntry]) -> list[DiffEntry]:
    payments: dict[tuple[str, int | None], list[DiffEntry]] = defaultdict(list)
    for entry in entries:
        if entry.table == "payment" and entry.action != CHANGED:
            payments[(entry.action, entry.parent_id)].append(entry)
    absorbed: set[int] = set()
    for entry in entries:
        paid = payments.get((entry.action, entry.parent_id)) if entry.table == "event" and entry.action != CHANGED else None
        if paid and entry.amount is not None and amount_sum(paid) == entry.amount:
            entry.merged = paid
            absorbed.update(id(payment) for payment in paid)
    return [entry for entry in entries if id(entry) not in absorbed]


def amount_sum(entries: list[DiffEntry]) -> Decimal:
    return sum((entry.amount for entry in entries if entry.amount is not None), Decimal(0))


def summary_lines(entries: list[DiffEntry]) -> list[str]:
    lines: list[str] = []
    flat_entries = [part for entry in entries for part in (entry, *entry.merged)]
    for table in DETAILED_TABLES:
        table_entries = [entry for entry in flat_entries if entry.table == table]
        parts: list[str] = []
        for action in ACTIONS:
            action_entries = [entry for entry in table_entries if entry.action == action]
            if not action_entries:
                continue
            part = f"{ACTION_TITLES[action].lower()} {len(action_entries)}"
            if table in SUMMED_TABLES and action != CHANGED:
                part += f" на {dec_strcommaspace(amount_sum(action_entries))}"
            parts.append(part)
        if parts:
            lines.append(f"{SECTION_TITLES[table]}: {', '.join(parts)}")
    return lines
