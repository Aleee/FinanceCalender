import hashlib
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QDate, QModelIndex, Qt
from PySide6.QtSql import QSqlTableModel

from base.date import date_str
from base.liability import (CATEGORY_NAMES, FilterFlags, HeaderFooterSubtype, LiabilityCategory, PaymentType, RowType,
                            TermCategory, category_section, is_top_level_category)
from base.version import DB_VERSION
from gui.eventproxymodel import Filter, LiabilitySortFilterProxyModel, LiabilityTotalsProxyModel
from gui.eventwidget import EventWidget
from base.formatting import dec_strcommaspace
from gui.eventsqlmodel import Col, LiabilitySqlTableModel, RowFormatting
from tests.dbtools import create_db

QT_VALUE = LiabilitySqlTableModel.qtValueRole
DB_VALUE = LiabilitySqlTableModel.dbValueRole
TODAY = QDate.currentDate()


def day(offset: int) -> str:
    return date_str(TODAY.addDays(offset))


def add_event(path: Path, *, row_type: int = RowType.LIABILITY, category: int = 1101, total: str | None = "1000.00",
              due: str | None = None, paymenttype: int = PaymentType.NORMAL, responsible: str = "1",
              receiver: str = "ООО Ромашка", featured: int = 0, hidden: int = 0, subcategory: int = 0) -> int:
    values = {"receiver": receiver, "type": int(row_type), "category": category, "subcategory": subcategory,
              "name": "name", "totalamount": total, "duedate": due if due is not None else day(10),
              "paymenttype": int(paymenttype), "descr": "descr", "responsible": responsible, "featured": featured,
              "hidden": hidden, "receivernocase": receiver.lower()}
    con = sqlite3.connect(path)
    try:
        cur = con.execute(f"INSERT INTO event ({', '.join(values)}) VALUES ({', '.join('?' * len(values))})",
                          list(values.values()))
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def add_payment(path: Path, event_id: int, paymentdate: str, amount: str) -> int:
    con = sqlite3.connect(path)
    try:
        cur = con.execute("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (?, ?, ?, ?)",
                          (event_id, paymentdate, amount, paymentdate))
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def run_sql(path: Path, sql: str, *params) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(sql, params)
        con.commit()
    finally:
        con.close()


class Models:

    def __init__(self, dbh, path: Path):
        self.path = path
        self.base = LiabilitySqlTableModel(dbh)
        self.base.setTable("event")
        self.base.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.labels: tuple[dict, dict] | None = None
        self.base.filterwidget_labels_changed.connect(lambda term, category: setattr(self, "labels", (dict(term), dict(category))))
        self.base.select()
        self.proxy1 = LiabilitySortFilterProxyModel()
        self.proxy1.setSourceModel(self.base)
        self.proxy1.set_filter(Filter.HEADER, True, invalidate=False)
        self.proxy1.set_filter(Filter.FOOTER, True, invalidate=False)
        self.proxy2 = LiabilityTotalsProxyModel()
        self.proxy2.setSourceModel(self.proxy1)
        self.proxy1.layoutChanged.connect(self.proxy2.recalculate_totals)
        self.apply()

    def apply(self, term=TermCategory.UNPAID, category=0, receiver="", responsible=0, paid_today=False,
              featured=False, months=3) -> None:
        args = (term, category, receiver, responsible, paid_today, months, featured)
        self.proxy1.set_filters(*args)
        self.base.send_filterwidget_labeldata(*args)

    def source_row(self, event_id: int) -> int:
        for row in range(self.base.rowCount()):
            if self.base.index(row, Col.ID).data(DB_VALUE) == event_id:
                return row
        raise LookupError(event_id)

    def value(self, event_id: int, column: int, role: int = QT_VALUE):
        return self.base.index(self.source_row(event_id), column).data(role)

    def visible(self, row_type: RowType = RowType.LIABILITY, model=None) -> list[int]:
        model = model or self.proxy2
        return sorted(model.index(row, Col.ID).data(DB_VALUE) for row in range(model.rowCount())
                      if model.index(row, Col.TYPE).data(DB_VALUE) == row_type)


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    return create_db(tmp_path / "db" / "db.db", DB_VERSION)


@pytest.fixture
def open_models(shared_dbh):
    opened: list[Models] = []

    def factory(path: Path) -> Models:
        shared_dbh.db.close()
        shared_dbh.db.setDatabaseName(str(path))
        assert shared_dbh.db.open()
        opened.append(Models(shared_dbh, path))
        return opened[-1]

    yield factory
    shared_dbh.db.close()
    shared_dbh.db.setConnectOptions("")


@pytest.fixture
def models(db_file, open_models):
    return open_models(db_file)


def reload(models: Models) -> None:
    models.base.select()
    models.apply()


def test_remain_without_payments_equals_total(db_file, open_models):
    event_id = add_event(db_file, total="1234.56")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("1234.56")
    assert models.value(event_id, Col.TODAYSHARE) == Decimal(0)
    assert models.value(event_id, Col.LASTPAYMENTDATE) == ""


