from decimal import Decimal, InvalidOperation
from typing import Any, NamedTuple, TYPE_CHECKING

from PySide6.QtCore import QDate, Qt

from base.date import str_date
from base.formatting import dec_strcommaspace
from base.liability import (CATEGORY_NAMES, Col, HeaderFooterSubtype, LiabilityCategory, LiabilityRow,
                            PAYMENTTYPE_NAMES, PeriodField, RowType, STORED_INDEX, TermCategory, calculate_filterflags, category_section,
                            is_top_level_category, matches_category, matches_details, matches_filters, matches_term,
                            paid_threshold)

if TYPE_CHECKING:
    from base.dbhandler import DBHandler


def to_int(value: Any) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return Decimal(0)


class VisibleRow(NamedTuple):
    row_type: RowType
    event_id: int
    category: int
    subtype: int
    total: Decimal | None = None
    remain: Decimal | None = None
    today_share: Decimal | None = None


class Totals(NamedTuple):
    count: int
    total: dict[int, Decimal]
    remain: dict[int, Decimal]
    today: dict[int, Decimal]


class LiabilityStore:

    TOTAL_CATEGORY = 9999
    NO_PAYMENTS = (Decimal(0), Decimal(0), "")
    TEXT_SORT_COLUMNS = (Col.RECEIVER, Col.NAME, Col.DESCR)

    def __init__(self, db_handler: "DBHandler"):
        self.db_handler = db_handler
        self.current_date: QDate = QDate.currentDate()
        self.paid_load_months: int | None = None
        self.payment_totals: dict[int, tuple[Decimal, Decimal, str]] = {}
        self.events: dict[int, tuple] = {}
        self.liabilities: dict[int, LiabilityRow] = {}
        self.due_dates: dict[int, QDate] = {}
        self.sort_dates: dict[int, int] = {}
        self.responsible_names: dict[int, str] = {}

        self.term_filter: int = TermCategory.UNPAID
        self.category_filter: int = 0
        self.header_filter: bool = False
        self.footer_filter: bool = False
        self.paytoday_filter: bool = False
        self.search_filter: str = ""
        self.responsible_filter: int = 0
        self.featured_filter: bool = False
        self.date_from_filter: QDate | None = None
        self.date_to_filter: QDate | None = None
        self.period_field_filter: PeriodField = PeriodField.DUEDATE
        self.paid_months_filter: int = 3
        self.exclude_hidden: bool = False

        self.sort_column: int = Col.DUEDATE
        self.sort_order: Qt.SortOrder = Qt.SortOrder.AscendingOrder

        self.visible: list[VisibleRow] | None = None
        self.positions: dict[int, int] | None = None
        self.totals_cache: Totals | None = None
        self.counters_cache: tuple[dict, dict] | None = None

    def invalidate(self) -> None:
        self.visible = None
        self.positions = None
        self.totals_cache = None
        self.counters_cache = None

    def set_paid_load_months(self, months: int) -> None:
        self.paid_load_months = months

    def reload(self) -> None:
        previous = self.snapshot()
        self.current_date = QDate.currentDate()
        self.payment_totals = self.db_handler.load_payment_totals(self.current_date) or {}
        threshold = None if self.paid_load_months is None else paid_threshold(self.current_date, self.paid_load_months)
        events = self.db_handler.load_events(threshold) or []
        self.events = {values[STORED_INDEX[Col.ID]]: values for values in events}
        self.refresh_derived(*previous)

    def load_payment_totals(self) -> None:
        previous = self.snapshot()
        self.payment_totals = self.db_handler.load_payment_totals(self.current_date) or {}
        self.refresh_derived(*previous)

    def refresh_event(self, event_id: int) -> None:
        events = self.db_handler.load_events(event_id=event_id)
        if not events:
            self.remove_event(event_id)
            return
        previous = self.snapshot()
        payments = self.db_handler.load_payment_totals(self.current_date, event_id) or {}
        self.events = dict(self.events)
        self.events[event_id] = events[0]
        self.payment_totals = {key: value for key, value in self.payment_totals.items() if key != event_id}
        self.payment_totals.update(payments)
        self.refresh_derived(*previous)

    def remove_event(self, event_id: int) -> None:
        previous = self.snapshot()
        self.events = {key: value for key, value in self.events.items() if key != event_id}
        self.payment_totals = {key: value for key, value in self.payment_totals.items() if key != event_id}
        self.refresh_derived(*previous)

    def snapshot(self) -> tuple:
        return (self.current_date, self.events, self.payment_totals, self.liabilities, self.due_dates, self.sort_dates)

    @staticmethod
    def date_key(due_date: QDate) -> int:
        return due_date.toJulianDay() if due_date else 0

    def refresh_derived(self, previous_date: QDate, previous_events: dict, previous_payments: dict,
                        previous_liabilities: dict, previous_due_dates: dict, previous_sort_dates: dict) -> None:
        same_day = previous_date == self.current_date
        self.liabilities = {}
        self.due_dates = {}
        self.sort_dates = {}
        for event_id, values in self.events.items():
            unchanged = same_day and previous_events.get(event_id) == values
            due = values[STORED_INDEX[Col.DUEDATE]]
            if to_int(values[STORED_INDEX[Col.TYPE]]) != RowType.LIABILITY:
                if unchanged:
                    self.sort_dates[event_id] = previous_sort_dates[event_id]
                else:
                    self.sort_dates[event_id] = self.date_key(str_date(due)) if due else 0
                continue
            if unchanged:
                self.due_dates[event_id] = previous_due_dates[event_id]
                self.sort_dates[event_id] = previous_sort_dates[event_id]
                if previous_payments.get(event_id) == self.payment_totals.get(event_id):
                    self.liabilities[event_id] = previous_liabilities[event_id]
                    continue
            else:
                self.due_dates[event_id] = str_date(due)
                self.sort_dates[event_id] = self.date_key(self.due_dates[event_id])
            self.liabilities[event_id] = self.build_liability(event_id, values)
        self.invalidate()

    @staticmethod
    def amount_search_text(amount: Decimal) -> str:
        if amount == 0:
            return ""
        shown = dec_strcommaspace(amount)
        compact = shown.replace(" ", "")
        return f"{shown}\n{compact}\n{compact.replace(',', '.')}"

    def build_liability(self, event_id: int, values: tuple) -> LiabilityRow:
        paid, today_share, last_payment_date = self.payment_totals.get(event_id, self.NO_PAYMENTS)
        try:
            remain = Decimal(values[STORED_INDEX[Col.TOTALAMOUNT]]) - paid
        except (InvalidOperation, TypeError):
            remain = -paid
        incurrence = values[STORED_INDEX[Col.INCURRENCEDATE]]
        filter_flags = calculate_filterflags(remain, self.due_dates[event_id], today_share != 0, self.current_date)
        total = to_decimal(values[STORED_INDEX[Col.TOTALAMOUNT]])
        search_text = "\n".join([str(values[STORED_INDEX[column]] or "")
                                 for column in (Col.NAME, Col.DESCR, Col.RECEIVER)]
                                + [self.amount_search_text(amount) for amount in (total, remain, today_share)]).lower()
        return LiabilityRow(category=to_int(values[STORED_INDEX[Col.CATEGORY]]),
                            search_text=search_text,
                            responsible=to_int(values[STORED_INDEX[Col.RESPONSIBLE]]),
                            featured=bool(values[STORED_INDEX[Col.FEATURED]]),
                            hidden=bool(values[STORED_INDEX[Col.HIDDEN]]),
                            remain=remain, today_share=today_share, last_payment_date=last_payment_date,
                            filter_flags=filter_flags, due_date=self.due_dates[event_id],
                            incurrence_date=str_date(incurrence) if incurrence else QDate())

    def set_filters(self, term: TermCategory, category: int, search: str, responsible: int, paid_today: bool,
                    paid_months_toshow: int, featured: bool, date_from: QDate | None = None,
                    date_to: QDate | None = None, period_field: PeriodField = PeriodField.DUEDATE) -> None:
        self.term_filter = term
        self.category_filter = category
        self.search_filter = search.strip().lower()
        self.responsible_filter = responsible
        self.paytoday_filter = paid_today
        self.paid_months_filter = paid_months_toshow
        self.featured_filter = featured
        self.date_from_filter = date_from
        self.date_to_filter = date_to
        self.period_field_filter = period_field
        self.invalidate()

    def set_hidden_filter(self, exclude_hidden: bool) -> None:
        self.exclude_hidden = exclude_hidden
        self.invalidate()

    def set_header_filter(self, show: bool) -> None:
        self.header_filter = show
        self.invalidate()

    def set_footer_filter(self, show: bool) -> None:
        self.footer_filter = show
        self.invalidate()

    def set_sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.sort_column = column
        self.sort_order = order
        self.invalidate()

    def row_by_id(self, event_id: int) -> LiabilityRow | None:
        return self.liabilities.get(event_id)

    def event_values(self, event_id: int) -> tuple | None:
        return self.events.get(event_id)

    def position_of(self, event_id: int) -> int | None:
        if self.positions is None:
            self.positions = {row.event_id: position for position, row in enumerate(self.visible_rows())}
        return self.positions.get(event_id)

    def visible_rows(self) -> list[VisibleRow]:
        if self.visible is None:
            self.build_visible()
        return self.visible

    def totals(self) -> Totals:
        if self.totals_cache is None:
            self.build_visible()
        return self.totals_cache

    def build_visible(self) -> None:
        threshold = paid_threshold(self.current_date, self.paid_months_filter)
        accepted_ids: set[int] = set()
        category_counts: dict[int, int] = {}
        for event_id, liability in self.liabilities.items():
            if self.exclude_hidden and liability.hidden:
                continue
            if not matches_filters(liability, self.term_filter, self.category_filter, self.search_filter,
                                   self.responsible_filter, self.paytoday_filter, self.featured_filter, threshold,
                                   self.date_from_filter, self.date_to_filter, self.period_field_filter):
                continue
            accepted_ids.add(event_id)
            group = category_section(liability.category)
            category_counts[liability.category] = category_counts.get(liability.category, 0) + 1
            category_counts[group] = category_counts.get(group, 0) + 1

        rows: list[VisibleRow] = []
        for event_id, values in self.events.items():
            row_type = to_int(values[STORED_INDEX[Col.TYPE]])
            category = to_int(values[STORED_INDEX[Col.CATEGORY]])
            subtype = to_int(values[STORED_INDEX[Col.SUBCATEGORY]])
            if row_type == RowType.LIABILITY:
                if event_id not in accepted_ids or not category:
                    continue
            elif not self.service_row_accepted(row_type, subtype, bool(accepted_ids), category, category_counts):
                continue
            rows.append(VisibleRow(RowType(row_type), event_id, category, subtype))

        rows.sort(key=self.sort_value, reverse=self.sort_order == Qt.SortOrder.DescendingOrder)
        rows.sort(key=self.group_key)
        self.visible = self.attach_totals(rows)

    def service_row_accepted(self, row_type: int, subtype: int, has_liabilities: bool, category: int,
                             category_counts: dict[int, int]) -> bool:
        if row_type not in (RowType.HEADER, RowType.FOOTER, RowType.FINALFOOTER):
            return False
        if self.search_filter and row_type in (RowType.HEADER, RowType.FOOTER):
            return False
        if row_type == RowType.HEADER and not self.header_filter:
            return False
        if row_type in (RowType.FOOTER, RowType.FINALFOOTER) and not self.footer_filter:
            return False
        if self.category_filter:
            if row_type == RowType.HEADER:
                return False
            if row_type == RowType.FOOTER and subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS:
                return False
            if row_type == RowType.FINALFOOTER:
                return False
        if row_type == RowType.FINALFOOTER:
            return has_liabilities
        if not category:
            return False
        key = category_section(category) if category == LiabilityCategory.TOP_CURRENT else category
        return category_counts.get(key, 0) > 0

    @staticmethod
    def group_key(row: VisibleRow) -> tuple:
        if row.row_type == RowType.FINALFOOTER:
            return 98, 0, 0, 0
        division_footer = 1 if row.row_type == RowType.FOOTER and row.subtype == HeaderFooterSubtype.TOPLEVELNOEVENTS else 0
        return category_section(row.category), division_footer, row.category, int(row.row_type)

    def sort_value(self, row: VisibleRow) -> Any:
        column = self.sort_column
        values = self.events[row.event_id]
        liability = self.liabilities.get(row.event_id)
        if column in self.TEXT_SORT_COLUMNS:
            return str(values[STORED_INDEX[column]] or "").casefold()
        if column == Col.INCURRENCEDATE:
            return str(values[STORED_INDEX[column]] or "")
        if column == Col.TOTALAMOUNT:
            return to_decimal(values[STORED_INDEX[column]])
        if column == Col.PAYMENTTYPE:
            return PAYMENTTYPE_NAMES.get(to_int(values[STORED_INDEX[column]]), "").casefold()
        if column == Col.RESPONSIBLE:
            return self.responsible_names.get(to_int(values[STORED_INDEX[column]]), "Н/Д").casefold()
        if column in (Col.FEATURED, Col.HIDDEN):
            return to_int(values[STORED_INDEX[column]])
        if column == Col.REMAINAMOUNT:
            return liability.remain if liability else Decimal(0)
        if column == Col.TODAYSHARE:
            return liability.today_share if liability else Decimal(0)
        if column == Col.LASTPAYMENTDATE:
            return liability.last_payment_date if liability else ""
        return self.sort_dates[row.event_id]

    def attach_totals(self, rows: list[VisibleRow]) -> list[VisibleRow]:
        stored_total, stored_remain, stored_today = ({category: Decimal(0) for category in LiabilityCategory}
                                                     for _ in range(3))
        for stored_dict in stored_total, stored_remain, stored_today:
            stored_dict[self.TOTAL_CATEGORY] = Decimal(0)
        count = 0
        for row in rows:
            if row.row_type != RowType.LIABILITY:
                continue
            liability = self.liabilities[row.event_id]
            count += 1
            totalamount = to_decimal(self.events[row.event_id][STORED_INDEX[Col.TOTALAMOUNT]])
            for stored_dict, value in ((stored_total, totalamount), (stored_remain, liability.remain),
                                       (stored_today, liability.today_share)):
                stored_dict[row.category] = stored_dict.get(row.category, Decimal(0)) + value
        for stored_dict in stored_total, stored_remain, stored_today:
            total_total: Decimal = Decimal(0)
            for category in stored_dict.keys():
                if is_top_level_category(category):
                    category_prefix: int = category_section(category)
                    running_total: Decimal = Decimal(0)
                    for key, value in stored_dict.items():
                        if category_section(key) == category_prefix:
                            running_total += value
                    stored_dict[category] = running_total
                if category != LiabilityCategory.TOP_CURRENT:
                    total_total += stored_dict[category]
            stored_dict[self.TOTAL_CATEGORY] = total_total
        self.totals_cache = Totals(count, stored_total, stored_remain, stored_today)

        result: list[VisibleRow] = []
        for row in rows:
            if row.row_type == RowType.FOOTER:
                row = row._replace(total=stored_total.get(row.category, Decimal(0)),
                                   remain=stored_remain.get(row.category, Decimal(0)),
                                   today_share=stored_today.get(row.category, Decimal(0)))
            elif row.row_type == RowType.FINALFOOTER:
                row = row._replace(total=stored_total[self.TOTAL_CATEGORY], remain=stored_remain[self.TOTAL_CATEGORY],
                                   today_share=stored_today[self.TOTAL_CATEGORY])
            result.append(row)
        return result

    def filter_counters(self) -> tuple[dict[int, int], dict[int, int]]:
        if self.counters_cache is None:
            self.counters_cache = self.build_counters()
        return self.counters_cache

    def build_counters(self) -> tuple[dict[int, int], dict[int, int]]:
        threshold = paid_threshold(self.current_date, self.paid_months_filter)
        term_labels_dict = dict.fromkeys(TermCategory, 0)
        category_counts: dict[int, int] = {}
        total_by_term = 0
        for liability in self.liabilities.values():
            if not matches_details(liability, self.search_filter, self.responsible_filter, self.paytoday_filter,
                                   self.featured_filter, self.date_from_filter, self.date_to_filter,
                                   self.period_field_filter):
                continue
            if matches_category(self.category_filter, liability):
                for term_category in TermCategory:
                    if matches_term(term_category, liability, threshold):
                        term_labels_dict[term_category] += 1
            if matches_term(self.term_filter, liability, threshold):
                total_by_term += 1
                category_counts[liability.category] = category_counts.get(liability.category, 0) + 1

        category_labels_dict = {}
        for category_key in CATEGORY_NAMES.keys():
            category_labels_dict[category_key] = total_by_term if category_key % 1000 == 0 else category_counts.get(category_key, 0)
        return term_labels_dict, category_labels_dict
