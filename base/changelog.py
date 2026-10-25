import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from base.syncdiff import BOOL_COLUMNS, column_title, format_value

INSERT, UPDATE, DELETE = "insert", "update", "delete"
EVENT_TABLE, PAYMENT_TABLE = "event", "payment"
SNAPSHOT_SKIPPED_COLUMNS = ("id", "eventid", "type")
UNSET_COLUMNS = ("subcategory", "contractdocument_id")
EVENT_TITLES = {INSERT: "Платеж добавлен", UPDATE: "Платеж изменён", DELETE: "Платеж удалён"}
PAYMENT_ACTION_TITLES = {INSERT: "добавлена", UPDATE: "изменена", DELETE: "удалена"}

ValueResolvers = dict[str, Callable[[str], str | None]]
PaymentInfo = dict[int, tuple[str, str]]


@dataclass
class ChangeRecord:
    id: int
    changed_at: str
    author: str
    machine: str
    table: str
    record_id: int
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None

    @property
    def operation_key(self) -> tuple:
        return self.changed_at, self.author, self.machine, self.table, self.record_id, self.action


@dataclass
class ChangeOperation:
    time: datetime
    author: str
    machine: str
    table: str
    action: str
    title: str
    fields: list[tuple[str, str, str]] = field(default_factory=list)


def is_unset(column: str, value: object) -> bool:
    return column in UNSET_COLUMNS and str(value) == "0"


def display_value(column: str, value: object, resolvers: ValueResolvers) -> str:
    if is_unset(column, value):
        return "не задан"
    resolve = resolvers.get(column)
    name = resolve(str(value)) if resolve is not None and value not in (None, "") else None
    return format_value(value if name is None else name, column)


def snapshot_values(text: str | None) -> dict[str, object]:
    try:
        values = json.loads(text or "{}")
    except ValueError:
        return {}
    return values if isinstance(values, dict) else {}


def payment_snapshot(record: ChangeRecord) -> tuple[str, str]:
    values = snapshot_values(record.new_value or record.old_value)
    return str(values.get("paymentdate") or ""), str(values.get("sum") or "")


def known_payments(records: list[ChangeRecord], current: PaymentInfo) -> PaymentInfo:
    known: PaymentInfo = {record.record_id: payment_snapshot(record) for record in records
                          if record.table == PAYMENT_TABLE and record.action in (INSERT, DELETE)}
    known.update(current)
    return known


def payment_label(payment_id: int, known: PaymentInfo) -> str:
    if payment_id not in known:
        return f"№{payment_id}"
    payment_date, amount = known[payment_id]
    return f"{format_value(amount, 'sum')} от {format_value(payment_date)}"


def operation_title(record: ChangeRecord, known: PaymentInfo) -> str:
    if record.table == EVENT_TABLE:
        return EVENT_TITLES[record.action]
    if record.action != UPDATE:
        known = {record.record_id: payment_snapshot(record)}
    return f"Оплата {payment_label(record.record_id, known)} {PAYMENT_ACTION_TITLES[record.action]}"


def snapshot_fields(record: ChangeRecord, resolvers: ValueResolvers) -> list[tuple[str, str, str]]:
    is_insert = record.action == INSERT
    fields: list[tuple[str, str, str]] = []
    for column, value in snapshot_values(record.new_value if is_insert else record.old_value).items():
        if (column in SNAPSHOT_SKIPPED_COLUMNS or value in (None, "") or is_unset(column, value)
                or (column in BOOL_COLUMNS and str(value) in ("0", "False"))):
            continue
        shown = display_value(column, value, resolvers)
        fields.append((column_title(column), "—" if is_insert else shown, shown if is_insert else "—"))
    return fields


def build_operations(records: list[ChangeRecord], current_payments: PaymentInfo,
                     resolvers: ValueResolvers | None = None) -> list[ChangeOperation]:
    resolvers = resolvers or {}
    known = known_payments(records, current_payments)
    operations: list[ChangeOperation] = []
    previous_key: tuple | None = None
    for record in sorted(records, key=lambda item: item.id):
        if record.operation_key != previous_key:
            operations.append(ChangeOperation(datetime.fromisoformat(record.changed_at), record.author, record.machine,
                                              record.table, record.action, operation_title(record, known)))
            previous_key = record.operation_key
        if record.action == UPDATE:
            column = record.field or ""
            operations[-1].fields.append((column_title(column), display_value(column, record.old_value, resolvers),
                                          display_value(column, record.new_value, resolvers)))
        else:
            operations[-1].fields.extend(snapshot_fields(record, resolvers))
    operations.reverse()
    return operations
