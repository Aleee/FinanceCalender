import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QDate, QSettings

from base import edition
from base.contract import ContractInfo
from base.contracthistory import payment_years, payments_for_year
from base.version import DB_VERSION
from gui.contractdialog import ContractDocumentDialog
from gui.contractordialog import ContractorDialog
from gui.contracthistorydialog import ALL_YEARS, OVERDUE_BACKCOLOR, PAID_BACKCOLOR, ContractHistoryDialog
from tests.dbtools import create_db


def run(path: Path, sql: str, *params) -> int:
    con = sqlite3.connect(path)
    try:
        cursor = con.execute(sql, params)
        con.commit()
        return cursor.lastrowid
    finally:
        con.close()


def add_chain(path: Path, contractor: str, number: str, document: str) -> tuple[int, int, int]:
    contractor_id = run(path, "INSERT INTO contractor (name) VALUES (?)", contractor)
    contract_id = run(path, "INSERT INTO contract (contractor_id, name, date) VALUES (?, ?, '2025-01-10')",
                      contractor_id, number)
    document_id = run(path, "INSERT INTO contractdocument (contract_id, document_name) VALUES (?, ?)",
                      contract_id, document)
    return contractor_id, contract_id, document_id


def add_event(path: Path, document_id: int | None, total: str | None, due: str, name: str = "Счет",
              row_type: int = 2, hidden: int = 0) -> int:
    return run(path, "INSERT INTO event (type, contractdocument_id, name, totalamount, duedate, hidden) "
                     "VALUES (?, ?, ?, ?, ?, ?)", row_type, document_id, name, total, due, hidden)


def add_payment(path: Path, event_id: int, paymentdate: str, amount: str) -> int:
    return run(path, "INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (?, ?, ?, ?)",
               event_id, paymentdate, amount, paymentdate)


@pytest.fixture
def hdb(tmp_path, shared_dbh):
    path = create_db(tmp_path / "db" / "db.db", DB_VERSION)
    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(path))
    assert shared_dbh.db.open()
    shared_dbh.path = path
    yield shared_dbh
    shared_dbh.db.close()
    shared_dbh.db.setConnectOptions("")


def test_obligations_and_payments_of_contractor(hdb):
    path = hdb.path
    contractor_id, contract_id, document_id = add_chain(path, "Альфа", "К-1", "Спецификация")
    event_id = add_event(path, document_id, "1000.00", "2026-03-01")
    add_payment(path, event_id, "2026-03-02", "300.50")
    add_payment(path, event_id, "2026-04-02", "200.00")
    add_event(path, document_id, "500.00", "2026-05-01", name="Второй")

    obligations, payments = hdb.load_contract_history(contractor_id)

    assert [obligation.name for obligation in obligations] == ["Счет", "Второй"]
    first = obligations[0]
    assert (first.total, first.paid, first.remain) == (Decimal("1000.00"), Decimal("500.50"), Decimal("499.50"))
    assert first.due_date == QDate(2026, 3, 1)
    assert (first.contract_id, first.contract_number, first.document_name) == (contract_id, "К-1", "Спецификация")
    assert obligations[1].paid == 0
    assert [(payment.payment_date, payment.amount) for payment in payments] == [
        (QDate(2026, 3, 2), Decimal("300.50")), (QDate(2026, 4, 2), Decimal("200.00"))]
    assert payments[0].event_id == event_id and payments[0].event_name == "Счет"


def test_other_contractors_and_unbound_events_are_not_included(hdb):
    path = hdb.path
    contractor_id, _, document_id = add_chain(path, "Альфа", "К-1", "Док")
    _, _, other_document_id = add_chain(path, "Бета", "К-2", "Док")
    add_event(path, document_id, "100.00", "2026-03-01")
    other_event = add_event(path, other_document_id, "999.00", "2026-03-01")
    add_payment(path, other_event, "2026-03-05", "999.00")
    unbound = add_event(path, None, "777.00", "2026-03-01")
    add_payment(path, unbound, "2026-03-05", "777.00")
    add_event(path, document_id, "50.00", "2026-03-01", row_type=1)

    obligations, payments = hdb.load_contract_history(contractor_id)

    assert [obligation.total for obligation in obligations] == [Decimal("100.00")]
    assert payments == []


