import re
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import gui.feedialog as feedialog
from base.feeparser import DailyFees
from base.formatting import records_word
from base.liability import LiabilityCategory
from base.payment import PaymentEntry
from base.paymentmacther import (CONTRACT_TAX_DESCRIPTION, DateDiscrepancy, ProbablePair, ReconciliationMarks,
                                  ReconciliationResult, _merge_split_payments, _pair_probable_matches,
                                  _regroup_contract_payments,
                                  extract_statement_payments, pair_confidence, pair_reasons,
                                  reconcile_statement_with_calendar)
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


def test_confidence_decreases_with_amount_difference_up_to_fifteen_percent():
    statement = entry("1000.00", "ООО Ромашка")
    confidences = [pair_confidence(statement, entry(amount, "ООО Ромашка")) for amount in ("1000.01", "980.00", "915.00")]
    assert confidences[0] > confidences[1] > confidences[2] > 0
    assert pair_confidence(statement, entry("840.00", "ООО Ромашка")) == 0


def test_document_number_allows_bigger_difference_with_stronger_penalty():
    statement = entry("891.25", "Ромашка-Торг", "договор 2026/080 от 01.12.2025")
    close = entry("782.00", "ООО Василёк", "договор 2026/080 от 01.12.2025")
    far = entry("700.00", "ООО Василёк", "договор 2026/080 от 01.12.2025")
    assert pair_confidence(statement, close) >= 0.35
    assert pair_confidence(statement, close) > pair_confidence(statement, far) > 0
    assert pair_confidence(statement, entry("700.00", "ООО Ромашка-Торг")) == 0
    assert pair_confidence(statement, entry("500.00", "ООО Василёк", "договор 2026/080 от 01.12.2025")) == 0


def test_one_similar_word_is_not_enough_but_several_are():
    statement = entry("1000.00", "ООО Ромашка", "бахилы полиэтиленовые одноразовые")
    assert pair_confidence(statement, entry("990.00", "ООО Василёк", "Бахилы")) < 0.35
    assert pair_confidence(statement, entry("990.00", "ООО Василёк", "Бахилы полиэтиленовые одноразовые")) >= 0.35


def test_big_difference_is_not_paired():
    pairs, rest_statement, rest_calendar = _pair_probable_matches([entry("1500.00", "ООО Ромашка")],
                                                                  [entry("1000.00", "ООО Ромашка")])
    assert pairs == [] and len(rest_statement) == 1 and len(rest_calendar) == 1


def test_other_counterparty_is_not_paired():
    pairs, _, _ = _pair_probable_matches([entry("1000.00", "ООО Ромашка")], [entry("1010.00", "ООО Василёк")])
    assert pairs == []


