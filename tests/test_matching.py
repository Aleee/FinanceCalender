from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import gui.feedialog as feedialog
from base.feeparser import DailyFees
from base.liability import LiabilityCategory
from base.payment import PaymentEntry
from base.paymentmacther import (CONTRACT_TAX_DESCRIPTION, DateDiscrepancy, ReconciliationResult, _pair_probable_matches,
                                  _regroup_contract_payments, extract_statement_payments, pair_confidence)
from tests.test_audit_fixes import query_all
from tests.test_readpath import add_event, add_payment, db_file, models, open_models  # noqa: F401


def entry(amount: str, receiver: str, descr: str = "", **ids) -> PaymentEntry:
    return PaymentEntry(Decimal(amount), f"{descr} ({receiver})", receiver, details=descr, **ids)


def test_same_counterparty_with_other_word_order_and_small_difference_is_paired():
    statement = [entry("1846.00", "САНИТАРНАЯ ОБОРОНА ЗАО", "ТТН 2156811 СРЕДСТВО ДЕЗИНФИЦИРУЮЩЕЕ")]
    calendar = [entry("1828.00", "ЗАО Санитарная оборона", "Средство дезинфицирующее")]
    pairs, rest_statement, rest_calendar = _pair_probable_matches(statement, calendar)
    assert [(p.statement, p.calendar) for p in pairs] == [(statement[0], calendar[0])]
    assert pairs[0].difference == Decimal("18.00")
    assert rest_statement == [] and rest_calendar == []


def test_legal_form_and_hyphen_do_not_prevent_pairing():
    pairs, _, _ = _pair_probable_matches([entry("1033.75", "ГК ЭКСПЕРТ ОПТ")],
                                         [entry("1031.75", "ООО ГК Эксперт-ОПТ")])
    assert len(pairs) == 1


def test_document_number_and_date_pair_entries_with_different_names():
    statement = entry("1000.00", "Ромашка-Торг", "ТТН 123456 ОТ 01.09.2026 бахилы")
    calendar = entry("970.00", "ООО Василёк", "бахилы ТТН № 123456 от 01.09.2026")
    assert pair_confidence(statement, calendar) > 0.7


def test_other_document_number_does_not_help():
    statement = entry("1000.00", "Ромашка-Торг", "ТТН 111 ОТ 01.09.2026")
    calendar = entry("990.00", "ООО Василёк", "ТТН № 222 от 01.09.2026")
    assert pair_confidence(statement, calendar) < 0.35


def test_close_but_not_identical_names_still_pair():
    assert pair_confidence(entry("1000.00", "БЕЛТЕХНОИМПОРТ ООО"), entry("970.00", "ООО Белтехноимпорт-Сервис")) > 0.6
    assert pair_confidence(entry("1000.00", "ООО Ромошка"), entry("980.00", "ООО Ромашка")) > 0.5


def test_confidence_decreases_with_amount_difference_up_to_ten_percent():
    statement = entry("1000.00", "ООО Ромашка")
    confidences = [pair_confidence(statement, entry(amount, "ООО Ромашка")) for amount in ("1000.01", "980.00", "915.00")]
    assert confidences[0] > confidences[1] > confidences[2] > 0
    assert pair_confidence(statement, entry("890.00", "ООО Ромашка")) == 0


def test_only_similar_text_is_not_enough():
    assert pair_confidence(entry("1000.00", "ООО Ромашка", "бахилы полиэтиленовые"),
                           entry("990.00", "ООО Василёк", "Бахилы полиэтиленовые")) < 0.35


def test_big_difference_is_not_paired():
    pairs, rest_statement, rest_calendar = _pair_probable_matches([entry("1500.00", "ООО Ромашка")],
                                                                  [entry("1000.00", "ООО Ромашка")])
    assert pairs == [] and len(rest_statement) == 1 and len(rest_calendar) == 1


def test_other_counterparty_is_not_paired():
    pairs, _, _ = _pair_probable_matches([entry("1000.00", "ООО Ромашка")], [entry("1010.00", "ООО Василёк")])
    assert pairs == []


def test_entries_without_receiver_are_not_paired():
    pairs, _, _ = _pair_probable_matches([entry("1156.92", "", "Комиссии в поступлениях")],
                                         [entry("1150.00", "", "Комиссии")])
    assert pairs == []


def test_each_entry_is_used_once_and_closest_amount_wins():
    statement = [entry("1000.00", "ООО Ромашка")]
    calendar = [entry("1030.00", "ООО Ромашка"), entry("1002.00", "ООО Ромашка")]
    pairs, rest_statement, rest_calendar = _pair_probable_matches(statement, calendar)
    assert len(pairs) == 1 and pairs[0].calendar is calendar[1]
    assert 0 < pairs[0].confidence <= 1
    assert rest_statement == [] and rest_calendar == [calendar[0]]


