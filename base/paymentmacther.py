import csv
import re

from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from decimal import Decimal
from typing import Optional

import lovely_logger as log

from base.casting import str_int
from base.dbhandler import DBHandler
from base.feeparser import (CODE_COLUMNINDEX, DATE_COLUMNINDEX, DESCR_COLUMNINDEX, SUM_COLUMNINDEX,
                            RECEIVER_COLUMNINDEX, UNP_COLUMNINDEX, FEE_IN_TEXT_PATTERN, CSVParseError,
                            FeeKind, classify_fee, read_bank_unp, parse_date, parse_period)
from base.formatting import str_decimal, dec_html, dec_strcommaspace, COLOR_STATEMENT, COLOR_CALENDAR, COLOR_OK
from base.liability import LiabilityCategory
from base.payment import PaymentEntry


PAYROLL_KEYWORDS: tuple[str, ...] = (
    "окончательный расчет",
    "отпускные",
    "заработная плата",
    "отчисления в фсзн",
    "подоходный налог",
    "материальная помощь",
)
PAYROLL_DESCRIPTION: str = "Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"
CONTRACT_TAX_KEYWORDS: tuple[str, ...] = (
    "по договору подряда",
    "по договорам подряда",
)
CONTRACT_TAX_DESCRIPTION: str = "Налоги и взносы по договорам подряда"
CALENDAR_TAX_KEYWORDS: tuple[str, ...] = ("фсзн", "подоходный налог")
GROUP_MIN_NAME_SIMILARITY: float = 0.7

PAIR_MAX_DIFF_SHARE: Decimal = Decimal("0.10")
PAIR_MIN_CONFIDENCE: float = 0.35
AMOUNT_PENALTY: float = 0.7
NAME_NOISE_LEVEL: float = 0.4
WORD_MIN_RATIO: float = 0.75
TEXT_EVIDENCE_WEIGHT: float = 0.35
EVIDENCE_NUMBER: float = 0.85
EVIDENCE_NUMBER_AND_DATE: float = 0.95
EVIDENCE_DATE: float = 0.3
DOCUMENT_NUMBER_MIN_DIGITS: int = 3
DOCUMENT_NUMBER_PATTERN = re.compile(r"\d+(?:[/-]\d+)*")
DATE_IN_TEXT_PATTERN = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4}|\d{2})\b")
LEGAL_FORMS: frozenset[str] = frozenset(
    ("ооо", "зао", "оао", "ао", "чуп", "уп", "ип", "одо", "иооо", "тчуп", "чтуп", "пуп", "руп", "унп"))
COMMON_WORDS: frozenset[str] = frozenset(
    ("ттн", "акт", "счет", "счёт", "оплата", "платеж", "договор", "фактура", "накладная", "согласно", "ндс", "сумма"))


# ---------------------------------------------------------------------------
# 1. Извлечение эталонных сумм платежей из выписки
# ---------------------------------------------------------------------------

@dataclass
class StatementPayments:
    period: tuple[date, date]
    by_date: dict[date, list[PaymentEntry]] = field(default_factory=dict)

    def add(self, dt: date, amount: Decimal, descr: str, receiver: str = "", details: str = "",
            fee_category: LiabilityCategory | None = None) -> None:
        self.by_date.setdefault(dt, []).append(
            PaymentEntry(amount, descr, receiver.strip(), details=details, fee_category=fee_category))


