import ast
import itertools
import random
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

import base.liabilitystore as storemod
from base.liability import Col, FilterFlags, HeaderFooterSubtype, PaymentType, RowType, TermCategory
from base.liabilitystore import LiabilityStore
from gui.eventproxymodel import Filter
from tests.test_readpath import (DB_VALUE, add_event, add_payment, day, db_file, file_hash, fill_sample_db, models,
                                 open_models, run_sql)

TOP = HeaderFooterSubtype.TOPLEVELNOEVENTS
WITH_EVENTS = HeaderFooterSubtype.TOPLEVELWITHEVENTS
ORDINARY = HeaderFooterSubtype.ORDINARY


class Both:

    def __init__(self, models):
        self.models = models
        self.store = LiabilityStore(models.base.db_handler)
        self.store.set_header_filter(True)
        self.store.set_footer_filter(True)
        self.store.reload()
        self.args: dict = {}
        self.apply()

    def apply(self, term=TermCategory.UNPAID, category=0, search="", responsible=0, paid_today=False,
              featured=False, months=3) -> None:
        self.args = dict(term=term, category=category, search=search, responsible=responsible, paid_today=paid_today,
                         featured=featured, months=months)
        self.models.apply(**self.args)
        self.store.set_filters(term, category, search, responsible, paid_today, months, featured)

    def reload(self) -> None:
        self.models.base.invalidate_sort_cache()
        self.models.base.select()
        self.store.reload()
        self.apply(**self.args)

    def set_service_rows(self, headers: bool, footers: bool) -> None:
        self.models.proxy1.set_filter(Filter.HEADER, headers)
        self.models.proxy1.set_filter(Filter.FOOTER, footers)
        self.store.set_header_filter(headers)
        self.store.set_footer_filter(footers)

    def set_hidden_filter(self, exclude_hidden: bool) -> None:
        self.models.proxy1.set_hidden_filter(exclude_hidden)
        self.store.set_hidden_filter(exclude_hidden)

    def set_paid_load_months(self, months: int) -> None:
        self.models.base.set_paid_load_months(months)
        self.store.set_paid_load_months(months)
        self.reload()


@pytest.fixture
def both_factory(open_models):
    def factory(path: Path) -> Both:
        return Both(open_models(path))
    return factory


@pytest.fixture
def both(db_file, both_factory):
    return both_factory(db_file)


def oracle_rows(models) -> list[tuple]:
    proxy = models.proxy2
    return [(RowType(proxy.index(row, Col.TYPE).data(DB_VALUE)), proxy.index(row, Col.ID).data(DB_VALUE))
            for row in range(proxy.rowCount())]


def oracle_footer_values(models) -> list[tuple]:
    proxy = models.proxy2
    result = []
    for row in range(proxy.rowCount()):
        if proxy.index(row, Col.TYPE).data(DB_VALUE) in (RowType.FOOTER, RowType.FINALFOOTER):
            result.append(tuple(proxy.index(row, column).data(proxy.decimalValueRole)
                                for column in (Col.TOTALAMOUNT, Col.REMAINAMOUNT, Col.TODAYSHARE)))
    return result


def assert_same_as_chain(both: Both, label=None) -> None:
    models, store = both.models, both.store
    visible = store.visible_rows()
    assert [(row.row_type, row.event_id) for row in visible] == oracle_rows(models), label
    assert [(row.total, row.remain, row.today_share) for row in visible
            if row.row_type in (RowType.FOOTER, RowType.FINALFOOTER)] == oracle_footer_values(models), label
    proxy = models.proxy2
    assert tuple(store.totals()) == (proxy.stored_count, proxy.stored_total, proxy.stored_remain, proxy.stored_today), label
    assert store.filter_counters() == models.labels, label
    for position, row in enumerate(visible):
        assert store.position_of(row.event_id) == position