def test_summary_counts_paired_entries_as_discrepancies():
    pair_statement, pair_calendar = entry("1846.00", "ООО Ромашка"), entry("1828.00", "ООО Ромашка")
    pairs, _, _ = _pair_probable_matches([pair_statement], [pair_calendar])
    result = ReconciliationResult((date(2026, 10, 10),) * 2,
                                  [DateDiscrepancy(date(2026, 10, 10), [entry("5.00", "")], [], pairs)])
    assert result.only_in_statement_count == 2
    assert result.only_in_statement_sum == Decimal("1851.00")
    assert result.only_in_calendar_count == 1
    assert result.only_in_calendar_sum == Decimal("1828.00")


def test_calendar_entries_carry_ids_for_correction(db_file, shared_dbh, open_models):
    event_id = add_event(db_file, total="1828.0", receiver="ЗАО Санитарная оборона")
    payment_id = add_payment(db_file, event_id, "2026-10-10", "1828.0")
    open_models(db_file)
    entries = shared_dbh.get_paymentsum_for_period(date(2026, 10, 10), date(2026, 10, 10))[date(2026, 10, 10)]
    assert (entries[0].payment_id, entries[0].event_id, entries[0].receiver) == (
        payment_id, event_id, "ЗАО Санитарная оборона")


