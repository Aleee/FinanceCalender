import json
from decimal import Decimal

import pytest
from PySide6.QtCore import QDate, QSettings, Qt
from PySide6.QtTest import QTest

from base.liability import Col, FilterFlags
from base.monthly import (HiddenMonthly, MonthlyState, build_monthly_template, fill_placeholders, name_period_offset,
                          shift_name_period)
from gui.copydocdialog import CopyDocDialog
from gui.liabilitytablemodel import LiabilityTableModel
from gui.monthlydialog import MonthlyDialog, template_model
from tests.test_contracthistory import add_chain, add_event, add_payment, hdb, run  # noqa: F401

OCTOBER = QDate(2026, 10, 15)


def make_monthly(path, contractor: str, number: str, document: str, amount: str | None = None) -> int:
    _, _, document_id = add_chain(path, contractor, number, document)
    run(path, "UPDATE contractdocument SET monthly = 1, monthlyamount = ? WHERE id = ?", amount, document_id)
    run(path, "INSERT INTO contractpaymentterm (document_id, payment_type, month_day, month_type) VALUES (?, 'FIXED', 25, 'NEXT')",
        document_id)
    return document_id


def save_values(path, document_id: int, name: str = "Услуги", category: int = 1112, **fields) -> None:
    values = {"receiver": "", "subcategory": 0, "nds": 0, "paymenttype": 1, "descr": "", "responsible": 0, "hidden": 0, **fields}
    run(path, "INSERT OR REPLACE INTO contractsavedvalues (contractdocumentid, category, name, receiver, subcategory, nds, paymenttype, "
              "descr, responsible, hidden) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        document_id, category, name, values["receiver"], values["subcategory"], values["nds"], values["paymenttype"], values["descr"],
        values["responsible"], values["hidden"])


def test_name_period_offset():
    assert name_period_offset("Услуги связи за сентябрь 2026 г.", QDate(2026, 10, 26)) == -1
    assert name_period_offset("Аренда за ноябрь 2026 г.", QDate(2026, 11, 10)) == 0
    assert name_period_offset("Услуги за декабрь", QDate(2027, 1, 12)) == -1
    assert name_period_offset("Аренда за январь-май 2026 г.", QDate(2026, 10, 30)) is None
    assert name_period_offset("Стирка белья", QDate(2026, 10, 30)) is None


def test_shift_name_period_keeps_case_and_year_style():
    assert shift_name_period("Услуги связи за сентябрь 2026 г.", QDate(2027, 1, 1)) == "Услуги связи за январь 2027 г."
    assert shift_name_period("Услуги за СЕНТЯБРЬ 2026", QDate(2026, 11, 1)) == "Услуги за НОЯБРЬ 2026"
    assert shift_name_period("Месяц: Сентябрь", QDate(2026, 11, 1)) == "Месяц: Ноябрь"
    assert shift_name_period("Аренда за январь-май 2026 г.", QDate(2026, 11, 1)) == "Аренда за январь-май 2026 г."
    assert shift_name_period("Стирка белья", QDate(2026, 11, 1)) == "Стирка белья"


def test_fill_placeholders():
    assert fill_placeholders("Аренда за {месяц} {год} г.", QDate(2026, 11, 1)) == "Аренда за ноябрь 2026 г."
    assert fill_placeholders("Аренда за {месяц} {год}", QDate(2026, 11, 1)) == "Аренда за ноябрь 2026 г."


def test_monthly_entries_states(hdb):
    path = hdb.path
    missing = make_monthly(path, "Альфа", "1", "Акт связи")
    unpaid = make_monthly(path, "Бета", "2", "Акт аренды", "5600.39")
    partly = make_monthly(path, "Гамма", "3", "Акт охраны")
    paid = make_monthly(path, "Дельта", "4", "Акт вывоза")
    _, _, not_monthly = add_chain(path, "Эпсилон", "5", "Поставка")
    archived = make_monthly(path, "Омега", "6", "Старый акт")
    run(path, "UPDATE contract SET archived = 1 WHERE id = (SELECT contract_id FROM contractdocument WHERE id = ?)", archived)

    add_event(path, missing, "100", "2026-11-05")
    add_event(path, unpaid, "5600.39", "2026-10-10")
    partly_event = add_event(path, partly, "200", "2026-10-31")
    add_payment(path, partly_event, "2026-10-20", "50")
    paid_event = add_event(path, paid, "300", "2026-10-01")
    add_payment(path, paid_event, "2026-10-02", "300")
    add_event(path, not_monthly, "10", "2026-10-12")

    entries = {entry.title.contractor_name: entry for entry in hdb.load_monthly_entries(OCTOBER)}

    assert set(entries) == {"Альфа", "Бета", "Гамма", "Дельта"}
    assert entries["Альфа"].state == MonthlyState.MISSING
    assert entries["Бета"].state == MonthlyState.UNPAID
    assert entries["Бета"].amount == Decimal("5600.39")
    assert entries["Гамма"].state == MonthlyState.UNPAID
    assert entries["Дельта"].state == MonthlyState.PAID
    assert entries["Альфа"].amount is None

    november = {entry.title.contractor_name: entry for entry in hdb.load_monthly_entries(QDate(2026, 11, 1))}
    assert november["Альфа"].state == MonthlyState.UNPAID
    assert november["Бета"].state == MonthlyState.MISSING