def fill_rich_db(path: Path) -> None:
    rnd = random.Random(7)
    categories = [1101, 1102, 1103, 1103, 1110, 2100, 3100]
    receivers = ["ООО Ромашка", "ИП Иванов", "Склад Альфа", "ООО Ромашка плюс"]
    for category, subtype in ((1000, TOP), (1101, ORDINARY), (1102, ORDINARY), (1103, ORDINARY), (1110, ORDINARY),
                              (2100, WITH_EVENTS), (3100, TOP)):
        add_event(path, row_type=RowType.HEADER, category=category, total=None, subcategory=subtype, due="")
        add_event(path, row_type=RowType.FOOTER, category=category, total=None, subcategory=subtype, due="")
    add_event(path, row_type=RowType.FINALFOOTER, category=None, total=None, due="")
    for number in range(70):
        refund = number % 17 == 0
        total = f"{rnd.randint(10, 5000)}.{rnd.randint(0, 99):02d}"
        event_id = add_event(path, category=rnd.choice(categories), total=f"-{total}" if refund else total,
                             due=day(rnd.randint(-40, 40)), responsible=str(rnd.randint(1, 3)),
                             receiver=rnd.choice(receivers), featured=int(number % 5 == 0), hidden=int(number % 11 == 0),
                             paymenttype=PaymentType.REFUND if refund else PaymentType.NORMAL)
        sign = "-" if refund else ""
        kind = number % 7
        if kind == 1:
            add_payment(path, event_id, day(-rnd.randint(1, 20)), f"{sign}{total}")
        elif kind == 2:
            add_payment(path, event_id, day(0), f"{sign}{Decimal(total) / 2:.2f}")
        elif kind == 3:
            add_payment(path, event_id, day(-rnd.randint(1, 20)), f"{sign}{Decimal(total) + 15:.2f}")
        elif kind == 4:
            add_payment(path, event_id, day(0), f"{sign}{total}")
        elif kind == 5:
            add_payment(path, event_id, day(-200), f"{sign}{total}")
        elif kind == 6:
            add_payment(path, event_id, day(-2), f"{sign}1.10")
            add_payment(path, event_id, day(-1), f"{sign}2.20")
    add_event(path, category=1000, total="300.00", due=day(3))
    add_event(path, category=0, total="70.00", due=day(1))
    add_event(path, category=1101, total="abc", due=day(2))
    add_event(path, category=1101, total=None, due=day(2))
    add_event(path, category=1101, total="40.00", due="")
    run_sql(path, "UPDATE event SET name = 'Аренда ' || id, descr = 'Договор ' || (id % 4) WHERE type = 2")


@pytest.fixture
def rich(db_file, both_factory):
    fill_rich_db(db_file)
    return both_factory(db_file)


def test_chain_oracle_covers_all_row_kinds(rich):
    kinds = {row.row_type for row in rich.store.visible_rows()}
    assert kinds == set(RowType)


def test_every_term_category_and_service_flags_match_chain(rich):
    checked = 0
    for term, category, headers, footers in itertools.product(TermCategory, (0, 1000, 1101, 1103, 2100),
                                                              (True, False), (True, False)):
        rich.set_service_rows(headers, footers)
        rich.apply(term, category=category)
        assert_same_as_chain(rich, (term, category, headers, footers))
        checked += 1
    assert checked == 120


def test_random_filter_combinations_match_chain(rich):
    rnd = random.Random(11)
    for _ in range(200):
        rich.set_service_rows(rnd.random() < 0.8, rnd.random() < 0.8)
        rich.set_hidden_filter(rnd.random() < 0.3)
        rich.apply(rnd.choice(list(TermCategory)), category=rnd.choice((0, 1000, 1101, 1102, 1103, 1110, 2100, 3100)),
                   search=rnd.choice(("", "", "ромашка", "иванов", " АРЕНДА 1", "договор 2", "нет такого")),
                   responsible=rnd.choice((0, 1, 2, 3)), paid_today=rnd.random() < 0.3,
                   featured=rnd.random() < 0.3, months=rnd.choice((1, 3, 12)))
        assert_same_as_chain(rich, rich.args)


def test_hidden_rows_are_excluded_from_rows_and_totals_but_not_from_counters(rich):
    rich.apply(TermCategory.UNPAID)
    counters_before = rich.store.filter_counters()
    count_before = rich.store.totals().count
    rich.set_hidden_filter(True)
    assert_same_as_chain(rich)
    assert rich.store.filter_counters() == counters_before
    assert rich.store.totals().count < count_before
    assert all(not rich.store.row_by_id(row.event_id).hidden for row in rich.store.visible_rows()
               if row.row_type == RowType.LIABILITY)
    rich.set_hidden_filter(False)
    assert_same_as_chain(rich)
    assert rich.store.totals().count == count_before


def test_reload_picks_up_changes_like_the_chain(rich):
    new_event = add_event(rich.models.path, category=1102, total="500.00", due=day(-3), receiver="Новый")
    due_event = add_event(rich.models.path, category=1102, total="20.00", due=day(-4), receiver="Новый")
    rich.reload()
    assert_same_as_chain(rich)
    assert rich.store.row_by_id(new_event).remain == Decimal("500.00")

    add_payment(rich.models.path, new_event, day(0), "500.00")
    run_sql(rich.models.path, "UPDATE event SET duedate = ? WHERE id = ?", day(30), due_event)
    rich.models.base.load_payment_totals()
    rich.reload()
    assert_same_as_chain(rich)
    assert rich.store.row_by_id(new_event).remain == Decimal(0)
    assert rich.store.row_by_id(new_event).today_share == Decimal("500.00")

    run_sql(rich.models.path, "DELETE FROM event WHERE id = ?", due_event)
    rich.reload()
    assert_same_as_chain(rich)
    assert rich.store.row_by_id(due_event) is None
    assert rich.store.position_of(due_event) is None