def test_filter_by_contract(hdb):
    path = hdb.path
    contractor_id, first_contract, first_document = add_chain(path, "Альфа", "К-1", "Док")
    second_contract = run(path, "INSERT INTO contract (contractor_id, name, date) VALUES (?, 'К-2', '2025-06-01')",
                          contractor_id)
    second_document = run(path, "INSERT INTO contractdocument (contract_id, document_name) VALUES (?, 'Док 2')",
                          second_contract)
    add_event(path, first_document, "100.00", "2026-03-01")
    add_event(path, second_document, "200.00", "2026-03-01")

    assert len(hdb.load_contract_history(contractor_id)[0]) == 2
    obligations, _ = hdb.load_contract_history(contractor_id, second_contract)
    assert [(obligation.total, obligation.contract_number) for obligation in obligations] == [(Decimal("200.00"), "К-2")]


def test_filter_by_document(hdb):
    path = hdb.path
    contractor_id, contract_id, first_document = add_chain(path, "Альфа", "К-1", "Док 1")
    second_document = run(path, "INSERT INTO contractdocument (contract_id, document_name) VALUES (?, 'Док 2')",
                          contract_id)
    add_event(path, first_document, "100.00", "2026-03-01")
    second_event = add_event(path, second_document, "200.00", "2026-03-01")
    add_payment(path, second_event, "2026-03-05", "50.00")

    obligations, payments = hdb.load_contract_history(contractor_id, contract_id, second_document)

    assert [(obligation.total, obligation.document_name) for obligation in obligations] == [(Decimal("200.00"), "Док 2")]
    assert [payment.amount for payment in payments] == [Decimal("50.00")]


def test_empty_total_and_refund_payment(hdb):
    path = hdb.path
    contractor_id, _, document_id = add_chain(path, "Альфа", "К-1", "Док")
    event_id = add_event(path, document_id, None, "2026-03-01")
    add_payment(path, event_id, "2026-03-02", "100.00")
    add_payment(path, event_id, "2026-03-03", "-30.00")

    obligations, payments = hdb.load_contract_history(contractor_id)

    assert (obligations[0].total, obligations[0].paid) == (Decimal(0), Decimal("70.00"))
    assert [payment.amount for payment in payments] == [Decimal("100.00"), Decimal("-30.00")]


def test_viewer_does_not_see_hidden_events(hdb):
    path = hdb.path
    contractor_id, _, document_id = add_chain(path, "Альфа", "К-1", "Док")
    hidden_event = add_event(path, document_id, "100.00", "2026-03-01", hidden=1)
    add_payment(path, hidden_event, "2026-03-02", "100.00")
    add_event(path, document_id, "200.00", "2026-03-01")
    assert len(hdb.load_contract_history(contractor_id)[0]) == 2
    edition.set_viewer(True)
    try:
        obligations, payments = hdb.load_contract_history(contractor_id)
    finally:
        edition.set_viewer(False)
    assert [obligation.total for obligation in obligations] == [Decimal("200.00")]
    assert payments == []


def test_payment_years(hdb):
    path = hdb.path
    contractor_id, _, document_id = add_chain(path, "Альфа", "К-1", "Док")
    paid_event = add_event(path, document_id, "100.00", "2025-12-01")
    add_payment(path, paid_event, "2025-12-20", "100.00")
    partly_event = add_event(path, document_id, "400.00", "2026-01-15")
    add_payment(path, partly_event, "2026-01-20", "150.00")
    add_event(path, document_id, "50.00", "2026-02-01")
    payments = hdb.load_contract_history(contractor_id)[1]

    assert payment_years(payments) == [2026, 2025]
    assert [payment.amount for payment in payments_for_year(payments, 2025)] == [Decimal("100.00")]
    assert len(payments_for_year(payments, None)) == 2



def fill_history(path: Path) -> tuple[int, int, int]:
    contractor_id, contract_id, document_id = add_chain(path, "Альфа", "К-1", "Спецификация")
    year = QDate.currentDate().year()
    paid_event = add_event(path, document_id, "100.00", f"{year}-01-10", name="Оплаченный")
    add_payment(path, paid_event, f"{year}-01-12", "100.00")
    add_payment(path, paid_event, f"{year - 1}-01-12", "0.00")
    add_event(path, document_id, "250.00", f"{year - 1}-02-01", name="Долг")
    return contractor_id, contract_id, paid_event