def test_entries_without_receiver_are_not_paired():
    pairs, _, _ = _pair_probable_matches([entry("1156.92", "", "Комиссии, относимые на банковские расходы")],
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


def test_proposal_entries_count_includes_pairs_and_groups():
    pair_statement, pair_calendar = entry("1846.00", "ООО Ромашка"), entry("1828.00", "ООО Ромашка")
    pairs, _, _ = _pair_probable_matches([pair_statement], [pair_calendar])
    statement, calendar = contract_case()
    groups, _, _ = _regroup_contract_payments(date(2026, 10, 6), statement, calendar)
    result = ReconciliationResult((date(2026, 10, 6),) * 2,
                                  [DateDiscrepancy(date(2026, 10, 6), [], [], pairs, groups)])
    assert result.proposal_entries_count == 2 + len(statement) + len(calendar)


def test_records_word_agrees_with_number():
    words = {1: "запись", 2: "записи", 4: "записи", 5: "записей", 11: "записей", 12: "записей", 21: "запись",
             22: "записи", 25: "записей", 111: "записей"}
    assert {count: records_word(count) for count in words} == words


def test_calendar_entries_carry_ids_for_correction(db_file, shared_dbh, open_models):
    event_id = add_event(db_file, total="1828.0", receiver="ЗАО Санитарная оборона")
    payment_id = add_payment(db_file, event_id, "2026-10-10", "1828.0")
    open_models(db_file)
    entries = shared_dbh.get_paymentsum_for_period(date(2026, 10, 10), date(2026, 10, 10))[date(2026, 10, 10)]
    assert (entries[0].payment_id, entries[0].event_id, entries[0].receiver) == (
        payment_id, event_id, "ЗАО Санитарная оборона")


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


def statement_with(tmp_path, *descriptions_and_debits: tuple[str, str], extra_settings: dict | None = None):
    rows = [[""] * 10 for _ in range(8)]
    rows[0][0] = "ВЫПИСКА ПО СЧЕТУ С 06.10.2026 ПО 06.10.2026"
    for number, (descr, debit) in enumerate(descriptions_and_debits):
        rows.append(["06.10.2026", str(number), "1", "", "", "100", "Контрагент", debit, "0,00", descr])
    path = tmp_path / "statement.csv"
    path.write_text("\n".join(";".join(row) for row in rows) + "\n", encoding="windows-1251")
    settings = {"CSVparser/columnstoparse": "0,2,5,8,7,9,6", "CSVparser/rowperiod": "1",
                "CSVparser/rowtransactionstart": "9", "CSVparser/knownunp": "", "CSVparser/patterns": "",
                "CSVparser/nomatchpatterns": "", **(extra_settings or {})}
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


def test_sole_proprietor_tax_is_not_included_in_payroll(tmp_path):
    entries = statement_with(tmp_path,
                             ("ПОДОХОДНЫЙ НАЛОГ ПО ИП ЛЕМЕНКОВУ С.А. ПО ДОГОВОРУ АИ003 ОТ 01.12.2026 ПО СРОКУ 12.10.2026", "98,72"),
                             ("ПОДОХОДНЫЙ НАЛОГ ИЗ ОКОНЧ.РАСЧЕТА И ОТПУСКНЫХ ЗА ОКТЯБРЬ 2026", "1 224,14"),
                             ("ОТПУСКНЫЕ ЗА ОКТЯБРЬ, 2026", "6 763,26"))
    amounts = {entry.descr.removesuffix(" (Контрагент)"): entry.amount for entry in entries}
    assert amounts["Налоги и взносы по договорам подряда"] == Decimal("98.72")
    assert amounts["Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"] == Decimal("7987.40")


def test_material_aid_is_included_in_payroll(tmp_path):
    entries = statement_with(tmp_path, ("МАТЕРИАЛЬНАЯ ПОМОЩЬ К ОТПУСКУ ЗА ОКТЯБРЬ", "1 000,00"),
                             ("ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026", "6 430,44"))
    assert [(e.descr, e.amount) for e in entries] == [
        ("Выплаты работникам (зарплата/отпускные/ФСЗН/налог)", Decimal("7430.44"))]


def test_default_payroll_patterns_cover_word_forms(tmp_path):
    entries = statement_with(tmp_path,
                             ("ОТЧИСЛЕНИЯ НА ППС ИЗ ЗАРАБОТНОЙ ПЛАТЫ ЗА СЕНТЯБРЬ 2026", "376,31"),
                             ("ОТЧИСЛЕНИЯ ОТ ЧЛЕНСКИХ ВЗНОСОВ ИЗ ЗАРПЛАТЫ ЗА СЕНТЯБРЬ 2026", "4 256,01"),
                             ("ОПЛАТА ЧЛЕНСКИХ ВЗНОСОВ ЗА ОКТЯБРЬ 2026", "300,00"))
    amounts = {entry.descr.removesuffix(" (Контрагент)"): entry.amount for entry in entries}
    assert amounts["Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"] == Decimal("4632.32")
    assert amounts["ОПЛАТА ЧЛЕНСКИХ ВЗНОСОВ ЗА ОКТЯБРЬ 2026"] == Decimal("300.00")


def test_payroll_patterns_are_taken_from_settings(tmp_path):
    entries = statement_with(tmp_path,
                             ("ХОЗЯЙСТВЕННЫЕ РАСХОДЫ ЗА ОКТЯБРЬ СОГЛ. СПИСКУ N 194", "194,14"),
                             ("ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026", "6 430,44"),
                             extra_settings={"CSVparser/payrollpatterns": " Хозяйственные расходы ,, "})
    amounts = {entry.descr.removesuffix(" (Контрагент)"): entry.amount for entry in entries}
    assert amounts["Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"] == Decimal("194.14")
    assert amounts["ОТПУСКНЫЕ ЗА ОКТЯБРЬ 2026"] == Decimal("6430.44")


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


FEE_DATE = date(2026, 10, 15)


def split_case():
    statement = [entry("1026.46", "ЮРСПЕКТР ООО", "ОПЛАТА ПО СЧЕТУ 57041 ОТ 08.09.2026"),
                 entry("2.00", "ЮРСПЕКТР ООО", "ОПЛАТА ПО СЧЕТУ 57041 ОТ 08.09.2026 (ДОПЛАТА)")]
    calendar = [entry("1028.46", "ООО ЮрСпектр", "Информационные услуги Счет на оплату № 57041 от 08.09.2026")]
    return statement, calendar


def test_one_calendar_payment_paid_in_parts_is_grouped():
    statement, calendar = split_case()
    groups, rest_statement, rest_calendar = _merge_split_payments(FEE_DATE, statement, calendar)
    assert len(groups) == 1 and rest_statement == [] and rest_calendar == []
    assert groups[0].statement == statement and groups[0].calendar == calendar
    assert groups[0].explanation.splitlines() == [
        "ООО ЮрСпектр: один платёж в календаре оплачен несколькими платежами в выписке",
        "Выписка: 1 026,46 + 2,00 = 1 028,46",
        "Календарь: 1 028,46 = 1 028,46",
    ]


def test_one_statement_payment_for_several_calendar_payments_is_grouped():
    statement, calendar = split_case()
    groups, rest_statement, rest_calendar = _merge_split_payments(FEE_DATE, calendar, statement)
    assert len(groups) == 1 and rest_statement == [] and rest_calendar == []
    assert groups[0].statement == calendar and groups[0].calendar == statement
    assert groups[0].explanation.splitlines()[0] == (
        "ООО ЮрСпектр: один платёж в выписке соответствует нескольким платежам в календаре")


def test_split_with_different_total_is_not_grouped():
    statement, calendar = split_case()
    statement[1] = entry("2.10", "ЮРСПЕКТР ООО")
    groups, rest_statement, rest_calendar = _merge_split_payments(FEE_DATE, statement, calendar)
    assert groups == [] and rest_statement == statement and rest_calendar == calendar


def test_split_needs_the_same_counterparty():
    statement, calendar = split_case()
    statement[1] = entry("2.00", "ООО Василёк")
    assert _merge_split_payments(FEE_DATE, statement, calendar)[0] == []


def test_split_takes_only_needed_parts():
    statement, calendar = split_case()
    extra = entry("5.00", "ЮРСПЕКТР ООО")
    groups, rest_statement, _ = _merge_split_payments(FEE_DATE, statement + [extra], calendar)
    assert len(groups) == 1 and rest_statement == [extra]


def test_split_ignores_fee_entries():
    statement, calendar = split_case()
    statement[1].fee_category = LiabilityCategory.BANKING
    assert _merge_split_payments(FEE_DATE, statement, calendar)[0] == []


def test_rejected_split_returns_entries_to_the_lists():
    statement, calendar = split_case()
    group = _merge_split_payments(FEE_DATE, statement, calendar)[0][0]
    groups, rest_statement, rest_calendar = _merge_split_payments(FEE_DATE, statement, calendar, rejected={group.key})
    assert groups == [] and rest_statement == statement and rest_calendar == calendar


def test_year_is_not_a_document_number():
    statement = entry("1000.00", "Ромашка-Торг", "за октябрь 2026")
    calendar = entry("990.00", "ООО Василёк", "услуги 2026")
    assert pair_confidence(statement, calendar) == 0


def test_several_matching_words_are_strong_evidence_even_in_long_statement_text():
    statement = entry("891.25", "Банк", "лицензия помощник сайт mrt оплата по договору поставки согласно приложению "
                                      "дополнительному соглашению реквизитам контрагента")
    calendar = entry("890.00", "ИП Иванов", "Лицензия помощник на сайт mrt")
    two_words = entry("890.00", "ИП Иванов", "Лицензия помощник")
    assert pair_confidence(statement, calendar) > pair_confidence(statement, two_words) > 0
    assert pair_confidence(statement, calendar) >= 0.35


def test_generic_words_and_months_are_not_evidence():
    statement = entry("1000.00", "Банк", "перевод по договору за услуги сентябрь оказанные согласно акту")
    calendar = entry("1000.00", "ООО Василёк", "Услуги за сентябрь по договору")
    assert pair_confidence(statement, calendar) == 0


def test_document_number_with_other_separators_is_the_same():
    statement = entry("1000.00", "Банк", "по договору № 24-06/01/136 от 27.06.2025")
    calendar = entry("1000.00", "ООО Василёк", "Кредитный договор № 24-06-01/136 от 27.06.2025")
    assert pair_confidence(statement, calendar) >= 0.9


def reconcile_case(tmp_path, statement_rows, calendar_rows, marks=None):
    rows = [[""] * 10 for _ in range(8)]
    rows[0][0] = "ВЫПИСКА ПО СЧЕТУ С 01.10.2026 ПО 10.10.2026"
    for number, (day, debit, receiver, descr) in enumerate(statement_rows):
        rows.append([f"{day:02d}.10.2026", str(number), "1", "", "", "100", receiver, debit, "0,00", descr])
    path = tmp_path / "statement.csv"
    path.write_text("\n".join(";".join(row) for row in rows) + "\n", encoding="windows-1251")
    settings = {"CSVparser/columnstoparse": "0,2,5,8,7,9,6", "CSVparser/rowperiod": "1",
                "CSVparser/rowtransactionstart": "9", "CSVparser/knownunp": "", "CSVparser/patterns": "",
                "CSVparser/nomatchpatterns": ""}
    calendar: dict[date, list[PaymentEntry]] = {}
    for number, (day, amount, receiver, name) in enumerate(calendar_rows):
        calendar.setdefault(date(2026, 10, day), []).append(
            PaymentEntry(Decimal(amount), f"{name} ({receiver})", receiver, number, number, name, key=f"c|{number}"))
    dbh = SimpleNamespace(get_setting=lambda key, default="": settings.get(key, default),
                          get_paymentsum_for_period=lambda start, end: calendar)
    return reconcile_statement_with_calendar(str(path), dbh, marks)


STATEMENT_ROWS = [(5, "750,00", "ИП Петров", "ЗА РЕМОНТ"), (6, "99,99", "ООО Гамма", "КАНЦТОВАРЫ"),
                  (6, "200,00", "ООО Омега", "УСЛУГИ")]
CALENDAR_ROWS = [(3, "750.00", "Сервис-Принт", "Оргтехника"), (7, "450.00", "ЧУП Дельта", "Уборка"),
                 (6, "200.00", "ООО Омега", "Услуги")]


def test_exact_amounts_on_same_date_are_counted_as_matched(tmp_path):
    result = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS)
    assert (result.statement_total, result.statement_matched) == (3, 1)
    assert (result.calendar_total, result.calendar_matched) == (3, 1)
    assert [e.amount for e in result.unmatched_statement] == [Decimal("750.00"), Decimal("99.99")]
    assert all(e.fee_date for e in result.unmatched_statement + result.unmatched_calendar)