def extract_statement_payments(filename: str, dbh) -> StatementPayments:

    columns_to_parse: list[int] = list(
        map(int, dbh.get_setting("CSVparser/columnstoparse").split(","))
    )
    # 1 и 9 - дефолты из gui/settingsdialog.py (DEF_ROW_PERIOD, DEF_ROW_TRANSACTIONSTART)
    row_period: int = str_int(dbh.get_setting("CSVparser/rowperiod"), 1) - 1
    row_transactions_start: int = str_int(dbh.get_setting("CSVparser/rowtransactionstart"), 9) - 1
    bank_unp: list[str] = read_bank_unp(dbh)
    keyword_templates: set[str] = {
        sub.strip().lower()
        for sub in dbh.get_setting("CSVparser/patterns").split(",")
        if sub.strip()
    }
    nomatch_templates: set[str] = {
        sub.strip().lower()
        for sub in dbh.get_setting("CSVparser/nomatchpatterns").split(",")
        if sub.strip()
    }

    period: Optional[tuple[date, date]] = None
    payments = StatementPayments(period=(None, None))

    income_fee_totals: dict[date, Decimal] = {}
    outgoing_fee_totals: dict[date, Decimal] = {}
    payroll_totals: dict[date, Decimal] = {}
    contract_tax_totals: dict[date, Decimal] = {}

    with open(filename, newline="", encoding="windows-1251") as f:
        reader = csv.reader(f, delimiter=";")

        for row_index, content in enumerate(reader):
            if row_index == row_period:
                try:
                    period = parse_period(content[columns_to_parse[DATE_COLUMNINDEX]])
                except IndexError:
                    raise CSVParseError("Не удалось найти строку с периодом выписки (ROW_PERIOD)")
                if period is None:
                    raise CSVParseError("В строке периода не обнаружено ожидаемого паттерна дат")
                continue

            if row_index < row_transactions_start:
                continue
            if not content:
                break

            try:
                transaction_code: str = content[columns_to_parse[CODE_COLUMNINDEX]]
                description: str = content[columns_to_parse[DESCR_COLUMNINDEX]]
                unp: str = content[columns_to_parse[UNP_COLUMNINDEX]]
                receiver: str = content[columns_to_parse[RECEIVER_COLUMNINDEX]]
                debit_raw: str = content[columns_to_parse[SUM_COLUMNINDEX]]
                raw_date: str = content[columns_to_parse[DATE_COLUMNINDEX]]
            except IndexError:
                break

            description_lower = description.lower()
            if any(kw in description_lower for kw in nomatch_templates):
                continue
            debit_stripped = debit_raw.strip()
            # Назначение платежа + контрагент в скобках — только для обычных строк
            description_with_receiver = f"{description} ({receiver})" if receiver.strip() else description

            # Есть сумма по Дебету
            if debit_stripped and debit_stripped != "0":
                debit_amount = str_decimal(debit_stripped)
                if debit_amount is None:
                    raise CSVParseError(
                        f"Строка {row_index}: не удалось преобразовать сумму дебета: {debit_raw!r}"
                    )
                if debit_amount > 0:
                    transaction_date = parse_date(raw_date, row_index)
                    fee_kind = classify_fee(transaction_code, unp, description, bank_unp, keyword_templates)
                    is_payroll = any(kw in description_lower for kw in PAYROLL_KEYWORDS)
                    is_contract_tax = is_payroll and any(kw in description_lower for kw in CONTRACT_TAX_KEYWORDS)
                    if fee_kind == FeeKind.OUTGOING:
                        outgoing_fee_totals[transaction_date] = (
                                outgoing_fee_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    elif fee_kind == FeeKind.INCOME:
                        income_fee_totals[transaction_date] = (
                                income_fee_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    elif is_contract_tax:
                        contract_tax_totals[transaction_date] = (
                                contract_tax_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    elif is_payroll:
                        payroll_totals[transaction_date] = (
                                payroll_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    else:
                        payments.add(transaction_date, debit_amount, description_with_receiver, receiver, description)
                    continue

            # Дебета нет
            if classify_fee(transaction_code, unp, description, bank_unp, keyword_templates) == FeeKind.EMBEDDED:
                matches = FEE_IN_TEXT_PATTERN.findall(description)
                if len(matches) > 1:
                    raise CSVParseError(
                        f"Строка {row_index}: найдено более одного совпадения суммы комиссии: {description}"
                    )
                if len(matches) == 1:
                    fee = str_decimal(matches[0])
                    if fee is None:
                        raise CSVParseError(f"Не удалось преобразовать в число: {matches[0]!r}")
                    transaction_date = parse_date(raw_date, row_index)
                    income_fee_totals[transaction_date] = (
                            income_fee_totals.get(transaction_date, Decimal("0")) + fee
                    )

    if period is None:
        raise CSVParseError("В файле не найдена строка с периодом выписки")

    for transaction_date, total in income_fee_totals.items():
        payments.add(transaction_date, total, "Комиссии в поступлениях", fee_category=LiabilityCategory.BANKING)
    for transaction_date, total in outgoing_fee_totals.items():
        payments.add(transaction_date, total, "Комиссии к уплате", fee_category=LiabilityCategory.COMMISSION)
    for transaction_date, total in payroll_totals.items():
        payments.add(transaction_date, total, PAYROLL_DESCRIPTION)
    for transaction_date, total in contract_tax_totals.items():
        payments.add(transaction_date, total, CONTRACT_TAX_DESCRIPTION)

    payments.period = period
    return payments


# ---------------------------------------------------------------------------
# 2. Сравнение (только по суммам, мультимножество) и отчёт
# ---------------------------------------------------------------------------

def _payments_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return "платёж"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return "платежа"
    return "платежей"


def _summary_row(title: str, count: int, total: Decimal, color: str) -> str:
    return (f"<tr><td style='color:{color};'>{title}</td>"
            f"<td align='right'>{count} {_payments_word(count)}</td>"
            f"<td align='right'><b>{dec_html(total)}</b></td></tr>")


def _diff_amounts(statement_entries: list[PaymentEntry], calendar_entries: list[PaymentEntry]) \
        -> tuple[list[PaymentEntry], list[PaymentEntry]]:

    remaining_calendar = list(calendar_entries)
    unmatched_statement: list[PaymentEntry] = []
    for entry in statement_entries:
        match_index = next(
            (i for i, cal_entry in enumerate(remaining_calendar) if cal_entry.amount == entry.amount), None
        )
        if match_index is None:
            unmatched_statement.append(entry)
        else:
            remaining_calendar.pop(match_index)
    return unmatched_statement, remaining_calendar


def _name_words(text: str) -> list[str]:
    return [word for word in re.findall(r"[^\W\d_]+", text.lower()) if len(word) > 1 and word not in LEGAL_FORMS]


def _text_words(text: str) -> list[str]:
    return [word for word in _name_words(text) if len(word) > 2 and word not in COMMON_WORDS]


def _word_closeness(words_a: list[str], words_b: list[str]) -> float:
    if not words_a or not words_b:
        return 0.0
    shorter, longer = sorted((words_a, words_b), key=len)
    total = 0.0
    for word in shorter:
        best = max(SequenceMatcher(None, word, other).ratio() for other in longer)
        total += best if best >= WORD_MIN_RATIO else 0.0
    return total / len(shorter)


def _name_similarity(name_a: str, name_b: str) -> float:
    words_a, words_b = _name_words(name_a), _name_words(name_b)
    if not words_a or not words_b:
        return 0.0
    whole = SequenceMatcher(None, " ".join(sorted(words_a)), " ".join(sorted(words_b))).ratio()
    return max(whole, _word_closeness(words_a, words_b))


def _document_marks(text: str) -> tuple[set[str], set[tuple[int, int, int]]]:
    dates: set[tuple[int, int, int]] = set()
    for day, month, year in DATE_IN_TEXT_PATTERN.findall(text):
        dates.add((int(day), int(month), int(year) + 2000 if len(year) == 2 else int(year)))
    numbers = {number for number in DOCUMENT_NUMBER_PATTERN.findall(DATE_IN_TEXT_PATTERN.sub(" ", text))
               if len(re.sub(r"\D", "", number)) >= DOCUMENT_NUMBER_MIN_DIGITS}
    return numbers, dates


def _document_evidence(text_a: str, text_b: str) -> float:
    numbers_a, dates_a = _document_marks(text_a)
    numbers_b, dates_b = _document_marks(text_b)
    if numbers_a & numbers_b:
        return EVIDENCE_NUMBER_AND_DATE if dates_a & dates_b else EVIDENCE_NUMBER
    return EVIDENCE_DATE if dates_a & dates_b else 0.0


def pair_confidence(statement_entry: PaymentEntry, calendar_entry: PaymentEntry) -> float:
    biggest = max(statement_entry.amount, calendar_entry.amount)
    if biggest <= 0:
        return 0.0
    diff_share = abs(statement_entry.amount - calendar_entry.amount) / biggest
    if diff_share > PAIR_MAX_DIFF_SHARE:
        return 0.0

    name_closeness = max(0.0, (_name_similarity(statement_entry.receiver, calendar_entry.receiver)
                               - NAME_NOISE_LEVEL) / (1 - NAME_NOISE_LEVEL))
    text_closeness = _word_closeness(_text_words(statement_entry.details), _text_words(calendar_entry.details))
    evidences = (name_closeness,
                 _document_evidence(statement_entry.details, calendar_entry.details),
                 TEXT_EVIDENCE_WEIGHT * text_closeness)
    identity = 1.0
    for evidence in evidences:
        identity *= 1 - evidence
    identity = 1 - identity

    amount_factor = 1 - AMOUNT_PENALTY * float(diff_share / PAIR_MAX_DIFF_SHARE)
    return identity * amount_factor


def _pair_probable_matches(only_statement: list[PaymentEntry], only_calendar: list[PaymentEntry]) \
        -> tuple[list[ProbablePair], list[PaymentEntry], list[PaymentEntry]]:

    candidates: list[tuple] = []
    for statement_index, statement_entry in enumerate(only_statement):
        for calendar_index, calendar_entry in enumerate(only_calendar):
            confidence = pair_confidence(statement_entry, calendar_entry)
            if confidence >= PAIR_MIN_CONFIDENCE:
                candidates.append((confidence, statement_index, calendar_index))

    candidates.sort(reverse=True)
    used_statement: set[int] = set()
    used_calendar: set[int] = set()
    pairs: list[ProbablePair] = []
    for confidence, statement_index, calendar_index in candidates:
        if statement_index in used_statement or calendar_index in used_calendar:
            continue
        used_statement.add(statement_index)
        used_calendar.add(calendar_index)
        pairs.append(ProbablePair(only_statement[statement_index], only_calendar[calendar_index], confidence))

    rest_statement = [e for i, e in enumerate(only_statement) if i not in used_statement]
    rest_calendar = [e for i, e in enumerate(only_calendar) if i not in used_calendar]
    return pairs, rest_statement, rest_calendar


def _regroup_contract_payments(fee_date: date, only_statement: list[PaymentEntry],
                               only_calendar: list[PaymentEntry]
                               ) -> tuple[list[RegroupedPayments], list[PaymentEntry], list[PaymentEntry]]:

    statement_taxes = [e for e in only_statement if e.descr == CONTRACT_TAX_DESCRIPTION]
    calendar_taxes = [e for e in only_calendar if any(kw in e.descr.lower() for kw in CALENDAR_TAX_KEYWORDS)]
    if not statement_taxes:
        return [], only_statement, only_calendar

    nets = [e for e in only_statement if e.receiver and not e.fee_category and e not in statement_taxes]
    grosses = [e for e in only_calendar if e.receiver and e not in calendar_taxes]
    candidates = sorted(((_name_similarity(net.receiver, gross.receiver), net_index, gross_index)
                         for net_index, net in enumerate(nets) for gross_index, gross in enumerate(grosses)
                         if net.amount < gross.amount), reverse=True)
    used_nets: set[int] = set()
    used_grosses: set[int] = set()
    contracts: list[tuple[PaymentEntry, PaymentEntry]] = []
    for similarity, net_index, gross_index in candidates:
        if similarity < GROUP_MIN_NAME_SIMILARITY or net_index in used_nets or gross_index in used_grosses:
            continue
        used_nets.add(net_index)
        used_grosses.add(gross_index)
        contracts.append((nets[net_index], grosses[gross_index]))
    if not contracts:
        return [], only_statement, only_calendar

    group_statement = [net for net, _ in contracts] + statement_taxes
    group_calendar = [gross for _, gross in contracts] + calendar_taxes
    if sum(e.amount for e in group_statement) != sum(e.amount for e in group_calendar):
        return [], only_statement, only_calendar

    rest_statement = [e for e in only_statement if all(e is not g for g in group_statement)]
    rest_calendar = [e for e in only_calendar if all(e is not g for g in group_calendar)]
    return [RegroupedPayments(fee_date, group_statement, group_calendar, contracts)], rest_statement, rest_calendar


@dataclass
class ProbablePair:
    statement: PaymentEntry
    calendar: PaymentEntry
    confidence: float

    @property
    def difference(self) -> Decimal:
        return self.statement.amount - self.calendar.amount


def _percent(share: Decimal) -> str:
    return f"{share * 100:.1f}".removesuffix(".0").replace(".", ",") + "%"


@dataclass
class RegroupedPayments:
    fee_date: date
    statement: list[PaymentEntry]
    calendar: list[PaymentEntry]
    contracts: list[tuple[PaymentEntry, PaymentEntry]]

    @property
    def key(self) -> tuple:
        return (self.fee_date,
                tuple(sorted(e.amount for e in self.statement)),
                tuple(sorted(e.amount for e in self.calendar)))

    @property
    def explanation(self) -> str:
        contracts_total = sum((calendar_entry.amount for _, calendar_entry in self.contracts), Decimal("0"))
        statement_taxes = [e for e in self.statement if all(e is not n for n, _ in self.contracts)]
        calendar_taxes = [e for e in self.calendar if all(e is not c for _, c in self.contracts)]

        lines: list[str] = []
        for statement_entry, calendar_entry in self.contracts:
            withheld = calendar_entry.amount - statement_entry.amount
            lines.append(f"{calendar_entry.receiver}: по договору {dec_strcommaspace(calendar_entry.amount)}, "
                         f"выплачено {dec_strcommaspace(statement_entry.amount)}, "
                         f"удержано {dec_strcommaspace(withheld)} "
                         f"({_percent(withheld / calendar_entry.amount)} - ПН/СТР)")
        contracts_word = "договора" if len(self.contracts) == 1 else "договоров"
        for entry in calendar_taxes:
            lines.append(f"{entry.descr.split(' (')[0]} в календаре: {dec_strcommaspace(entry.amount)} "
                         f"({_percent(entry.amount / contracts_total)} от суммы {contracts_word})")

        statement_parts = [f"{dec_strcommaspace(n.amount)} (выплачено)" for n, _ in self.contracts]
        statement_parts += [f"{dec_strcommaspace(e.amount)} (ФСЗН + ПН/СТР)" for e in statement_taxes]
        calendar_parts = [f"{dec_strcommaspace(c.amount)} (выплачено + ПН/СТР)" for _, c in self.contracts]
        calendar_parts += [f"{dec_strcommaspace(e.amount)} ({e.descr.split(' (')[0]})" for e in calendar_taxes]
        lines.append(f"Выписка: {' + '.join(statement_parts)} = "
                     f"{dec_strcommaspace(sum((e.amount for e in self.statement), Decimal('0')))}")
        lines.append(f"Календарь: {' + '.join(calendar_parts)} = "
                     f"{dec_strcommaspace(sum((e.amount for e in self.calendar), Decimal('0')))}")
        return "\n".join(lines)


@dataclass
class DateDiscrepancy:
    fee_date: date
    only_in_statement: list[PaymentEntry]
    only_in_calendar: list[PaymentEntry]
    probable_pairs: list[ProbablePair] = field(default_factory=list)
    groups: list[RegroupedPayments] = field(default_factory=list)


@dataclass
class ReconciliationResult:
    period: tuple[date, date]
    discrepancies: list[DateDiscrepancy]
    fee_totals: dict[tuple[date, LiabilityCategory], Decimal] = field(default_factory=dict)
    confirmed_groups_count: int = 0

    @property
    def only_in_statement_count(self) -> int:
        return sum(len(d.only_in_statement) + len(d.probable_pairs) + sum(len(g.statement) for g in d.groups)
                   for d in self.discrepancies)

    @property
    def only_in_statement_sum(self) -> Decimal:
        return sum(
            (sum((e.amount for e in d.only_in_statement), Decimal("0")) +
             sum((p.statement.amount for p in d.probable_pairs), Decimal("0")) +
             sum((e.amount for g in d.groups for e in g.statement), Decimal("0")) for d in self.discrepancies),
            Decimal("0"),
        )

    @property
    def only_in_calendar_count(self) -> int:
        return sum(len(d.only_in_calendar) + len(d.probable_pairs) + sum(len(g.calendar) for g in d.groups)
                   for d in self.discrepancies)

    @property
    def only_in_calendar_sum(self) -> Decimal:
        return sum(
            (sum((e.amount for e in d.only_in_calendar), Decimal("0")) +
             sum((p.calendar.amount for p in d.probable_pairs), Decimal("0")) +
             sum((e.amount for g in d.groups for e in g.calendar), Decimal("0")) for d in self.discrepancies),
            Decimal("0"),
        )

    @property
    def has_discrepancies(self) -> bool:
        return bool(self.discrepancies)

    def format_summary(self) -> str:
        period_from = self.period[0].strftime("%d.%m.%Y")
        period_to = self.period[1].strftime("%d.%m.%Y")
        header = f"<h3>Сверка выписки за период {period_from} – {period_to}</h3>"
        confirmed = (f"<p>Подтверждено вручную групп платежей: {self.confirmed_groups_count}</p>"
                     if self.confirmed_groups_count else "")

        if not self.discrepancies:
            return (f"{header}<p style='color:{COLOR_OK};'>"
                    f"Расхождений не найдено: все платежи из выписки учтены в календаре.</p>{confirmed}")

        return "\n".join([
            header,
            "<table cellspacing='0' cellpadding='3'>",
            _summary_row("Только в выписке:", self.only_in_statement_count,
                         self.only_in_statement_sum, COLOR_STATEMENT),
            _summary_row("Только в календаре:", self.only_in_calendar_count,
                         self.only_in_calendar_sum, COLOR_CALENDAR),
            "</table>",
            confirmed,
        ])


def reconcile_statement_with_calendar(csv_filename: str, dbh: DBHandler,
                                       confirmed_groups: frozenset = frozenset()) -> ReconciliationResult | None:
    statement = extract_statement_payments(csv_filename, dbh)
    calendar_by_date = dbh.get_paymentsum_for_period(statement.period[0], statement.period[1])
    if calendar_by_date is None:
        return None

    all_dates = sorted(set(statement.by_date) | set(calendar_by_date))
    discrepancies: list[DateDiscrepancy] = []
    confirmed_groups_count: int = 0

    for fee_date in all_dates:
        only_statement, only_calendar = _diff_amounts(
            statement.by_date.get(fee_date, []), calendar_by_date.get(fee_date, [])
        )
        if only_statement or only_calendar:
            pairs, only_statement, only_calendar = _pair_probable_matches(only_statement, only_calendar)
            groups, only_statement, only_calendar = _regroup_contract_payments(fee_date, only_statement, only_calendar)
            confirmed_groups_count += sum(1 for g in groups if g.key in confirmed_groups)
            groups = [g for g in groups if g.key not in confirmed_groups]
            if only_statement or only_calendar or pairs or groups:
                discrepancies.append(DateDiscrepancy(fee_date, only_statement, only_calendar, pairs, groups))

    fee_totals = {(fee_date, entry.fee_category): entry.amount
                  for fee_date, entries in statement.by_date.items() for entry in entries if entry.fee_category}
    return ReconciliationResult(statement.period, discrepancies, fee_totals, confirmed_groups_count)