def test_template_takes_values_from_saved_values_and_shifts_month(hdb):
    path = hdb.path
    document_id = make_monthly(path, "УП А1", "1", "Счет-акт", "310")
    save_values(path, document_id, "Услуги связи за сентябрь 2026 г.", receiver="УП А1", nds=25, descr="Счет № 5", responsible=1)
    run(path, "INSERT INTO event (type, contractdocument_id, receiver, name, totalamount, duedate, category, subcategory, nds, "
              "paymenttype, descr, responsible, hidden) VALUES (2, ?, 'УП А1', 'Услуги связи за сентябрь 2026 г.', '259.79', "
              "'2026-10-26', 1112, 0, 25, 1, 'Счет № 5', '1', 0)", document_id)

    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 20))

    assert template.values[Col.NAME] == "Услуги связи за октябрь 2026 г."
    assert template.values[Col.RECEIVER] == "УП А1"
    assert template.values[Col.CATEGORY] == 1112
    assert template.values[Col.NDS] == 25
    assert template.values[Col.DESCR] == "Счет № 5"
    assert template.amount == Decimal("310")
    assert template.period == QDate(2026, 10, 1)
    assert template.due_date is not None and template.due_date.month() == 11


def test_template_is_none_without_saved_values_even_with_history(hdb):
    path = hdb.path
    document_id = make_monthly(path, "Альфа", "1", "Акт")
    assert build_monthly_template(hdb, document_id, OCTOBER) is None

    add_event(path, document_id, "100", "2026-10-05")
    assert build_monthly_template(hdb, document_id, OCTOBER) is None

    save_values(path, document_id, category=0)
    assert build_monthly_template(hdb, document_id, OCTOBER) is None


def test_template_fills_placeholders_of_saved_values(hdb):
    path = hdb.path
    document_id = make_monthly(path, "Альфа", "1", "Акт")
    save_values(path, document_id, "Аренда за {месяц} {год} г.", category=1107, nds=20, responsible=6)

    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 1))

    assert template.values[Col.NAME] == "Аренда за октябрь 2026 г."
    assert template.values[Col.CATEGORY] == 1107
    assert template.values[Col.RECEIVER] == "Альфа"


def test_template_prefers_monthly_name_over_saved_name(hdb):
    path = hdb.path
    document_id = make_monthly(path, "Альфа", "1", "Акт")
    save_values(path, document_id, "Старое название за октябрь", category=1107)
    run(path, "UPDATE contractdocument SET monthlyname = 'Аренда за {месяц} {год} г.' WHERE id = ?", document_id)

    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 1))

    assert template.values[Col.NAME] == "Аренда за октябрь 2026 г."
    assert template.values[Col.CATEGORY] == 1107

    run(path, "UPDATE contractdocument SET monthlyname = NULL WHERE id = ?", document_id)
    assert build_monthly_template(hdb, document_id, QDate(2026, 11, 1)).values[Col.NAME] == "Старое название за октябрь"


def test_template_model_is_readable_like_table_rows(hdb):
    path = hdb.path
    document_id = make_monthly(path, "Альфа", "1", "Акт", "100.5")
    save_values(path, document_id)
    run(path, "INSERT INTO event (type, contractdocument_id, receiver, name, totalamount, duedate, category) "
              "VALUES (2, ?, 'Альфа', 'Услуги', '1', '2026-10-26', 1112)", document_id)
    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 1))
    source = template_model(template)
    index = source.index(0, 0)

    def value(column):
        return index.siblingAtColumn(column).data(LiabilityTableModel.qtValueRole)

    assert value(Col.TOTALAMOUNT) == Decimal("100.5")
    assert value(Col.CONTRACTDOCUMENTID) == document_id
    assert value(Col.DUEDATE) == template.due_date
    assert FilterFlags.PAID not in value(Col.FILTERFLAGS)
    assert value(Col.RESPONSIBLE) == 0