def test_manual_link_between_different_dates_removes_both_entries(tmp_path):
    result = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS)
    statement_key = result.unmatched_statement[0].key
    calendar_key = result.unmatched_calendar[0].key
    marks = ReconciliationMarks(links=[(statement_key, calendar_key)])

    linked = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS, marks)
    assert [e.amount for e in linked.unmatched_statement] == [Decimal("99.99")]
    assert [e.amount for e in linked.unmatched_calendar] == [Decimal("450.00")]
    assert len(linked.links) == 1
    assert linked.links[0].difference == 0
    assert [e.fee_date for e in linked.links[0].statement + linked.links[0].calendar] == [date(2026, 10, 5),
                                                                                         date(2026, 10, 3)]
    assert summary_cells(linked, "Выписка")[2:4] == ["1", "0"]
    assert summary_cells(linked, "Календарь")[2:4] == ["1", "0"]


def summary_cells(result, title):
    row = re.search(rf"<b>{title}</b></td>(.*?)</tr>", result.format_summary()).group(1)
    return [re.sub(r"<[^>]+>", "", cell) for cell in re.findall(r"<td[^>]*>(.*?)</td>", row)]


def test_link_with_missing_entry_is_ignored(tmp_path):
    result = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS)
    marks = ReconciliationMarks(links=[(result.unmatched_statement[0].key, "c|9999")])
    linked = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS, marks)
    assert linked.links == [] and len(linked.unmatched_statement) == 2


