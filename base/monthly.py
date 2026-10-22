import json
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from PySide6.QtCore import QDate, QSettings, Qt

from base.contract import DocumentTitle
from base.date import MONTHS_RU
from base.formatting import str_decimal
from base.liability import Col
from base.paymentdate import calculate_payment_date, period_for_due_month

MONTH_WORDS = [name.lower() for name in MONTHS_RU]
MONTH_RE = re.compile(rf"\b({'|'.join(MONTH_WORDS)})\b(?:(\s+)(\d{{4}}))?", re.IGNORECASE)


class MonthlyState(Enum):
    MISSING = 0
    UNPAID = 1
    PAID = 2


@dataclass
class MonthlyEvent:
    event_id: int
    due_date: QDate
    amount: Decimal | None
    is_paid: bool


@dataclass
class MonthlyEntry:
    title: DocumentTitle
    amount: Decimal | None
    event: MonthlyEvent | None = None
    has_saved_values: bool = False
    planned_date: QDate | None = None

    @property
    def state(self) -> MonthlyState:
        if self.event is None:
            return MonthlyState.MISSING
        return MonthlyState.PAID if self.event.is_paid else MonthlyState.UNPAID


@dataclass
class MonthlyTemplate:
    values: dict[Col, Any]
    amount: Decimal | None
    period: QDate
    incurrence_date: QDate
    due_date: QDate | None
    month: QDate | None = None
    last_amount: Decimal | None = None
    name_ambiguous: bool = False


class HiddenMonthly:
    KEY = "Monthly/hidden"
    KEEP_DAYS = 365

    def __init__(self, settings: QSettings | None = None):
        self.settings = settings
        self.items: dict[str, str] = {}
        if settings is not None:
            try:
                self.items = dict(json.loads(settings.value(self.KEY) or "{}"))
            except (ValueError, TypeError):
                self.items = {}
        self.purge()

    @staticmethod
    def key(document_id: int, month: QDate) -> str:
        return f"{document_id}:{month.toString('yyyy-MM')}"

    def is_hidden(self, document_id: int, month: QDate) -> bool:
        return self.key(document_id, month) in self.items

    def hide(self, document_id: int, month: QDate) -> None:
        self.items[self.key(document_id, month)] = QDate.currentDate().toString(Qt.DateFormat.ISODate)
        self.save()

    def restore(self, document_id: int, month: QDate) -> None:
        self.items.pop(self.key(document_id, month), None)
        self.save()

    def purge(self) -> None:
        limit = QDate.currentDate().addDays(-self.KEEP_DAYS)
        expired = [key for key, hidden_on in self.items.items()
                   if not QDate.fromString(hidden_on, Qt.DateFormat.ISODate).isValid()
                   or QDate.fromString(hidden_on, Qt.DateFormat.ISODate) < limit]
        for key in expired:
            del self.items[key]
        if expired:
            self.save()

    def save(self) -> None:
        if self.settings is not None:
            self.settings.setValue(self.KEY, json.dumps(self.items))


def first_of_month(day: QDate) -> QDate:
    return QDate(day.year(), day.month(), 1)


def calculate_monthly_dates(dbh, terms, month: QDate) -> tuple[QDate, QDate, QDate | None]:
    period = period_for_due_month(terms, month)
    today = QDate.currentDate()
    incurrence_date = today if first_of_month(today) == month else month
    due_date = calculate_payment_date(dbh, terms, incurrence_date, period.year(), period.month())
    return period, incurrence_date, due_date if due_date is not None and due_date.isValid() else None


def planned_due_date(dbh, document_id: int, month: QDate) -> QDate | None:
    terms = dbh.load_document_data(document_id)
    if terms is None:
        return None
    return calculate_monthly_dates(dbh, terms, first_of_month(month))[2]


def name_period_offset(name: str, due_date: QDate) -> int | None:
    matches = list(MONTH_RE.finditer(name))
    if len(matches) != 1:
        return None
    month = MONTH_WORDS.index(matches[0].group(1).lower()) + 1
    if matches[0].group(3):
        return (int(matches[0].group(3)) - due_date.year()) * 12 + month - due_date.month()
    diff = (month - due_date.month()) % 12
    return diff - 12 if diff > 6 else diff


def shift_name_period(name: str, period: QDate) -> str:
    matches = list(MONTH_RE.finditer(name))
    if len(matches) != 1:
        return name
    match = matches[0]
    word = MONTH_WORDS[period.month() - 1]
    if match.group(1).isupper():
        word = word.upper()
    elif match.group(1)[0].isupper():
        word = word.capitalize()
    year = f"{match.group(2)}{period.year()}" if match.group(3) else ""
    return f"{name[:match.start()]}{word}{year}{name[match.end():]}"


def fill_placeholders(text: str, period: QDate) -> str:
    return text.replace("{месяц}", MONTH_WORDS[period.month() - 1]).replace("{год}", str(period.year()))


def build_monthly_template(dbh, document_id: int, month: QDate) -> MonthlyTemplate | None:
    terms = dbh.load_document_data(document_id)
    if terms is None:
        return None
    saved = dbh.load_contractdocumentvalues(document_id)
    if saved is None or not saved.category:
        return None
    last = dbh.load_last_event(document_id)

    month = first_of_month(month)
    fields = ("receiver", "category", "subcategory", "name", "nds", "paymenttype", "descr", "responsible", "hidden")
    source = {field: getattr(saved, field) for field in fields}
    source["receiver"] = source["receiver"] or terms.contractor_name
    source["name"] = terms.monthly_name or source["name"]

    period, incurrence_date, due_date = calculate_monthly_dates(dbh, terms, month)
    offset = None
    if last is not None and last["duedate"]:
        offset = name_period_offset(last["name"] or "", QDate.fromString(last["duedate"], dbh.DATE_FORMAT))
    if offset is None:
        offset = (period if terms.month_type is not None else month.addMonths(-1)).month() - month.month()
        offset = (offset + 6) % 12 - 6
    name_period = month.addMonths(offset)

    name = fill_placeholders(source["name"], name_period)
    if name == source["name"]:
        name = shift_name_period(name, name_period)

    values = {
        Col.RECEIVER: source["receiver"], Col.CATEGORY: int(source["category"] or 0), Col.SUBCATEGORY: int(source["subcategory"] or 0),
        Col.NAME: name, Col.NDS: int(source["nds"] or 0), Col.PAYMENTTYPE: int(source["paymenttype"] or 0),
        Col.DESCR: fill_placeholders(source["descr"], name_period), Col.RESPONSIBLE: int(source["responsible"] or 0),
        Col.NOTES: "", Col.HIDDEN: int(source["hidden"] or 0), Col.CONTRACTDOCUMENTID: document_id,
    }
    last_amount = str_decimal(str(last["totalamount"])) if last is not None and last["totalamount"] is not None else None
    name_ambiguous = name == source["name"] and len(MONTH_RE.findall(name)) > 1
    return MonthlyTemplate(values, terms.monthly_amount, period, incurrence_date, due_date, month=month, last_amount=last_amount, name_ambiguous=name_ambiguous)