class FakeModel:
    def __init__(self):
        self.inserted: list = []

    def insert_event(self, data):
        self.inserted.append(data)
        return 1


def test_copydoc_dialog_in_monthly_mode_creates_event_for_the_month(hdb, qapp):
    path = hdb.path
    document_id = make_monthly(path, "УП А1", "1", "Счет-акт", "310")
    save_values(path, document_id, "Услуги связи за сентябрь 2026 г.", receiver="УП А1", nds=25, responsible=1)
    run(path, "INSERT INTO event (type, contractdocument_id, receiver, name, totalamount, duedate, category, nds, paymenttype, responsible) "
              "VALUES (2, ?, 'УП А1', 'Услуги связи за сентябрь 2026 г.', '259.79', '2026-10-26', 1112, 25, 1, '1')", document_id)
    entry = next(entry for entry in hdb.load_monthly_entries(QDate(2026, 11, 1)) if entry.title.document_id == document_id)
    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 1))
    source = template_model(template)
    model = FakeModel()

    dialog = CopyDocDialog(model, hdb, None, source.index(0, 0), entry.title, monthly=template)

    assert dialog.ui.te_name.toPlainText() == "Услуги связи за октябрь 2026 г."
    assert dialog.ui.dsb_amount.value() == 310
    assert dialog.ui.cmb_month.currentData() == 10 and dialog.ui.spb_year.value() == 2026
    assert dialog.ui.de_duedate.date() == template.due_date

    dialog.check_integrity = lambda: True
    dialog.accept()

    (data,) = model.inserted
    assert data[3] == document_id and data[4] == 1112 and data[6] == "Услуги связи за октябрь 2026 г."
    assert data[7] == "310.0" and data[9] == template.due_date.toString("yyyy-MM-dd")


@pytest.fixture
def notices(monkeypatch):
    texts: list = []

    class FakeBox:
        def __init__(self, text, *args, **kwargs):
            texts.append(text)

        def exec(self):
            return 0

    monkeypatch.setattr("gui.monthlydialog.ErrorInfoMessageBox", FakeBox)
    return texts


def test_monthly_dialog_lists_filters_and_creates(hdb, qapp, notices):
    path = hdb.path
    make_monthly(path, "Альфа", "1", "Акт связи")
    paid_id = make_monthly(path, "Бета", "2", "Акт аренды", "100")
    event_id = add_event(path, paid_id, "100", QDate.currentDate().toString("yyyy-MM-dd"))
    add_payment(path, event_id, "2026-10-02", "100")
    calls: list = []

    def create_event(entry, month, full_form, parent):
        calls.append((entry.title.contractor_name, month, full_form))
        return False

    dialog = MonthlyDialog(hdb, create_event)
    table = dialog.ui.tbl_monthly

    assert table.rowCount() == 2
    assert dialog.ui.la_summary.text() == "Не создано: 1 из 2"
    assert [table.item(row, 4).text() for row in range(2)] == ["не создан", "оплачен"]
    assert table.item(0, 2).text() == "по счёту" and not table.item(0, 2).font().italic()
    assert table.item(0, 3).text() != "—" and table.item(0, 3).font().italic()
    assert table.item(1, 3).text() == QDate.currentDate().toString("dd.MM.yyyy") and not table.item(1, 3).font().italic()
    assert table.item(1, 2).text() == "100,00" and not table.item(1, 2).font().italic()

    dialog.ui.chb_onlymissing.setChecked(True)
    assert table.rowCount() == 1 and table.item(0, 0).text() == "Альфа"

    table.selectRow(0)
    dialog.ui.pb_create.click()
    assert calls == [("Альфа", dialog.month, True)]
    assert notices == [MonthlyDialog.NO_SAVED_VALUES_TEXT]

    month = dialog.month
    dialog.ui.tb_next.click()
    assert dialog.month == month.addMonths(1)


def test_monthly_dialog_italic_amount_for_missing_with_fixed_amount(hdb, qapp):
    make_monthly(hdb.path, "Альфа", "1", "Акт связи", "310")
    table = MonthlyDialog(hdb, lambda *args: False).ui.tbl_monthly

    assert table.item(0, 2).text() == "310,00" and table.item(0, 2).font().italic()