def test_stored_computed_columns_are_ignored(db_file, open_models):
    event_id = add_event(db_file, total="500.00", due=day(-3))
    add_payment(db_file, event_id, day(-2), "120.50")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("379.50")
    assert models.value(event_id, Col.LASTPAYMENTDATE) == day(-2)
    flags = models.value(event_id, Col.FILTERFLAGS)
    assert FilterFlags.NOTPAID in flags and FilterFlags.DUE in flags


def test_partial_payments_are_summed(db_file, open_models):
    event_id = add_event(db_file, total="1000.00")
    add_payment(db_file, event_id, day(-5), "0.10")
    add_payment(db_file, event_id, day(-1), "0.20")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("999.70")
    assert models.value(event_id, Col.LASTPAYMENTDATE) == day(-1)


def test_full_payment_makes_row_paid(db_file, open_models):
    event_id = add_event(db_file, total="300.00", due=day(-4))
    add_payment(db_file, event_id, day(-1), "300.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal(0)
    assert models.value(event_id, Col.FILTERFLAGS) == FilterFlags.PAID


def test_overpayment_gives_negative_remain_and_paid_flag(db_file, open_models):
    event_id = add_event(db_file, total="100.00")
    add_payment(db_file, event_id, day(-1), "150.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("-50.00")
    assert models.value(event_id, Col.FILTERFLAGS) == FilterFlags.PAID


def test_refund_is_paid_by_negative_payment(db_file, open_models):
    event_id = add_event(db_file, total="-500.00", paymenttype=PaymentType.REFUND, due=day(-2))
    add_payment(db_file, event_id, day(-2), "-500.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal(0)
    assert models.value(event_id, Col.FILTERFLAGS) == FilterFlags.PAID


def test_payment_today_gives_todayshare_and_keeps_row_notpaid(db_file, open_models):
    event_id = add_event(db_file, total="200.00", due=day(0))
    add_payment(db_file, event_id, day(0), "200.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal(0)
    assert models.value(event_id, Col.TODAYSHARE) == Decimal("200.00")
    flags = models.value(event_id, Col.FILTERFLAGS)
    assert FilterFlags.NOTPAID in flags and FilterFlags.PAID not in flags and FilterFlags.TODAY in flags


def test_partial_payment_today(db_file, open_models):
    event_id = add_event(db_file, total="200.00", due=day(-1))
    add_payment(db_file, event_id, day(0), "50.00")
    add_payment(db_file, event_id, day(-3), "10.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.TODAYSHARE) == Decimal("50.00")
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("140.00")
    assert models.value(event_id, Col.LASTPAYMENTDATE) == day(0)


def test_payment_yesterday_is_not_todayshare(db_file, open_models):
    event_id = add_event(db_file, total="200.00")
    add_payment(db_file, event_id, day(-1), "200.00")
    models = open_models(db_file)
    assert models.value(event_id, Col.TODAYSHARE) == Decimal(0)


@pytest.mark.parametrize("offset, expected, absent", [
    (-1, FilterFlags.DUE, FilterFlags.TODAY | FilterFlags.WEEK | FilterFlags.MONTH),
    (0, FilterFlags.TODAY | FilterFlags.WEEK | FilterFlags.MONTH, FilterFlags.DUE),
    (400, FilterFlags.NONE, FilterFlags.DUE | FilterFlags.TODAY | FilterFlags.WEEK | FilterFlags.MONTH),
])
def test_date_flags(db_file, open_models, offset, expected, absent):
    event_id = add_event(db_file, due=day(offset))
    models = open_models(db_file)
    flags = models.value(event_id, Col.FILTERFLAGS)
    assert FilterFlags.NOTPAID in flags
    assert flags & expected == expected
    assert not flags & absent


def test_adding_and_deleting_payment(models):
    event_id = add_event(models.path, total="800.00", due=day(-1))
    reload(models)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("800.00")

    payment_id = add_payment(models.path, event_id, day(0), "800.00")
    models.base.load_payment_totals()
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal(0)
    assert models.value(event_id, Col.TODAYSHARE) == Decimal("800.00")
    assert models.value(event_id, Col.LASTPAYMENTDATE) == day(0)

    run_sql(models.path, "DELETE FROM payment WHERE id = ?", payment_id)
    models.base.load_payment_totals()
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("800.00")
    assert models.value(event_id, Col.TODAYSHARE) == Decimal(0)
    assert models.value(event_id, Col.LASTPAYMENTDATE) == ""
    assert models.value(event_id, Col.FILTERFLAGS) & FilterFlags.DUE


def test_payment_moves_row_between_terms(models):
    event_id = add_event(models.path, total="800.00", due=day(-1))
    reload(models)
    assert event_id in models.visible()
    add_payment(models.path, event_id, day(-1), "800.00")
    models.base.load_payment_totals()
    models.apply()
    assert event_id not in models.visible()
    models.apply(term=TermCategory.PAID)
    assert event_id in models.visible()


def test_due_date_change(models):
    event_id = add_event(models.path, due=day(-2))
    reload(models)
    assert models.value(event_id, Col.FILTERFLAGS) & FilterFlags.DUE
    run_sql(models.path, "UPDATE event SET duedate = ? WHERE id = ?", day(0), event_id)
    reload(models)
    flags = models.value(event_id, Col.FILTERFLAGS)
    assert flags & FilterFlags.TODAY and not flags & FilterFlags.DUE
    run_sql(models.path, "UPDATE event SET duedate = ? WHERE id = ?", day(300), event_id)
    reload(models)
    assert models.value(event_id, Col.FILTERFLAGS) == FilterFlags.NOTPAID


def test_total_amount_change_changes_remain(models):
    event_id = add_event(models.path, total="100.00")
    add_payment(models.path, event_id, day(-1), "40.00")
    reload(models)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("60.00")
    run_sql(models.path, "UPDATE event SET totalamount = '40.00' WHERE id = ?", event_id)
    reload(models)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal(0)
    assert models.value(event_id, Col.FILTERFLAGS) == FilterFlags.PAID


def test_non_liability_rows_have_neutral_values(models):
    header = add_event(models.path, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    reload(models)
    assert models.value(header, Col.FILTERFLAGS) == FilterFlags.NONE
    assert models.value(header, Col.TODAYSHARE) == Decimal(0)
    assert models.value(header, Col.LASTPAYMENTDATE) == ""


def make_term_events(path: Path) -> dict[str, int]:
    ids = {
        "due": add_event(path, due=day(-5)),
        "today": add_event(path, due=day(0)),
        "far": add_event(path, due=day(400)),
        "paid_recent": add_event(path, total="10.00", due=day(-30)),
        "paid_old": add_event(path, total="10.00", due=day(-300)),
    }
    add_payment(path, ids["paid_recent"], day(-7), "10.00")
    add_payment(path, ids["paid_old"], day(-200), "10.00")
    return ids


def test_term_filters(db_file, open_models):
    ids = make_term_events(db_file)
    models = open_models(db_file)

    models.apply(TermCategory.UNPAID)
    assert models.visible() == sorted([ids["due"], ids["today"], ids["far"]])
    models.apply(TermCategory.DUE)
    assert models.visible() == [ids["due"]]
    models.apply(TermCategory.TODAY)
    assert models.visible() == [ids["today"]]
    models.apply(TermCategory.WEEK)
    assert ids["today"] in models.visible()
    assert ids["due"] not in models.visible() and ids["far"] not in models.visible()
    models.apply(TermCategory.MONTH)
    assert ids["today"] in models.visible()
    assert ids["due"] not in models.visible() and ids["far"] not in models.visible()
    models.apply(TermCategory.PAID, months=3)
    assert models.visible() == [ids["paid_recent"]]
    models.apply(TermCategory.PAID, months=12)
    assert models.visible() == sorted([ids["paid_recent"], ids["paid_old"]])


def test_row_paid_today_stays_in_unpaid_but_not_in_paid(db_file, open_models):
    event_id = add_event(db_file, total="50.00", due=day(0))
    add_payment(db_file, event_id, day(0), "50.00")
    models = open_models(db_file)
    models.apply(TermCategory.UNPAID)
    assert event_id in models.visible()
    models.apply(TermCategory.PAID)
    assert event_id not in models.visible()
    models.apply(TermCategory.UNPAID, paid_today=True)
    assert models.visible() == [event_id]


def test_category_filter(db_file, open_models):
    first = add_event(db_file, category=1101)
    second = add_event(db_file, category=1102)
    models = open_models(db_file)
    models.apply(category=1101)
    assert models.visible() == [first]
    models.apply(category=1102)
    assert models.visible() == [second]
    models.apply(category=1000)
    assert models.visible() == sorted([first, second])


def test_receiver_filter_is_case_insensitive_substring(db_file, open_models):
    first = add_event(db_file, receiver="ООО Ромашка")
    second = add_event(db_file, receiver="ИП Иванов")
    models = open_models(db_file)
    models.apply(receiver="РОМАШ")
    assert models.visible() == [first]
    models.apply(receiver="иванов")
    assert models.visible() == [second]
    models.apply(receiver="нет такого")
    assert models.visible() == []


@pytest.mark.parametrize("text", ["%", "_", "'", "\"", "ромаш'ка"])
def test_receiver_filter_special_characters_are_literal(db_file, open_models, text):
    add_event(db_file, receiver="ООО Ромашка")
    special = add_event(db_file, receiver=f"Ромаш{text}ка")
    models = open_models(db_file)
    models.apply(receiver=f"ромаш{text}")
    assert models.visible() == [special]


def test_responsible_featured_and_hidden_filters(db_file, open_models):
    first = add_event(db_file, responsible="1", featured=1)
    second = add_event(db_file, responsible="2", hidden=1)
    models = open_models(db_file)
    models.apply(responsible=1)
    assert models.visible() == [first]
    models.apply(responsible=2)
    assert models.visible() == [second]
    models.apply(featured=True)
    assert models.visible() == [first]
    models.apply()
    models.proxy1.set_hidden_filter(True)
    assert models.visible() == [first]
    models.proxy1.set_hidden_filter(False)
    assert models.visible() == sorted([first, second])


def test_service_rows_follow_toolbar_flags(db_file, open_models):
    add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    liability = add_event(db_file, category=1101)
    models = open_models(db_file)

    models.apply()
    for row_type in (RowType.HEADER, RowType.FOOTER, RowType.FINALFOOTER):
        assert len(models.visible(row_type)) == 1, row_type
    assert models.visible() == [liability]

    models.proxy1.set_filter(Filter.HEADER, False)
    models.proxy1.set_filter(Filter.FOOTER, False)
    assert models.visible(RowType.HEADER) == []
    assert models.visible(RowType.FOOTER) == []
    assert models.visible(RowType.FINALFOOTER) == []
    assert models.visible() == [liability]


def test_service_rows_of_empty_categories_and_finalfooter_hidden_without_liabilities(db_file, open_models):
    add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    paid = add_event(db_file, category=1101, total="10.00")
    add_payment(db_file, paid, day(-1), "10.00")
    models = open_models(db_file)

    models.apply(TermCategory.UNPAID)
    assert models.visible() == []
    assert models.visible(RowType.HEADER) == []
    assert models.visible(RowType.FINALFOOTER) == []

    models.apply(TermCategory.PAID)
    assert models.visible() == [paid]
    assert len(models.visible(RowType.HEADER)) == 1
    assert len(models.visible(RowType.FINALFOOTER)) == 1


def test_totals_follow_filtered_liabilities(db_file, open_models):
    first = add_event(db_file, category=1101, total="100.00", due=day(-1))
    add_event(db_file, category=1102, total="40.00", due=day(400))
    add_payment(db_file, first, day(-1), "30.00")
    models = open_models(db_file)
    models.apply(TermCategory.DUE)
    assert models.proxy2.stored_count == 1
    assert models.proxy2.stored_total[1101] == Decimal("100.00")
    assert models.proxy2.stored_remain[1101] == Decimal("70.00")
    models.apply(TermCategory.UNPAID)
    assert models.proxy2.stored_count == 2
    assert models.proxy2.stored_total[models.proxy2.TOTAL_CATEGORY] == Decimal("140.00")


def test_sidebar_counters(db_file, open_models):
    ids = make_term_events(db_file)
    other = add_event(db_file, category=1102, due=day(-1), receiver="ИП Иванов")
    models = open_models(db_file)

    models.apply(TermCategory.UNPAID)
    term_labels, category_labels = models.labels
    assert term_labels[TermCategory.UNPAID] == 4
    assert term_labels[TermCategory.DUE] == 2
    assert term_labels[TermCategory.TODAY] == 1
    assert term_labels[TermCategory.WEEK] == 1
    assert term_labels[TermCategory.PAID] == 1
    assert category_labels[1101] == 3
    assert category_labels[1102] == 1
    assert category_labels[1000] == 4

    models.apply(TermCategory.DUE, category=1102)
    term_labels, category_labels = models.labels
    assert term_labels[TermCategory.UNPAID] == 1
    assert term_labels[TermCategory.DUE] == 1
    assert category_labels[1101] == 1
    assert category_labels[1102] == 1
    assert category_labels[1000] == 2

    models.apply(TermCategory.UNPAID, receiver="иванов")
    term_labels, category_labels = models.labels
    assert term_labels[TermCategory.UNPAID] == 1
    assert category_labels[1000] == 1
    assert other in models.visible() and len(models.visible()) == 1

    models.apply(TermCategory.PAID, months=12)
    term_labels, category_labels = models.labels
    assert term_labels[TermCategory.PAID] == 2
    assert category_labels[1000] == 2
    assert ids["paid_old"] in models.visible()


def test_sidebar_counters_match_visible_rows(db_file, open_models):
    make_term_events(db_file)
    add_event(db_file, category=1102, due=day(-1), receiver="ИП Иванов", responsible="2", featured=1)
    models = open_models(db_file)
    for term in TermCategory:
        for category in (0, 1101, 1102):
            models.apply(term, category=category)
            term_labels, category_labels = models.labels
            assert term_labels[term] == len(models.visible()), (term, category)
            assert models.proxy2.stored_count == len(models.visible())


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exercise_read_path(models: Models) -> None:
    models.base.select()
    for term in TermCategory:
        models.apply(term)
        models.visible()
    models.apply(TermCategory.UNPAID, category=1101, receiver="ромаш", responsible=1, paid_today=True, featured=True)
    models.base.load_payment_totals()
    models.base.select()
    models.proxy1.set_hidden_filter(True)
    models.proxy1.set_hidden_filter(False)
    for row in range(models.base.rowCount()):
        for column in range(models.base.columnCount()):
            models.base.index(row, column).data(Qt.ItemDataRole.DisplayRole)
            models.base.index(row, column).data(DB_VALUE)


def fill_sample_db(path: Path) -> None:
    for number in range(30):
        event_id = add_event(path, category=1101 + number % 3, due=day(number - 10), total=f"{100 + number}.00")
        if number % 2:
            add_payment(path, event_id, day(0) if number % 4 == 1 else day(-number), f"{50 + number}.00")
    add_event(path, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(path, row_type=RowType.FINALFOOTER, category=None, total=None)


def test_reading_does_not_write(db_file, open_models):
    fill_sample_db(db_file)
    monitor = sqlite3.connect(db_file)
    try:
        version_before = monitor.execute("PRAGMA data_version").fetchone()[0]
        hash_before = file_hash(db_file)
        content_before = list(monitor.iterdump())

        models = open_models(db_file)
        exercise_read_path(models)

        assert monitor.execute("PRAGMA data_version").fetchone()[0] == version_before
        assert file_hash(db_file) == hash_before
        assert list(monitor.iterdump()) == content_before
    finally:
        monitor.close()


def test_app_works_with_read_only_database(db_file, shared_dbh):
    fill_sample_db(db_file)
    expected_unpaid = 0
    con = sqlite3.connect(db_file)
    try:
        for event_id, total in con.execute("SELECT id, totalamount FROM event WHERE type = 2").fetchall():
            paid = con.execute("SELECT COALESCE(SUM(CAST(sum AS REAL)), 0) FROM payment WHERE eventid = ?", (event_id,)).fetchone()[0]
            today_paid = con.execute("SELECT COUNT(*) FROM payment WHERE eventid = ? AND paymentdate = ?", (event_id, day(0))).fetchone()[0]
            if float(total) - paid > 0 or today_paid:
                expected_unpaid += 1
    finally:
        con.close()
    hash_before = file_hash(db_file)

    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(db_file))
    shared_dbh.db.setConnectOptions("QSQLITE_OPEN_READONLY")
    try:
        assert shared_dbh.db.open()
        models = Models(shared_dbh, db_file)
        exercise_read_path(models)
        models.apply(TermCategory.UNPAID)
        assert len(models.visible()) == expected_unpaid
        assert models.base.lastError().text() == ""
    finally:
        shared_dbh.db.close()
        shared_dbh.db.setConnectOptions("")
    assert file_hash(db_file) == hash_before


def test_startup_at_current_version_does_not_write(dbh, work_db_path):
    create_db(work_db_path, dbh.DB_VERSION)
    fill_sample_db(work_db_path)
    hash_before = file_hash(work_db_path)
    assert dbh.migrate_db()
    assert dbh.open_db_connection()
    assert file_hash(work_db_path) == hash_before


def test_model_after_migration_matches_computed_values(dbh, work_db_path, open_models):
    create_db(work_db_path, 3, legacy_event=True)
    con = sqlite3.connect(work_db_path)
    try:
        con.execute("INSERT INTO event (receiver, type, category, name, remainamount, totalamount, duedate, todayshare, "
                    "lastpaymentdate, filterflags, featured, hidden, receivernocase) VALUES ('ООО Ромашка', 2, 1101, 'name', "
                    "'999999.0', '1000.00', ?, '777.0', '2000-01-01', 0, 0, 0, 'ооо ромашка')", (day(-1),))
        con.commit()
    finally:
        con.close()
    add_payment(work_db_path, 1, day(-1), "400.00")
    assert dbh.migrate_db()
    models = open_models(work_db_path)
    assert models.base.columnCount() == len(Col)
    assert models.value(1, Col.REMAINAMOUNT) == Decimal("600.00")
    assert models.value(1, Col.TODAYSHARE) == Decimal(0)
    assert models.value(1, Col.LASTPAYMENTDATE) == day(-1)
    assert models.value(1, Col.FILTERFLAGS) & FilterFlags.DUE
    assert models.visible() == [1]


def test_virtual_columns_are_read_only_and_selectable(models):
    event_id = add_event(models.path)
    reload(models)
    row = models.source_row(event_id)
    for column in LiabilitySqlTableModel.DERIVED_COLUMNS:
        index = models.base.index(row, column)
        flags = models.base.flags(index)
        assert flags & Qt.ItemFlag.ItemIsEnabled
        assert flags & Qt.ItemFlag.ItemIsSelectable
        assert not models.base.setData(index, "1")
    assert models.base.columnCount() == len(Col)


def test_insert_row_takes_only_stored_columns(models):
    data = ["ООО Ромашка", 0, int(RowType.LIABILITY), 0, 1101, 0, "name", "100.00", 0, day(5), day(0),
            int(PaymentType.NORMAL), "descr", "1", "", 0, 0, "ооо ромашка"]
    assert models.base.insert_row(data) is not None
    assert models.base.submitAll()
    reload(models)
    event_id = models.base.index(models.base.rowCount() - 1, Col.ID).data(DB_VALUE)
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("100.00")
    assert models.value(event_id, Col.TOTALAMOUNT) == Decimal("100.00")
    with pytest.raises(IndexError):
        models.base.insert_row(data + [0])


def test_edit_row_writes_every_stored_column(models):
    event_id = add_event(models.path, total="100.00")
    reload(models)
    data = ["ИП Иванов", event_id, int(RowType.LIABILITY), 5, 1102, 0, "new name", "250.00", 1, day(7), day(1),
            int(PaymentType.ADVANCE), "new descr", "3", "note", 1, 1, "ип иванов"]
    assert models.base.edit_row(models.source_row(event_id), data) is not None
    reload(models)
    con = sqlite3.connect(models.path)
    try:
        stored = con.execute("SELECT receiver, id, type, contractdocument_id, category, subcategory, name, totalamount, nds, "
                             "duedate, createdate, paymenttype, descr, responsible, notes, featured, hidden, receivernocase "
                             "FROM event WHERE id = ?", (event_id,)).fetchone()
    finally:
        con.close()
    assert list(stored) == data
    assert models.value(event_id, Col.REMAINAMOUNT) == Decimal("250.00")


def loaded_ids(models: Models) -> set[int]:
    return {models.base.index(row, Col.ID).data(DB_VALUE) for row in range(models.base.rowCount())}


def test_old_paid_rows_are_not_loaded_but_everything_else_is(db_file, open_models):
    old_paid = add_event(db_file, total="100.00")
    add_payment(db_file, old_paid, day(-200), "100.00")
    old_overpaid = add_event(db_file, total="100.00")
    add_payment(db_file, old_overpaid, day(-200), "150.00")
    old_split_paid = add_event(db_file, total="100.00")
    add_payment(db_file, old_split_paid, day(-250), "40.00")
    add_payment(db_file, old_split_paid, day(-200), "60.00")
    old_partial = add_event(db_file, total="100.00")
    add_payment(db_file, old_partial, day(-200), "30.00")
    recent_paid = add_event(db_file, total="100.00")
    add_payment(db_file, recent_paid, day(-10), "100.00")
    paid_today = add_event(db_file, total="100.00")
    add_payment(db_file, paid_today, day(0), "100.00")
    unpaid = add_event(db_file, total="100.00")
    header = add_event(db_file, row_type=RowType.HEADER, total=None)
    models = open_models(db_file)
    assert loaded_ids(models) == {old_paid, old_overpaid, old_split_paid, old_partial, recent_paid, paid_today, unpaid, header}

    models.base.set_paid_load_months(3)
    assert loaded_ids(models) == {old_partial, recent_paid, paid_today, unpaid, header}

    models.base.set_paid_load_months(12)
    assert loaded_ids(models) == {old_paid, old_overpaid, old_split_paid, old_partial, recent_paid, paid_today, unpaid, header}


def test_select_runs_once_per_call(models, monkeypatch):
    calls: list[int] = []
    original = LiabilitySqlTableModel.select

    def counting_select(self):
        calls.append(1)
        return original(self) if len(calls) < 5 else False

    monkeypatch.setattr(LiabilitySqlTableModel, "select", counting_select)
    models.base.select()
    assert len(calls) == 1


def test_select_in_batches_builds_event_cache_once_and_matches_full_build(db_file, open_models):
    for number in range(600):
        event_id = add_event(db_file, total="100.00", due=day(number % 20))
        if number % 3 == 0:
            add_payment(db_file, event_id, day(-1), "40.00")
    models = open_models(db_file)
    full_builds: list[int] = []
    original = models.base.build_event_cache

    def counting_build(rows=None):
        if rows is None:
            full_builds.append(1)
        return original(rows)

    models.base.build_event_cache = counting_build
    models.base.select()
    models.apply()
    assert models.base.rowCount() >= 600
    assert len(full_builds) == 1
    cached = dict(models.base.liability_rows())
    models.base.invalidate_liability_cache()
    assert cached == models.base.liability_rows()


def proxy_row(models: Models, event_id: int) -> int:
    for row in range(models.proxy2.rowCount()):
        if models.proxy2.index(row, Col.ID).data(DB_VALUE) == event_id:
            return row
    raise LookupError(event_id)


def row_font_bold(models: Models, event_id: int, column: int = Col.RECEIVER) -> bool | None:
    font = models.proxy2.index(proxy_row(models, event_id), column).data(Qt.ItemDataRole.FontRole)
    return None if font is None else font.bold()


def test_row_fonts_follow_formatting_and_term(db_file, open_models):
    due = add_event(db_file, category=1101, due=day(-1))
    today = add_event(db_file, category=1101, due=day(0))
    future = add_event(db_file, category=1101, due=day(10))
    header = add_event(db_file, row_type=RowType.HEADER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    footer = add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    final_footer = add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    models = open_models(db_file)

    models.base.set_row_formatting(RowFormatting(due_textbold=True, today_textbold=True, header_textbold=True, footer_textbold=True))
    models.apply()
    assert [row_font_bold(models, event_id) for event_id in (due, today, future, header, footer, final_footer)] == \
           [True, True, None, True, True, True]

    models.base.set_row_formatting(RowFormatting(due_textbold=False, today_textbold=True, header_textbold=False, footer_textbold=False))
    models.apply()
    assert [row_font_bold(models, event_id) for event_id in (due, today, future, header, footer, final_footer)] == \
           [False, True, None, False, False, True]

    models.apply(TermCategory.DUE)
    assert row_font_bold(models, due) is None
    models.apply(TermCategory.TODAY)
    assert row_font_bold(models, today) is None
    models.apply(TermCategory.UNPAID, paid_today=True)
    assert models.visible() == []


def test_totals_cells_only_differ_in_footer_total_columns(db_file, open_models):
    event_id = add_event(db_file, category=1101, total="100.00", due=day(10))
    footer = add_event(db_file, row_type=RowType.FOOTER, category=1101, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    models = open_models(db_file)
    models.base.set_row_formatting(RowFormatting(footer_textbold=False))
    models.apply()
    proxy = models.proxy2
    decimal_role = proxy.decimalValueRole
    footer_row, liability_row = proxy_row(models, footer), proxy_row(models, event_id)

    assert proxy.index(footer_row, Col.TOTALAMOUNT).data(Qt.ItemDataRole.DisplayRole) == dec_strcommaspace(Decimal("100.00"))
    assert proxy.index(footer_row, Col.TOTALAMOUNT).data(decimal_role) == Decimal("100.00")
    assert proxy.index(footer_row, Col.REMAINAMOUNT).data(decimal_role) == Decimal("100.00")
    assert proxy.index(footer_row, Col.TODAYSHARE).data(Qt.ItemDataRole.DisplayRole) == ""
    assert proxy.index(footer_row, Col.TOTALAMOUNT).data(Qt.ItemDataRole.FontRole).bold()
    assert not proxy.index(footer_row, Col.RECEIVER).data(Qt.ItemDataRole.FontRole).bold()
    assert proxy.index(footer_row, Col.RECEIVER).data(decimal_role) is None

    assert proxy.index(liability_row, Col.TOTALAMOUNT).data(Qt.ItemDataRole.DisplayRole) == dec_strcommaspace(Decimal("100.00"))
    assert proxy.index(liability_row, Col.TOTALAMOUNT).data(decimal_role) is None
    assert proxy.index(liability_row, Col.TOTALAMOUNT).data(Qt.ItemDataRole.FontRole) is None


def liability_order(models: Models) -> list[int]:
    proxy = models.proxy2
    return [proxy.index(row, Col.ID).data(DB_VALUE) for row in range(proxy.rowCount())
            if proxy.index(row, Col.TYPE).data(DB_VALUE) == RowType.LIABILITY]


def test_sort_order_follows_changed_due_date_after_cache_invalidation(db_file, open_models):
    first = add_event(db_file, due=day(1))
    second = add_event(db_file, due=day(2))
    third = add_event(db_file, due=day(3))
    models = open_models(db_file)
    assert liability_order(models) == [first, second, third]

    assert models.base.setData(models.base.index(models.source_row(first), Col.DUEDATE), day(10))
    models.base.invalidate_sort_cache()
    models.proxy1.invalidate()
    assert liability_order(models) == [second, third, first]


def test_sort_order_is_correct_after_rows_shift_on_row_removal(db_file, open_models):
    first = add_event(db_file, due=day(5))
    second = add_event(db_file, due=day(2))
    third = add_event(db_file, due=day(3))
    models = open_models(db_file)
    assert liability_order(models) == [second, third, first]

    assert models.base.delete_row(models.source_row(first)) == first
    models.proxy1.invalidate()
    assert liability_order(models) == [second, third]


def totals_by_cells(proxy) -> tuple:
    stored = {name: {category: 0 for category in LiabilityCategory} for name in ("total", "remain", "today")}
    for values in stored.values():
        values[proxy.TOTAL_CATEGORY] = 0
    count = 0
    for row in range(proxy.rowCount()):
        if proxy.index(row, Col.TYPE).data(DB_VALUE) != RowType.LIABILITY:
            continue
        count += 1
        category = proxy.index(row, Col.CATEGORY).data(DB_VALUE)
        stored["total"][category] += proxy.index(row, Col.TOTALAMOUNT).data(QT_VALUE)
        stored["remain"][category] += proxy.index(row, Col.REMAINAMOUNT).data(QT_VALUE)
        stored["today"][category] += proxy.index(row, Col.TODAYSHARE).data(QT_VALUE)
    for values in stored.values():
        total_total = Decimal(0)
        for category in values.keys():
            if is_top_level_category(category):
                section = category_section(category)
                values[category] = sum((value for key, value in values.items() if category_section(key) == section), Decimal(0))
            if category != LiabilityCategory.TOP_CURRENT:
                total_total += values[category]
        values[proxy.TOTAL_CATEGORY] = total_total
    return count, stored["total"], stored["remain"], stored["today"]


def test_totals_match_cell_by_cell_calculation(db_file, open_models):
    categories = [category for category in CATEGORY_NAMES if category % 1000 != 0][:4]
    assert len(categories) == 4
    first = add_event(db_file, category=categories[0], total="100.00", due=day(-3))
    add_payment(db_file, first, day(-2), "30.00")
    add_payment(db_file, first, day(0), "20.00")
    second = add_event(db_file, category=categories[0], total="55.55", due=day(0))
    add_payment(db_file, second, day(-1), "60.00")
    third = add_event(db_file, category=categories[1], total="abc", due=day(5))
    add_payment(db_file, third, day(0), "5.00")
    no_total = add_event(db_file, category=categories[1], total=None, due=day(6))
    add_payment(db_file, no_total, day(0), "7.00")
    fourth = add_event(db_file, category=categories[2], total="1234.50", due=day(40))
    add_payment(db_file, fourth, day(-30), "1234.50")
    add_event(db_file, category=categories[3], total="10.10", due=day(2), hidden=1)
    add_event(db_file, row_type=RowType.HEADER, category=categories[0], total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FOOTER, category=categories[0], total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    add_event(db_file, row_type=RowType.FINALFOOTER, category=None, total=None)
    run_sql(db_file, "UPDATE event SET name = 'special' WHERE id = ?", third)
    models = open_models(db_file)

    checked = 0
    for search in ("", "special", "name", "nothing-matches"):
        models.proxy1.set_filter(Filter.SEARCH, search)
        for term in TermCategory:
            for paytoday in (False, True):
                models.apply(term, paid_today=paytoday)
                assert (models.proxy2.stored_count, models.proxy2.stored_total, models.proxy2.stored_remain,
                        models.proxy2.stored_today) == totals_by_cells(models.proxy2), (search, term, paytoday)
                checked += 1
    assert checked == 48


def test_flags_make_only_liability_rows_selectable(db_file, open_models):
    liability = add_event(db_file)
    service = {row_type: add_event(db_file, row_type=row_type, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
               for row_type in (RowType.HEADER, RowType.FOOTER, RowType.FINALFOOTER)}
    models = open_models(db_file)
    base = models.base

    assert base.flags(base.index(-1, 0)) == Qt.ItemFlag.NoItemFlags
    checked = 0
    for event_id, row_type in [(liability, RowType.LIABILITY)] + [(event_id, row_type) for row_type, event_id in service.items()]:
        row = models.source_row(event_id)
        for column in range(base.columnCount()):
            flags = base.flags(base.index(row, column))
            assert bool(flags & Qt.ItemFlag.ItemIsSelectable) == (row_type == RowType.LIABILITY), (row_type, column)
            assert flags & ~Qt.ItemFlag.ItemIsSelectable == base.stored_flags(base.index(row, column)) & ~Qt.ItemFlag.ItemIsSelectable
            checked += 1
    assert checked == 4 * base.columnCount()


def spanned_rows(view: EventWidget) -> list[int]:
    return [row for row in range(view.model().rowCount()) if view.isFirstColumnSpanned(row, QModelIndex())]


def header_proxy_rows(models: Models) -> list[int]:
    proxy = models.proxy2
    return [row for row in range(proxy.rowCount()) if proxy.index(row, Col.TYPE).data(DB_VALUE) == RowType.HEADER]


def test_span_columns_spans_exactly_the_visible_header_rows(db_file, open_models):
    for category in (1101, 1102):
        add_event(db_file, row_type=RowType.HEADER, category=category, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
        add_event(db_file, row_type=RowType.FOOTER, category=category, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
        add_event(db_file, category=category, due=day(-1))
        paid = add_event(db_file, category=category, total="10.00")
        add_payment(db_file, paid, day(-1), "10.00")
        run_sql(db_file, "UPDATE event SET name = 'special' WHERE id = ?", paid)
    models = open_models(db_file)
    view = EventWidget()
    view.setModel(models.proxy2)

    checked_with_headers = 0
    for search in ("", "special"):
        models.proxy1.set_filter(Filter.SEARCH, search)
        for header_flag in (True, False):
            models.proxy1.set_filter(Filter.HEADER, header_flag)
            for term in TermCategory:
                for category in (0, 1101):
                    models.apply(term, category=category)
                    view.span_columns()
                    expected = header_proxy_rows(models)
                    assert spanned_rows(view) == expected, (search, header_flag, term, category)
                    checked_with_headers += bool(expected)
    assert checked_with_headers > 0

    models.proxy1.set_filter(Filter.SEARCH, "")
    models.proxy1.set_filter(Filter.HEADER, True)
    new_header = add_event(db_file, row_type=RowType.HEADER, category=1102, total=None, subcategory=HeaderFooterSubtype.ORDINARY)
    reload(models)
    view.span_columns()
    assert new_header in [models.proxy2.index(row, Col.ID).data(DB_VALUE) for row in header_proxy_rows(models)]
    assert spanned_rows(view) == header_proxy_rows(models)