def test_load_payment_totals_recalculates_only_aggregates(rich):
    event_id = add_event(rich.models.path, category=1101, total="800.00", due=day(-1), receiver="Платёж")
    rich.reload()
    assert rich.store.row_by_id(event_id).filter_flags & FilterFlags.DUE
    add_payment(rich.models.path, event_id, day(-1), "800.00")
    rich.store.load_payment_totals()
    assert rich.store.row_by_id(event_id).remain == Decimal(0)
    assert rich.store.row_by_id(event_id).filter_flags == FilterFlags.PAID
    rich.models.base.load_payment_totals()
    rich.apply(**rich.args)
    assert_same_as_chain(rich)


def test_old_paid_rows_are_not_loaded_like_in_the_chain(rich):
    assert any(rich.store.row_by_id(event_id).last_payment_date < day(-100) for event_id in rich.store.liabilities)
    for months in (3, 12, 1):
        rich.set_paid_load_months(months)
        loaded = {event_id for event_id in rich.store.events}
        chain = {rich.models.base.index(row, Col.ID).data(DB_VALUE) for row in range(rich.models.base.rowCount())}
        assert loaded == chain, months
        assert_same_as_chain(rich, months)


def test_empty_database(both):
    store = both.store
    assert store.visible_rows() == []
    assert store.position_of(1) is None and store.row_by_id(1) is None
    term_labels, category_labels = store.filter_counters()
    assert not any(term_labels.values()) and not any(category_labels.values())
    assert store.totals().count == 0 and not any(store.totals().total.values())
    for term in TermCategory:
        both.apply(term)
        assert_same_as_chain(both, term)


def test_only_service_rows_without_liabilities_are_hidden(db_file, both_factory):
    add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=ORDINARY)
    add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    both = both_factory(db_file)
    assert both.store.visible_rows() == []
    assert_same_as_chain(both)


def test_refunds_and_overpayment_in_rows_and_totals(db_file, both_factory):
    refund = add_event(db_file, category=1101, total="-500.00", paymenttype=PaymentType.REFUND, due=day(-2))
    refunded = add_event(db_file, category=1101, total="-300.00", paymenttype=PaymentType.REFUND, due=day(-2))
    add_payment(db_file, refunded, day(-1), "-300.00")
    over = add_event(db_file, category=1102, total="100.00", due=day(5))
    add_payment(db_file, over, day(0), "150.00")
    add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    both = both_factory(db_file)
    store = both.store

    assert store.row_by_id(refund).remain == Decimal("-500.00")
    assert store.row_by_id(refund).filter_flags == FilterFlags.PAID
    assert store.row_by_id(refunded).filter_flags == FilterFlags.PAID
    assert store.row_by_id(over).remain == Decimal("-50.00")
    assert store.row_by_id(over).today_share == Decimal("150.00")
    assert FilterFlags.NOTPAID in store.row_by_id(over).filter_flags

    for term in TermCategory:
        both.apply(term)
        assert_same_as_chain(both, term)

    both.apply(TermCategory.UNPAID)
    assert [row.event_id for row in store.visible_rows() if row.row_type == RowType.LIABILITY] == [over]
    assert store.totals().total[1102] == Decimal("100.00")
    assert store.totals().remain[store.TOTAL_CATEGORY] == Decimal("-50.00")
    assert store.totals().today[store.TOTAL_CATEGORY] == Decimal("150.00")

    both.apply(TermCategory.PAID)
    assert [row.event_id for row in store.visible_rows() if row.row_type == RowType.LIABILITY] == [refunded]
    footer = [row for row in store.visible_rows() if row.row_type == RowType.FOOTER][0]
    assert (footer.total, footer.remain, footer.today_share) == (Decimal("-300.00"), Decimal(0), Decimal(0))