@pytest.mark.parametrize("days_type, text", [("WORKING", "+5 раб. дн."), ("BANKING", "+5 банк. дн."), ("CALENDAR", "+5 кал. дн.")])
def test_monthly_dialog_relative_term_for_missing(hdb, qapp, days_type, text):
    _, _, document_id = add_chain(hdb.path, "Альфа", "1", "Акт связи")
    run(hdb.path, "UPDATE contractdocument SET monthly = 1 WHERE id = ?", document_id)
    run(hdb.path, "INSERT INTO contractpaymentterm (document_id, payment_type, days_count, days_type, has_calendar_condition, "
                  "month_day, month_type) VALUES (?, 'RELATIVE', 5, ?, 1, 25, 'NEXT')", document_id, days_type)
    table = MonthlyDialog(hdb, lambda *args: False).ui.tbl_monthly

    assert table.item(0, 3).text() == text and table.item(0, 3).font().italic()


def test_monthly_dialog_hides_and_restores(hdb, qapp):
    path = hdb.path
    make_monthly(path, "Альфа", "1", "Акт связи")
    make_monthly(path, "Бета", "2", "Акт аренды")
    created_id = make_monthly(path, "Гамма", "3", "Акт охраны", "100")
    add_event(path, created_id, "100", QDate.currentDate().toString("yyyy-MM-dd"))
    dialog = MonthlyDialog(hdb, lambda *args: False, lambda event, parent: True)
    table = dialog.ui.tbl_monthly

    table.selectRow(0)
    assert dialog.ui.pb_hide.text() == "Скрыть платеж" and dialog.ui.pb_hide.isEnabled()
    dialog.ui.pb_hide.click()
    assert [entry.title.contractor_name for entry in dialog.shown] == ["Бета", "Гамма"]
    assert dialog.ui.la_summary.text() == "Не создано: 1 из 2 (скрыто 1)"

    table.selectRow(1)
    assert dialog.ui.pb_create.text() == "Открыть платеж" and not dialog.ui.pb_hide.isEnabled()

    dialog.ui.chb_hidden.setChecked(True)
    assert [entry.title.contractor_name for entry in dialog.shown] == ["Альфа"]
    assert dialog.ui.pb_hide.text() == "Вернуть платеж" and dialog.ui.pb_hide.isEnabled()
    assert dialog.ui.pb_create.text() == "Создать платеж" and not dialog.ui.pb_create.isEnabled()

    dialog.ui.pb_hide.click()
    assert dialog.shown == [] and dialog.ui.stk_monthly.currentWidget() is dialog.ui.page_empty

    dialog.ui.chb_hidden.setChecked(False)
    assert table.rowCount() == 3 and dialog.ui.la_summary.text() == "Не создано: 2 из 3"