def test_correction_changes_payment_and_event_sum(db_file, shared_dbh, open_models):
    event_id = add_event(db_file, total="1828.0")
    payment_id = add_payment(db_file, event_id, "2026-10-10", "1828.0")
    open_models(db_file)
    assert shared_dbh.correct_payment_sum(payment_id, Decimal("1846.00"))
    assert Decimal(query_all(db_file, "SELECT sum FROM payment WHERE id = ?", payment_id)[0][0]) == Decimal("1846.00")
    assert Decimal(query_all(db_file, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("1846.00")


def test_correction_keeps_remainder_of_partially_paid_event(db_file, shared_dbh, open_models):
    event_id = add_event(db_file, total="5000.00")
    payment_id = add_payment(db_file, event_id, "2026-10-10", "1000.00")
    add_payment(db_file, event_id, "2026-10-09", "500.00")
    open_models(db_file)
    assert shared_dbh.correct_payment_sum(payment_id, Decimal("980.00"))
    assert Decimal(query_all(db_file, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("4980.00")


def test_correction_of_missing_payment_changes_nothing(db_file, shared_dbh, open_models):
    event_id = add_event(db_file, total="100.00")
    open_models(db_file)
    assert not shared_dbh.correct_payment_sum(9999, Decimal("90.00"))
    assert Decimal(query_all(db_file, "SELECT totalamount FROM event WHERE id = ?", event_id)[0][0]) == Decimal("100.00")


def fee_categories(total: str):
    daily = {date(2026, 10, 10): DailyFees(1, Decimal(total), [Decimal(total)])}
    return [(daily, LiabilityCategory.BANKING, ""), ({}, LiabilityCategory.COMMISSION, "")]


def confirm_fee_totals(monkeypatch, statement_total, calculated_total) -> list[str]:
    asked: list[str] = []

    class FakeYesNo:
        NO_RETURN_VALUE = 3

        def __init__(self, text):
            asked.append(text)

        def exec(self):
            return 2

    monkeypatch.setattr(feedialog, "YesNoMessagebox", FakeYesNo)
    dialog = SimpleNamespace(statement_fee_totals=statement_total)
    assert feedialog.FeeDialog._confirm_fee_totals(dialog, fee_categories(calculated_total))
    return asked


def test_matching_fee_totals_without_difference_do_not_warn(monkeypatch):
    totals = {(date(2026, 10, 10), LiabilityCategory.BANKING): Decimal("1156.92")}
    assert confirm_fee_totals(monkeypatch, totals, "1156.92") == []


def test_fee_totals_difference_asks_for_confirmation(monkeypatch):
    totals = {(date(2026, 10, 10), LiabilityCategory.BANKING): Decimal("1157.92")}
    asked = confirm_fee_totals(monkeypatch, totals, "1156.92")
    assert len(asked) == 1 and "10.10.2026" in asked[0]


def test_standalone_fee_dialog_does_not_check_totals(monkeypatch):
    assert confirm_fee_totals(monkeypatch, None, "1156.92") == []


def statement_with(tmp_path, *descriptions_and_debits: tuple[str, str]):
    rows = [[""] * 10 for _ in range(8)]
    rows[0][0] = "ВЫПИСКА ПО СЧЕТУ С 06.10.2026 ПО 06.10.2026"
    for number, (descr, debit) in enumerate(descriptions_and_debits):
        rows.append(["06.10.2026", str(number), "1", "", "", "100", "Контрагент", debit, "0,00", descr])
    path = tmp_path / "statement.csv"
    path.write_text("\n".join(";".join(row) for row in rows) + "\n", encoding="windows-1251")
    settings = {"CSVparser/columnstoparse": "0,2,5,8,7,9,6", "CSVparser/rowperiod": "1",
                "CSVparser/rowtransactionstart": "9", "CSVparser/knownunp": "", "CSVparser/patterns": "",
                "CSVparser/nomatchpatterns": ""}
    dbh = SimpleNamespace(get_setting=lambda key, default="": settings.get(key, default))
    return extract_statement_payments(str(path), dbh).by_date[date(2026, 10, 6)]


def test_contract_taxes_are_not_included_in_payroll(tmp_path):
    entries = statement_with(tmp_path,
                             ("ПОДОХОДНЫЙ НАЛОГ ПО ДОГОВОРУ ПОДРЯДА ЗА СЕНТЯБРЬ 2026", "105,95"),
                             ("ОТЧИСЛЕНИЯ В ФСЗН ПО ДОГОВОРУ ПОДРЯДА ЗА СЕНТЯБРЬ 2026", "285,25"),
                             ("ПОДОХОДНЫЙ НАЛОГ ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026", "1 117,85"),
                             ("ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026", "6 430,44"),
                             ("ВЫПЛАТЫ ПО ДОГОВОРАМ ПОДРЯДА НА СЧЕТ ИВАНОВ", "700,90"))
    amounts = {entry.descr.removesuffix(" (Контрагент)"): entry.amount for entry in entries}
    assert amounts["Налоги и взносы по договорам подряда"] == Decimal("391.20")
    assert amounts["Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"] == Decimal("7548.29")
    assert amounts["ВЫПЛАТЫ ПО ДОГОВОРАМ ПОДРЯДА НА СЧЕТ ИВАНОВ"] == Decimal("700.90")


def test_material_aid_is_included_in_payroll(tmp_path):
    entries = statement_with(tmp_path, ("МАТЕРИАЛЬНАЯ ПОМОЩЬ К ОТПУСКУ ЗА ОКТЯБРЬ", "1 000,00"),
                             ("ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026", "6 430,44"))
    assert [(e.descr, e.amount) for e in entries] == [
        ("Выплаты работникам (зарплата/отпускные/ФСЗН/налог)", Decimal("7430.44"))]


def contract_case(net="700.90", tax="391.20", gross="815.00", insurance="277.10"):
    statement = [entry(net, "ЮРИНОК ГЛЕБ КОНСТАНТИНОВИЧ", "ВЫПЛАТЫ ПО ДОГОВОРАМ ПОДРЯДА"),
                 PaymentEntry(Decimal(tax), CONTRACT_TAX_DESCRIPTION)]
    calendar = [entry(gross, "Юринок Г.К.", "Услуги по семинару"),
                PaymentEntry(Decimal(insurance), "ФСЗН (Главное управление Минфина)", "Главное управление Минфина")]
    return statement, calendar


def test_contract_payments_with_equal_totals_are_regrouped():
    statement, calendar = contract_case()
    groups, rest_statement, rest_calendar = _regroup_contract_payments(date(2026, 10, 6), statement, calendar)
    assert len(groups) == 1 and rest_statement == [] and rest_calendar == []
    assert groups[0].contracts == [(statement[0], calendar[0])]
    assert groups[0].explanation.splitlines() == [
        "Юринок Г.К.: по договору 815,00, выплачено 700,90, удержано 114,10 (14% - ПН/СТР)",
        "ФСЗН в календаре: 277,10 (34% от суммы договора)",
        "Выписка: 700,90 (выплачено) + 391,20 (ФСЗН + ПН/СТР) = 1 092,10",
        "Календарь: 815,00 (выплачено + ПН/СТР) + 277,10 (ФСЗН) = 1 092,10",
    ]


def test_contract_payments_with_different_totals_are_not_regrouped():
    statement, calendar = contract_case(insurance="277.00")
    groups, rest_statement, rest_calendar = _regroup_contract_payments(date(2026, 10, 6), statement, calendar)
    assert groups == [] and rest_statement == statement and rest_calendar == calendar


def test_regrouping_needs_the_same_counterparty():
    statement, calendar = contract_case()
    calendar[0] = entry("815.00", "ООО Василёк", "Услуги по семинару")
    assert _regroup_contract_payments(date(2026, 10, 6), statement, calendar)[0] == []


def test_regrouping_needs_contract_tax_entry_in_statement():
    statement, calendar = contract_case()
    assert _regroup_contract_payments(date(2026, 10, 6), statement[:1], calendar)[0] == []


def test_group_key_does_not_depend_on_entry_order():
    statement, calendar = contract_case()
    first = _regroup_contract_payments(date(2026, 10, 6), statement, calendar)[0][0]
    second = _regroup_contract_payments(date(2026, 10, 6), statement[::-1], calendar[::-1])[0][0]
    assert first.key == second.key