def test_history_dialog_tables_and_open_event(hdb, tmp_path):
    contractor_id, contract_id, paid_event = fill_history(hdb.path)
    opened: list[int] = []
    dlg = ContractHistoryDialog(hdb, "Контрагент «Альфа»", contractor_id, None,
                                lambda event_id, parent: opened.append(event_id) or False)
    year = QDate.currentDate().year()

    assert dlg.ui.cmb_year.currentData() == year
    assert dlg.ui.tbl_obligations.rowCount() == 2
    assert dlg.ui.tbl_payments.rowCount() == 1
    assert dlg.ui.tbl_obligations.item(0, 1).text() == "Долг"
    assert dlg.ui.tbl_obligations.item(0, 4).text() == "250,00"
    assert [dlg.ui.tbl_obligations_total.item(0, column).text() for column in (1, 3, 4)] == [
        "Итого", "350,00", "250,00"]
    assert dlg.ui.tbl_payments_total.item(0, 1).text() == f"Итого за {year} год"
    assert dlg.ui.tbl_payments_total.item(0, 3).text() == "100,00"
    assert dlg.ui.tw_history.tabText(0) == "Обязательства (2)"
    assert [dlg.ui.tbl_obligations_total.item(1, column).text() for column in (1, 4)] == [
        "из них просрочено:", "250,00"]
    paid_row, debt_row = (dlg.ui.tbl_obligations.item(row, 1).text() for row in (1, 0))
    assert (paid_row, debt_row) == ("Оплаченный", "Долг")
    assert dlg.ui.tbl_obligations.item(1, 0).background().color() == PAID_BACKCOLOR
    assert dlg.ui.tbl_obligations.item(0, 0).background().color() == OVERDUE_BACKCOLOR

    dlg.ui.chb_only_unpaid.setChecked(True)
    assert [dlg.ui.tbl_obligations.item(row, 1).text() for row in range(dlg.ui.tbl_obligations.rowCount())] == ["Долг"]
    assert dlg.ui.tbl_obligations_total.item(0, 3).text() == "250,00"

    dlg.ui.cmb_year.setCurrentIndex(dlg.ui.cmb_year.findData(ALL_YEARS))
    assert dlg.ui.tbl_payments.rowCount() == 2
    assert dlg.ui.tbl_payments_total.item(0, 1).text() == "Итого за все годы"

    dlg.ui.tbl_payments.cellDoubleClicked.emit(0, 0)
    assert opened == []

    dlg.ui.chb_only_unpaid.setChecked(False)
    dlg.ui.tbl_obligations.cellDoubleClicked.emit(1, 0)
    assert opened == [paid_event]


def test_history_dialog_for_contract_hides_contract_column(hdb):
    contractor_id, contract_id, _ = fill_history(hdb.path)
    dlg = ContractHistoryDialog(hdb, "Договор", contractor_id, contract_id, None)

    assert dlg.ui.tbl_obligations.isColumnHidden(0)
    assert dlg.ui.tbl_payments.isColumnHidden(2)


def test_contractor_dialog_history_buttons(hdb, tmp_path):
    fill_history(hdb.path)
    dlg = ContractorDialog(hdb, QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat))
    contractors = dlg.ui.lw_contractor

    contractors.setCurrentRow(0)
    assert not dlg.ui.tb_history_contractor.isEnabled()

    contractors.setCurrentRow(1)
    assert dlg.ui.tb_history_contractor.isEnabled()

    dlg.on_continue_to_contracts()
    dlg.ui.lw_contract.setCurrentRow(0)
    assert not dlg.ui.tb_history_contract.isEnabled()
    dlg.ui.lw_contract.setCurrentRow(1)
    assert dlg.ui.tb_history_contract.isEnabled()
    dlg.on_continue_to_documents()
    dlg.ui.lw_document.setCurrentRow(0)
    assert not dlg.ui.tb_history_document.isEnabled()
    dlg.ui.lw_document.setCurrentRow(1)
    assert dlg.ui.tb_history_document.isEnabled()