def test_hidden_monthly_is_remembered_per_month_and_expires(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    HiddenMonthly(settings).hide(5, OCTOBER)

    assert HiddenMonthly(settings).is_hidden(5, OCTOBER)
    assert not HiddenMonthly(settings).is_hidden(5, QDate(2026, 11, 1))
    assert not HiddenMonthly(settings).is_hidden(6, OCTOBER)

    today = QDate.currentDate()
    settings.setValue(HiddenMonthly.KEY, json.dumps({
        "7:2026-01": today.addDays(-366).toString(Qt.DateFormat.ISODate),
        "8:2026-02": today.addDays(-364).toString(Qt.DateFormat.ISODate),
    }))
    fresh = HiddenMonthly(settings)

    assert not fresh.is_hidden(7, QDate(2026, 1, 1)) and fresh.is_hidden(8, QDate(2026, 2, 1))
    assert list(json.loads(settings.value(HiddenMonthly.KEY))) == ["8:2026-02"]


def test_monthly_dialog_enter_creates_or_opens_and_does_not_close(hdb, qapp, notices):
    path = hdb.path
    make_monthly(path, "Альфа", "1", "Акт связи")
    created_id = make_monthly(path, "Бета", "2", "Акт аренды", "100")
    event_id = add_event(path, created_id, "100", QDate.currentDate().toString("yyyy-MM-dd"))
    created: list = []
    opened: list = []
    dialog = MonthlyDialog(hdb, lambda entry, month, full, parent: created.append(entry.title.contractor_name) or False,
                           lambda event, parent: opened.append(event) or True)
    dialog.show()
    table = dialog.ui.tbl_monthly

    table.selectRow(0)
    table.setFocus()
    QTest.keyClick(table, Qt.Key.Key_Return)
    table.selectRow(1)
    QTest.keyClick(table, Qt.Key.Key_Return)

    assert dialog.isVisible()
    assert created == ["Альфа"] and opened == [event_id]
    assert not dialog.ui.pb_close.autoDefault()


def test_monthly_dialog_create_button_and_empty_state(hdb, qapp):
    path = hdb.path
    save_values(path, make_monthly(path, "Альфа", "1", "Акт связи"))
    save_values(path, make_monthly(path, "Бета", "2", "Акт аренды"))
    calls: list = []
    dialog = MonthlyDialog(hdb, lambda entry, month, full, parent: calls.append(entry.title.contractor_name) or False)
    table = dialog.ui.tbl_monthly

    table.selectRow(1)
    dialog.ui.pb_create.click()

    assert dialog.selected_entry().title.contractor_name == "Бета" and calls == ["Бета"]
    assert dialog.ui.pb_create.text() == "Создать платеж"

    run(path, "UPDATE contractdocument SET monthly = 0")
    dialog.reload()
    assert dialog.ui.stk_monthly.currentWidget() is dialog.ui.page_empty
    assert "Нет документов" in dialog.ui.la_empty.text()


def test_monthly_dialog_quick_create_needs_saved_values(hdb, qapp, notices):
    path = hdb.path
    make_monthly(path, "Альфа", "1", "Акт связи")
    ready_id = make_monthly(path, "Бета", "2", "Акт аренды")
    save_values(path, ready_id)
    calls: list = []
    dialog = MonthlyDialog(hdb, lambda entry, month, full, parent: calls.append((entry.title.contractor_name, full)) or False)
    table = dialog.ui.tbl_monthly

    assert [entry.has_saved_values for entry in dialog.shown] == [False, True]

    dialog.activate_row(table.model().index(0, 0))
    assert notices == [MonthlyDialog.NO_SAVED_VALUES_TEXT]
    dialog.activate_row(table.model().index(1, 0))
    assert notices == [MonthlyDialog.NO_SAVED_VALUES_TEXT]
    assert calls == [("Альфа", True), ("Бета", False)]


def test_monthly_entry_is_one_row_per_document(hdb):
    path = hdb.path
    document_id = make_monthly(path, "Альфа", "1", "Акт связи")
    first = add_event(path, document_id, "100", "2026-10-05")
    add_event(path, document_id, "50", "2026-10-20")
    add_payment(path, first, "2026-10-06", "100")

    (entry,) = hdb.load_monthly_entries(OCTOBER)

    assert entry.event.event_id == first and entry.event.due_date == QDate(2026, 10, 5)
    assert entry.state == MonthlyState.PAID


def test_template_remembers_month_and_last_amount(hdb):
    path = hdb.path
    document_id = make_monthly(path, "УП А1", "1", "Счет-акт")
    save_values(path, document_id, "За январь и февраль")
    run(path, "INSERT INTO event (type, contractdocument_id, receiver, name, totalamount, duedate, category) "
              "VALUES (2, ?, 'УП А1', 'За январь и февраль', '259.79', '2026-10-26', 1112)", document_id)

    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 20))

    assert template.month == QDate(2026, 11, 1)
    assert template.last_amount == Decimal("259.79")
    assert template.name_ambiguous


def test_copydoc_monthly_warns_when_due_date_leaves_month(hdb, qapp):
    path = hdb.path
    document_id = make_monthly(path, "УП А1", "1", "Счет-акт", "310")
    save_values(path, document_id)
    run(path, "INSERT INTO event (type, contractdocument_id, receiver, name, totalamount, duedate, category) "
              "VALUES (2, ?, 'УП А1', 'Услуги', '259.79', '2026-10-26', 1112)", document_id)
    entry = next(entry for entry in hdb.load_monthly_entries(QDate(2026, 11, 1)) if entry.title.document_id == document_id)
    template = build_monthly_template(hdb, document_id, QDate(2026, 11, 1))
    source = template_model(template)
    dialog = CopyDocDialog(FakeModel(), hdb, None, source.index(0, 0), entry.title, monthly=template)

    assert "Ноябрь 2026" in dialog.windowTitle()
    assert dialog.ui.la_amounthint.text() == "В прошлый раз: 259,79"
    assert dialog.monthly_warnings() == ""

    dialog.ui.de_duedate.setDate(QDate(2026, 12, 3))

    assert "выходит за Ноябрь 2026" in dialog.monthly_warnings()