def test_link_with_already_matched_entry_is_ignored(tmp_path):
    result = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS)
    marks = ReconciliationMarks(links=[(result.unmatched_statement[0].key, "c|2")])
    assert reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS, marks).links == []


def test_hidden_entries_leave_the_lists_but_stay_available(tmp_path):
    result = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS)
    hidden_key = result.unmatched_calendar[1].key
    hidden = reconcile_case(tmp_path, STATEMENT_ROWS, CALENDAR_ROWS, ReconciliationMarks(hidden={hidden_key}))
    assert [e.key for e in hidden.hidden_entries] == [hidden_key]
    assert hidden_key not in [e.key for e in hidden.unmatched_calendar]
    assert summary_cells(hidden, "Выписка")[2:4] == ["0", "0"]
    assert summary_cells(hidden, "Календарь")[2:4] == ["0", "1"]


def test_rejected_pair_returns_entries_to_the_lists(tmp_path):
    statement_rows = [(5, "1846,00", "САНИТАРНАЯ ОБОРОНА ЗАО", "ТТН 2156811 СРЕДСТВО ДЕЗИНФИЦИРУЮЩЕЕ")]
    calendar_rows = [(5, "1828.00", "ЗАО Санитарная оборона", "Средство дезинфицирующее")]
    paired = reconcile_case(tmp_path, statement_rows, calendar_rows)
    pair = paired.discrepancies[0].probable_pairs[0]
    assert pair.reasons

    rejected = reconcile_case(tmp_path, statement_rows, calendar_rows, ReconciliationMarks(rejected={pair.key}))
    assert rejected.discrepancies[0].probable_pairs == []
    assert len(rejected.unmatched_statement) == 1 and len(rejected.unmatched_calendar) == 1