def test_document_dialog_history_button(hdb, tmp_path, monkeypatch):
    contractor_id, contract_id, document_id = add_chain(hdb.path, "Альфа", "К-1", "Спецификация")
    run(hdb.path, "INSERT INTO contractpaymentterm (document_id, payment_type) VALUES (?, 'PREPAYMENT')", document_id)
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    info = ContractInfo(contractor_id, "Альфа", contract_id, "К-1", QDate(2025, 1, 10))
    opened: list[ContractHistoryDialog] = []
    monkeypatch.setattr(ContractHistoryDialog, "exec", lambda self: opened.append(self))

    new_dlg = ContractDocumentDialog(hdb, settings, 0, info)
    assert new_dlg.ui.pb_history.isHidden()

    dlg = ContractDocumentDialog(hdb, settings, document_id, info)
    dlg.ui.pb_history.click()

    assert (opened[0].contractor_id, opened[0].contract_id, opened[0].document_id) == (
        contractor_id, contract_id, document_id)
    assert opened[0].ui.lbl_scope.text() == "<b>К-1 от 10.01.2025</b> (Спецификация)"
    assert opened[0].ui.lbl_subtitle.text() == "Альфа"


def test_document_dialog_monthly_fields(hdb, tmp_path):
    contractor_id, contract_id, document_id = add_chain(hdb.path, "Альфа", "К-1", "Акт")
    run(hdb.path, "INSERT INTO contractpaymentterm (document_id, payment_type, month_day, month_type) VALUES (?, 'FIXED', 25, 'NEXT')",
        document_id)
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    info = ContractInfo(contractor_id, "Альфа", contract_id, "К-1", QDate(2025, 1, 10))

    dlg = ContractDocumentDialog(hdb, settings, document_id, info)
    assert not dlg.ui.gb_monthly.isHidden()
    assert not dlg.ui.chb_monthly.isChecked()
    assert not dlg.ui.wdg_monthly.isEnabled()

    dlg.ui.chb_monthly.setChecked(True)
    assert dlg.ui.wdg_monthly.isEnabled()
    assert dlg.ui.chb_byinvoice.isChecked() and not dlg.ui.dsb_monthlyamount.isEnabled()
    dlg.ui.chb_byinvoice.setChecked(False)
    assert dlg.ui.dsb_monthlyamount.isEnabled()
    dlg.ui.dsb_monthlyamount.setValue(1200.5)
    dlg.ui.le_monthlyname.setText(" Аренда за {месяц} {год} г. ")
    assert hdb.save_document_data(dlg.collect_data()) == document_id

    reopened = ContractDocumentDialog(hdb, settings, document_id, info)
    assert reopened.ui.chb_monthly.isChecked()
    assert reopened.ui.dsb_monthlyamount.value() == 1200.5
    assert not reopened.ui.chb_byinvoice.isChecked()
    assert reopened.ui.le_monthlyname.text() == "Аренда за {месяц} {год} г."
    assert reopened.ui.wdg_monthly.isEnabled()

    reopened.ui.chb_byinvoice.setChecked(True)
    assert reopened.ui.dsb_monthlyamount.value() == 0 and not reopened.ui.dsb_monthlyamount.isEnabled()
    assert reopened.collect_data().monthly_amount is None


def test_document_dialog_monthly_only_for_fixed_terms(hdb, tmp_path):
    contractor_id, contract_id, document_id = add_chain(hdb.path, "Альфа", "К-1", "Акт")
    run(hdb.path, "INSERT INTO contractpaymentterm (document_id, payment_type, month_day, month_type) VALUES (?, 'FIXED', 25, 'NEXT')",
        document_id)
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    info = ContractInfo(contractor_id, "Альфа", contract_id, "К-1", QDate(2025, 1, 10))

    dlg = ContractDocumentDialog(hdb, settings, document_id, info)
    dlg.ui.chb_monthly.setChecked(True)
    assert dlg.collect_data().monthly

    dlg.ui.rb_relative.setChecked(True)
    assert dlg.ui.gb_monthly.isHidden()
    assert not dlg.collect_data().monthly

    dlg.ui.rb_fixed.setChecked(True)
    assert not dlg.ui.gb_monthly.isHidden() and dlg.collect_data().monthly