def test_visible_rows_have_four_kinds_in_section_order(rich):
    rows = rich.store.visible_rows()
    assert [row.row_type for row in rows][0] == RowType.HEADER
    assert rows[-1].row_type == RowType.FINALFOOTER
    sections = [row.category // 1000 for row in rows[:-1]]
    assert sections == sorted(sections)
    top_footer = [row for row in rows if row.row_type == RowType.FOOTER and row.subtype == TOP]
    for footer in top_footer:
        last_of_section = [row for row in rows[:-1] if row.category // 1000 == footer.category // 1000][-1]
        assert last_of_section == footer


def test_row_by_id_and_position_of(rich):
    rows = rich.store.visible_rows()
    liability = next(row for row in rows if row.row_type == RowType.LIABILITY)
    assert rich.store.row_by_id(liability.event_id).category == liability.category
    assert rich.store.position_of(liability.event_id) == rows.index(liability)
    assert rich.store.event_values(liability.event_id)[1] == liability.event_id
    header = next(row for row in rows if row.row_type == RowType.HEADER)
    assert rich.store.row_by_id(header.event_id) is None
    assert rich.store.position_of(header.event_id) == rows.index(header)


def liabilities_by_category(rows) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for row in rows:
        if row.row_type == RowType.LIABILITY:
            result.setdefault(row.category, []).append(row.event_id)
    return result


def test_set_sort_changes_order_only_inside_categories(db_file, both_factory):
    ids = [add_event(db_file, category=1101, total=total, due=due, receiver=receiver)
           for total, due, receiver in (("30.00", day(2), "Б"), ("10.00", day(3), "а"), ("20.00", day(1), "В"))]
    other = add_event(db_file, category=1102, total="5.00", due=day(9))
    add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=ORDINARY)
    both = both_factory(db_file)
    store = both.store
    first, second, third = ids

    assert liabilities_by_category(store.visible_rows())[1101] == [third, first, second]

    store.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.AscendingOrder)
    assert liabilities_by_category(store.visible_rows())[1101] == [second, third, first]
    store.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
    assert liabilities_by_category(store.visible_rows())[1101] == [first, third, second]
    store.set_sort(Col.RECEIVER, Qt.SortOrder.AscendingOrder)
    assert liabilities_by_category(store.visible_rows())[1101] == [second, first, third]
    store.set_sort(Col.DUEDATE, Qt.SortOrder.DescendingOrder)
    assert liabilities_by_category(store.visible_rows())[1101] == [second, first, third]
    assert [row.event_id for row in store.visible_rows()][-1] == other
    assert store.visible_rows()[0].row_type == RowType.HEADER

    store.set_sort(Col.DUEDATE, Qt.SortOrder.AscendingOrder)
    assert_same_as_chain(both)


def test_ties_keep_table_order(db_file, both_factory):
    ids = [add_event(db_file, category=1101, due=day(4)) for _ in range(5)]
    both = both_factory(db_file)
    assert liabilities_by_category(both.store.visible_rows())[1101] == ids
    assert_same_as_chain(both)


def test_store_does_not_import_gui_or_widgets():
    tree = ast.parse(Path(storemod.__file__).read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module)
    assert imported
    assert not [name for name in imported if name.split(".")[0] == "gui" or name.startswith("PySide6.QtWidgets")]


def exercise_store(both: Both) -> None:
    for term in TermCategory:
        both.apply(term)
        both.store.visible_rows()
        both.store.filter_counters()
    both.apply(TermCategory.UNPAID, category=1101, search="ромаш", responsible=1, paid_today=True, featured=True)
    both.store.set_hidden_filter(True)
    both.store.set_sort(Col.TOTALAMOUNT, Qt.SortOrder.DescendingOrder)
    both.store.visible_rows()
    both.store.load_payment_totals()
    both.store.reload()
    both.store.totals()


def test_store_reading_does_not_write(db_file, both_factory):
    fill_sample_db(db_file)
    monitor = sqlite3.connect(db_file)
    try:
        version_before = monitor.execute("PRAGMA data_version").fetchone()[0]
        hash_before = file_hash(db_file)
        content_before = list(monitor.iterdump())

        both = both_factory(db_file)
        exercise_store(both)

        assert monitor.execute("PRAGMA data_version").fetchone()[0] == version_before
        assert file_hash(db_file) == hash_before
        assert list(monitor.iterdump()) == content_before
    finally:
        monitor.close()


def test_store_works_with_read_only_database(db_file, shared_dbh):
    fill_sample_db(db_file)
    hash_before = file_hash(db_file)
    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(db_file))
    shared_dbh.db.setConnectOptions("QSQLITE_OPEN_READONLY")
    try:
        assert shared_dbh.db.open()
        store = LiabilityStore(shared_dbh)
        store.reload()
        store.set_filters(TermCategory.UNPAID, 0, "", 0, False, 3, False)
        expected = [row for row in store.liabilities.values() if FilterFlags.NOTPAID in row.filter_flags]
        assert len([row for row in store.visible_rows() if row.row_type == RowType.LIABILITY]) == len(expected)
        assert store.filter_counters()[0][TermCategory.UNPAID] == len(expected)
    finally:
        shared_dbh.db.close()
        shared_dbh.db.setConnectOptions("")
    assert file_hash(db_file) == hash_before