def test_split_group_is_found_before_probable_pairs(tmp_path):
    result = reconcile_case(tmp_path, [(15, "1026,46", "ЮРСПЕКТР ООО", "ОПЛАТА ПО СЧЕТУ 57041"),
                                       (15, "2,00", "ЮРСПЕКТР ООО", "ДОПЛАТА ПО СЧЕТУ 57041")],
                            [(15, "1028.46", "ООО ЮрСпектр", "Информационные услуги Счет № 57041")])
    discrepancy = result.discrepancies[0]
    assert len(discrepancy.groups) == 1 and discrepancy.probable_pairs == []
    assert discrepancy.only_in_statement == [] and discrepancy.only_in_calendar == []


def test_rejected_group_returns_entries_to_the_lists():
    statement, calendar = contract_case()
    group = _regroup_contract_payments(date(2026, 10, 6), statement, calendar)[0][0]
    groups, rest_statement, rest_calendar = _regroup_contract_payments(
        date(2026, 10, 6), statement, calendar, rejected={group.key})
    assert groups == [] and rest_statement == statement and rest_calendar == calendar


def test_pair_key_depends_on_both_entries():
    first, second = entry("100.00", "ООО Ромашка"), entry("100.00", "ООО Ромашка")
    first.key, second.key = "s|1", "c|2"
    assert ProbablePair(first, second, 0.5).key == "p|s|1|c|2"
    assert first.from_statement and not second.from_statement


def test_pair_reasons_name_the_evidence():
    statement = entry("1000.00", "Ромашка-Торг", "ТТН 123456 ОТ 01.09.2026 бахилы")
    calendar = entry("970.00", "ООО Василёк", "бахилы ТТН № 123456 от 01.09.2026")
    assert "номер документа" in pair_reasons(statement, calendar)
    assert pair_reasons(entry("1000.00", "ООО Ромашка"), entry("990.00", "ООО Василёк")) == []


def test_transposed_digits_with_a_matching_word_make_a_pair():
    statement = entry("984.08", "РАСЧЕТЫ ПО ОПЕРАЦИЯМ С ЧЕКАМИ, БПК И ЭЛ.ДЕНЬГАМИ (ЗАЧИСЛЕНИЯ)",
                      "КОМАНДИРОВОЧНЫЕ РАСХОДЫ ЗА СЕНТЯБРЬ, 2026 СОГЛ. СПИСКУ N 162 ОТ 07.09.2026 Г.")
    calendar = entry("948.08", "Работники", "Командировочные расходы в С.Петербург Расчёт")
    assert pair_confidence(statement, calendar) >= 0.35
    assert "цифры суммы переставлены" in pair_reasons(statement, calendar)
    other_amount = entry("940.08", "Работники", "Командировочные расходы в С.Петербург Расчёт")
    assert pair_confidence(statement, other_amount) < 0.35


def test_transposed_digits_alone_are_not_enough():
    assert pair_confidence(entry("984.08", "ООО Ромашка"), entry("948.08", "ООО Василёк")) < 0.35


def test_equal_amounts_are_not_transposed_digits():
    assert "цифры суммы переставлены" not in pair_reasons(entry("984.08", "ООО Ромашка"), entry("984.08", "ООО Ромашка"))
