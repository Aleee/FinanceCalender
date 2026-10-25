from __future__ import annotations

import csv
import re

from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from decimal import Decimal
from itertools import combinations
from typing import Optional


from base.casting import str_int
from base.dbhandler import DBHandler
from base.feeparser import (CODE_COLUMNINDEX, DATE_COLUMNINDEX, DESCR_COLUMNINDEX, SUM_COLUMNINDEX,
                            RECEIVER_COLUMNINDEX, UNP_COLUMNINDEX, FEE_IN_TEXT_PATTERN, CSVParseError,
                            FeeKind, classify_fee, ensure_no_operations_left, open_statement, read_bank_unp,
                            read_columns_to_parse, parse_date, parse_period)
from base.formatting import (str_decimal, dec_html, dec_strcommaspace, COLOR_STATEMENT, COLOR_CALENDAR, COLOR_OK,
                             COLOR_WARNING)
from base.liability import LiabilityCategory
from base.payment import PaymentEntry


DEF_PAYROLL_PATTERNS: str = (
    "окончательный расчет, отпускные, заработн, зарплат, з/пл, отчисления в фсзн, отчисления в бгс, "
    "отчисления на ппс, подоходный налог, материальная помощь, пособие по уходу, коллективного договора"
)
PAYROLL_DESCRIPTION: str = "Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"
CONTRACT_TAX_KEYWORDS: tuple[str, ...] = (
    "по договору подряда",
    "по договорам подряда",
    "налог по ип ",
    "по займу",
)
CONTRACT_TAX_DESCRIPTION: str = "Налоги и взносы по договорам подряда"
CALENDAR_TAX_KEYWORDS: tuple[str, ...] = ("фсзн", "подоходный налог")
GROUP_MIN_NAME_SIMILARITY: float = 0.7
SPLIT_MAX_PARTS: int = 4
SPLIT_MAX_RELATED: int = 20

PAIR_MAX_DIFF_SHARE: Decimal = Decimal("0.15")
PAIR_MAX_DIFF_SHARE_WITH_DOCUMENT: Decimal = Decimal("0.30")
PAIR_MIN_CONFIDENCE: float = 0.35
AMOUNT_PENALTY: float = 0.5
EXTENDED_AMOUNT_PENALTY: float = 0.4
NAME_NOISE_LEVEL: float = 0.4
WORD_MIN_RATIO: float = 0.75
TEXT_EVIDENCE_WEIGHT: float = 0.7
TEXT_EVIDENCE_DECAY: float = 0.6
EVIDENCE_NUMBER: float = 0.85
EVIDENCE_NUMBER_AND_DATE: float = 0.95
EVIDENCE_DATE: float = 0.3
EVIDENCE_DIGITS: float = 0.3
REASON_MIN_EVIDENCE: float = 0.25
DOCUMENT_NUMBER_MIN_DIGITS: int = 3
DOCUMENT_NUMBER_PATTERN = re.compile(r"\d+(?:[/-]\d+)*")
YEAR_PATTERN = re.compile(r"(?:19|20)\d\d")
DATE_IN_TEXT_PATTERN = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4}|\d{2})\b")
LEGAL_FORMS: frozenset[str] = frozenset(
    ("ооо", "зао", "оао", "ао", "чуп", "уп", "ип", "одо", "иооо", "тчуп", "чтуп", "пуп", "руп", "унп"))
COMMON_WORDS: frozenset[str] = frozenset(
    ("ттн", "акт", "счет", "счёт", "оплата", "платеж", "договор", "фактура", "накладная", "согласно", "ндс", "сумма",
     "для", "при", "под", "про", "без", "над", "из", "по", "за", "на", "от", "до",
     "январь", "января", "февраль", "февраля", "март", "марта", "апрель", "апреля", "май", "мая", "июнь", "июня",
     "июль", "июля", "август", "августа", "сентябрь", "сентября", "октябрь", "октября", "ноябрь", "ноября",
     "декабрь", "декабря", "год", "года", "г"))
COMMON_WORD_PREFIXES: tuple[str, ...] = (
    "договор", "дог", "услуг", "оказан", "выполнен", "работ", "согл", "солгас", "сдач", "приемк", "приёмк",
    "оплат", "платеж", "перевод", "погашен", "основн", "долг", "кредит", "процент", "вознагражд", "комисси",
    "расход", "период", "назначен", "документ", "накладн", "фактур")


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

    columns_to_parse: list[int] = read_columns_to_parse(dbh)
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
    payroll_templates: set[str] = {
        sub.strip().lower()
        for sub in dbh.get_setting("CSVparser/payrollpatterns", DEF_PAYROLL_PATTERNS).split(",")
        if sub.strip()
    }

    period: Optional[tuple[date, date]] = None
    payments = StatementPayments(period=(None, None))

    income_fee_totals: dict[date, Decimal] = {}
    outgoing_fee_totals: dict[date, Decimal] = {}
    payroll_totals: dict[date, Decimal] = {}
    contract_tax_totals: dict[date, Decimal] = {}

    with open_statement(filename) as f:
        reader = csv.reader(f, delimiter=";")

        for row_index, content in enumerate(reader):
            if row_index == row_period:
                try:
                    period = parse_period(content[columns_to_parse[DATE_COLUMNINDEX]])
                except IndexError:
                    raise CSVParseError("Не удалось найти строку с периодом выписки (ROW_PERIOD)")
                if period is None:
                    raise CSVParseError("В строке периода выписки не найдены даты")
                continue

            if row_index < row_transactions_start:
                continue
            if not content:
                ensure_no_operations_left(reader, columns_to_parse[DATE_COLUMNINDEX], row_index)
                break

            try:
                transaction_code: str = content[columns_to_parse[CODE_COLUMNINDEX]]
                description: str = content[columns_to_parse[DESCR_COLUMNINDEX]]
                unp: str = content[columns_to_parse[UNP_COLUMNINDEX]]
                receiver: str = content[columns_to_parse[RECEIVER_COLUMNINDEX]]
                debit_raw: str = content[columns_to_parse[SUM_COLUMNINDEX]]
                raw_date: str = content[columns_to_parse[DATE_COLUMNINDEX]]
            except IndexError:
                ensure_no_operations_left(reader, columns_to_parse[DATE_COLUMNINDEX], row_index)
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
                    is_payroll = any(kw in description_lower for kw in payroll_templates)
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
        payments.add(transaction_date, total, "Комиссии, относимые на банковские расходы", fee_category=LiabilityCategory.BANKING)
    for transaction_date, total in outgoing_fee_totals.items():
        payments.add(transaction_date, total, "Комиссии, относимые на комиссионные расходы", fee_category=LiabilityCategory.COMMISSION)
    for transaction_date, total in payroll_totals.items():
        payments.add(transaction_date, total, PAYROLL_DESCRIPTION)
    for transaction_date, total in contract_tax_totals.items():
        payments.add(transaction_date, total, CONTRACT_TAX_DESCRIPTION)

    payments.period = period
    return payments


# ---------------------------------------------------------------------------
# 2. Сравнение (только по суммам, мультимножество) и отчёт
# ---------------------------------------------------------------------------

SUMMARY_PADDING = "padding-left:18px;"


def _summary_row(title: str, counts: tuple[int, int, int, int, int], total: Decimal, color: str) -> str:
    total_count, matched_count, linked_count, hidden_count, unmatched_count = counts
    cells = (str(total_count), str(matched_count), _summary_link("linked", linked_count),
             _summary_link("hidden", hidden_count), f"<b>{unmatched_count}</b>")
    return (f"<tr><td style='color:{color};'><b>{title}</b></td>"
            + "".join(f"<td align='right' style='{SUMMARY_PADDING}'>{cell}</td>" for cell in cells)
            + f"<td align='right' style='{SUMMARY_PADDING}color:{color};'><b>{dec_html(total)}</b></td></tr>")


def _summary_link(target: str, count: int) -> str:
    return f"<a href='{target}'>{count}</a>" if count else str(count)


def _diff_amounts(statement_entries: list[PaymentEntry], calendar_entries: list[PaymentEntry]) \
        -> tuple[list[PaymentEntry], list[PaymentEntry]]:

    remaining_calendar = list(calendar_entries)
    unmatched_statement: list[PaymentEntry] = []
    for entry in statement_entries:
        same_amount = [i for i, cal_entry in enumerate(remaining_calendar) if cal_entry.amount == entry.amount]
        if not same_amount:
            unmatched_statement.append(entry)
        else:
            match_index = max(same_amount,
                              key=lambda i: _name_similarity(entry.receiver, remaining_calendar[i].receiver))
            remaining_calendar.pop(match_index)
    return unmatched_statement, remaining_calendar


def _name_words(text: str) -> list[str]:
    return [word for word in re.findall(r"[^\W\d_]+", text.lower()) if len(word) > 1 and word not in LEGAL_FORMS]


def _text_words(text: str) -> list[str]:
    return [word for word in _name_words(text)
            if len(word) > 2 and word not in COMMON_WORDS and not word.startswith(COMMON_WORD_PREFIXES)]


def _word_closeness(words_a: list[str], words_b: list[str]) -> float:
    if not words_a or not words_b:
        return 0.0
    shorter, longer = sorted((words_a, words_b), key=len)
    total = 0.0
    for word in shorter:
        best = max(SequenceMatcher(None, word, other).ratio() for other in longer)
        total += best if best >= WORD_MIN_RATIO else 0.0
    return total / len(shorter)


def _text_evidence(words_a: list[str], words_b: list[str]) -> float:
    matched = _word_closeness(words_a, words_b) * min(len(words_a), len(words_b))
    return TEXT_EVIDENCE_WEIGHT * (1 - TEXT_EVIDENCE_DECAY ** matched)


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
    numbers = {number.replace("-", "/") for number in DOCUMENT_NUMBER_PATTERN.findall(DATE_IN_TEXT_PATTERN.sub(" ", text))
               if len(re.sub(r"\D", "", number)) >= DOCUMENT_NUMBER_MIN_DIGITS and not YEAR_PATTERN.fullmatch(number)}
    return numbers, dates


def _document_evidence(text_a: str, text_b: str) -> float:
    numbers_a, dates_a = _document_marks(text_a)
    numbers_b, dates_b = _document_marks(text_b)
    if numbers_a & numbers_b:
        return EVIDENCE_NUMBER_AND_DATE if dates_a & dates_b else EVIDENCE_NUMBER
    return EVIDENCE_DATE if dates_a & dates_b else 0.0


def _same_digits(amount_a: Decimal, amount_b: Decimal) -> bool:
    return amount_a != amount_b and sorted(f"{amount_a:.2f}".replace(".", "")) == sorted(f"{amount_b:.2f}".replace(".", ""))


def pair_confidence(statement_entry: PaymentEntry, calendar_entry: PaymentEntry) -> float:
    biggest = max(statement_entry.amount, calendar_entry.amount)
    if biggest <= 0:
        return 0.0
    diff_share = abs(statement_entry.amount - calendar_entry.amount) / biggest
    if diff_share > PAIR_MAX_DIFF_SHARE_WITH_DOCUMENT:
        return 0.0
    document_evidence = _document_evidence(statement_entry.details, calendar_entry.details)
    if diff_share > PAIR_MAX_DIFF_SHARE and document_evidence < EVIDENCE_NUMBER:
        return 0.0

    name_closeness = max(0.0, (_name_similarity(statement_entry.receiver, calendar_entry.receiver)
                               - NAME_NOISE_LEVEL) / (1 - NAME_NOISE_LEVEL))
    text_evidence = _text_evidence(_text_words(statement_entry.details), _text_words(calendar_entry.details))
    digits_evidence = EVIDENCE_DIGITS if _same_digits(statement_entry.amount, calendar_entry.amount) else 0.0
    evidences = (name_closeness,
                 document_evidence,
                 text_evidence,
                 digits_evidence)
    identity = 1.0
    for evidence in evidences:
        identity *= 1 - evidence
    identity = 1 - identity

    normal_part = min(diff_share, PAIR_MAX_DIFF_SHARE)
    extended_part = diff_share - normal_part
    extended_range = PAIR_MAX_DIFF_SHARE_WITH_DOCUMENT - PAIR_MAX_DIFF_SHARE
    amount_factor = (1 - AMOUNT_PENALTY * float(normal_part / PAIR_MAX_DIFF_SHARE)
                     - EXTENDED_AMOUNT_PENALTY * float(extended_part / extended_range))
    return identity * amount_factor


def pair_reasons(statement_entry: PaymentEntry, calendar_entry: PaymentEntry) -> list[str]:
    reasons: list[str] = []
    name_closeness = (_name_similarity(statement_entry.receiver, calendar_entry.receiver)
                      - NAME_NOISE_LEVEL) / (1 - NAME_NOISE_LEVEL)
    if name_closeness >= REASON_MIN_EVIDENCE:
        reasons.append("контрагент")
    document_evidence = _document_evidence(statement_entry.details, calendar_entry.details)
    if document_evidence >= EVIDENCE_NUMBER:
        reasons.append("номер документа")
    elif document_evidence >= REASON_MIN_EVIDENCE:
        reasons.append("дата документа")
    if _text_evidence(_text_words(statement_entry.details),
                      _text_words(calendar_entry.details)) >= REASON_MIN_EVIDENCE:
        reasons.append("слова в назначении")
    if _same_digits(statement_entry.amount, calendar_entry.amount):
        reasons.append("цифры суммы переставлены")
    return reasons


def _pair_probable_matches(only_statement: list[PaymentEntry], only_calendar: list[PaymentEntry],
                           rejected: frozenset | set = frozenset()) \
        -> tuple[list[ProbablePair], list[PaymentEntry], list[PaymentEntry]]:

    candidates: list[tuple] = []
    for statement_index, statement_entry in enumerate(only_statement):
        for calendar_index, calendar_entry in enumerate(only_calendar):
            if pair_key(statement_entry, calendar_entry) in rejected:
                continue
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
                               only_calendar: list[PaymentEntry], rejected: frozenset | set = frozenset()
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

    group = RegroupedPayments(fee_date, group_statement, group_calendar, contracts)
    if group.key in rejected:
        return [], only_statement, only_calendar
    rest_statement = [e for e in only_statement if all(e is not g for g in group_statement)]
    rest_calendar = [e for e in only_calendar if all(e is not g for g in group_calendar)]
    return [group], rest_statement, rest_calendar


def _same_counterparty(first: PaymentEntry, second: PaymentEntry) -> bool:
    if first.fee_category or second.fee_category:
        return False
    return (_name_similarity(first.receiver, second.receiver) >= GROUP_MIN_NAME_SIMILARITY
            or _document_evidence(first.details, second.details) >= EVIDENCE_NUMBER)


def _find_parts(whole: PaymentEntry, candidates: list[PaymentEntry]) -> list[PaymentEntry] | None:
    related = [e for e in candidates if e.amount < whole.amount and _same_counterparty(whole, e)]
    if len(related) > SPLIT_MAX_RELATED:
        return None
    for size in range(2, min(SPLIT_MAX_PARTS, len(related)) + 1):
        for parts in combinations(related, size):
            if sum(e.amount for e in parts) == whole.amount:
                return list(parts)
    return None


def _merge_split_payments(fee_date: date, only_statement: list[PaymentEntry], only_calendar: list[PaymentEntry],
                          rejected: frozenset | set = frozenset()
                          ) -> tuple[list[RegroupedPayments], list[PaymentEntry], list[PaymentEntry]]:

    groups: list[RegroupedPayments] = []
    used: set[int] = set()

    def free(entries: list[PaymentEntry]) -> list[PaymentEntry]:
        return [e for e in entries if id(e) not in used]

    for calendar_entry in only_calendar:
        parts = _find_parts(calendar_entry, free(only_statement))
        group = parts and RegroupedPayments(fee_date, parts, [calendar_entry], [])
        if group and group.key not in rejected:
            groups.append(group)
            used.update(id(e) for e in parts + [calendar_entry])
    for statement_entry in only_statement:
        if id(statement_entry) in used:
            continue
        parts = _find_parts(statement_entry, free(only_calendar))
        group = parts and RegroupedPayments(fee_date, [statement_entry], parts, [])
        if group and group.key not in rejected:
            groups.append(group)
            used.update(id(e) for e in parts + [statement_entry])
    return groups, free(only_statement), free(only_calendar)


def pair_key(statement_entry: PaymentEntry, calendar_entry: PaymentEntry) -> str:
    return f"p|{statement_entry.key}|{calendar_entry.key}"


@dataclass
class ProbablePair:
    statement: PaymentEntry
    calendar: PaymentEntry
    confidence: float

    @property
    def difference(self) -> Decimal:
        return self.statement.amount - self.calendar.amount

    @property
    def key(self) -> str:
        return pair_key(self.statement, self.calendar)

    @property
    def reasons(self) -> list[str]:
        return pair_reasons(self.statement, self.calendar)


@dataclass
class ManualLink:
    keys: tuple[str, ...]
    statement: list[PaymentEntry]
    calendar: list[PaymentEntry]

    @property
    def difference(self) -> Decimal:
        return (sum((e.amount for e in self.statement), Decimal("0"))
                - sum((e.amount for e in self.calendar), Decimal("0")))


@dataclass
class ReconciliationMarks:
    hidden: set[str] = field(default_factory=set)
    links: list[tuple[str, ...]] = field(default_factory=list)
    rejected: set[str] = field(default_factory=set)


def _percent(share: Decimal) -> str:
    return f"{share * 100:.1f}".removesuffix(".0").replace(".", ",") + "%"


@dataclass
class RegroupedPayments:
    fee_date: date
    statement: list[PaymentEntry]
    calendar: list[PaymentEntry]
    contracts: list[tuple[PaymentEntry, PaymentEntry]]

    @property
    def key(self) -> str:
        return (f"g|{self.fee_date.isoformat()}|{','.join(str(a) for a in sorted(e.amount for e in self.statement))}"
                f"|{','.join(str(a) for a in sorted(e.amount for e in self.calendar))}")

    @property
    def explanation(self) -> str:
        if not self.contracts:
            return self._split_explanation()
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

    def _split_explanation(self) -> str:
        def side(entries: list[PaymentEntry]) -> str:
            return " + ".join(dec_strcommaspace(e.amount) for e in entries)

        total = dec_strcommaspace(sum((e.amount for e in self.statement), Decimal("0")))
        if len(self.calendar) == 1:
            title = f"{self.calendar[0].receiver}: один платеж в календаре оплачен несколькими платежами в выписке"
        else:
            title = f"{self.statement[0].receiver}: один платеж в выписке соответствует нескольким платежам в календаре"
        return "\n".join([title, f"Выписка: {side(self.statement)} = {total}",
                          f"Календарь: {side(self.calendar)} = {total}"])


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
    hidden_entries: list[PaymentEntry] = field(default_factory=list)
    links: list[ManualLink] = field(default_factory=list)
    statement_total: int = 0
    calendar_total: int = 0
    statement_matched: int = 0
    calendar_matched: int = 0

    @property
    def unmatched_statement(self) -> list[PaymentEntry]:
        return sorted((e for d in self.discrepancies for e in d.only_in_statement),
                      key=lambda e: (e.fee_date, e.amount))

    @property
    def unmatched_calendar(self) -> list[PaymentEntry]:
        return sorted((e for d in self.discrepancies for e in d.only_in_calendar),
                      key=lambda e: (e.fee_date, e.amount))

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
    def proposal_entries_count(self) -> int:
        return sum(2 * len(d.probable_pairs) + sum(len(g.statement) + len(g.calendar) for g in d.groups)
                   for d in self.discrepancies)

    @property
    def has_discrepancies(self) -> bool:
        return bool(self.discrepancies)

    def format_summary(self) -> str:
        statement_hidden = sum(1 for e in self.hidden_entries if e.from_statement)
        difference = self.only_in_statement_sum - self.only_in_calendar_sum
        difference_color = COLOR_OK if difference == 0 else COLOR_WARNING
        verdict = (f"<p style='color:{COLOR_OK};'><b>Всё сопоставлено: платежи выписки и календаря "
                   f"сошлись.</b></p>" if not self.discrepancies else "")
        return "\n".join([
            "<table cellspacing='0' cellpadding='2'>",
            "<tr><th></th>" + "".join(f"<th align='right' style='{SUMMARY_PADDING}'>{title}</th>" for title in
                                      ("Всего", "Совпало", "Связано", "Скрыто", "Не сопоставлено",
                                       "На сумму")) + "</tr>",
            _summary_row("Выписка", (self.statement_total, self.statement_matched,
                                     sum(len(link.statement) for link in self.links), statement_hidden,
                                     self.only_in_statement_count), self.only_in_statement_sum, COLOR_STATEMENT),
            _summary_row("Календарь", (self.calendar_total, self.calendar_matched,
                                       sum(len(link.calendar) for link in self.links),
                                       len(self.hidden_entries) - statement_hidden,
                                       self.only_in_calendar_count), self.only_in_calendar_sum, COLOR_CALENDAR),
            "<tr><td colspan='6' align='right'>Разница (выписка − календарь)</td>"
            f"<td align='right' style='color:{difference_color};'><b>{dec_html(difference)}</b></td></tr>",
            "</table>",
            verdict,
        ])


def _assign_statement_keys(statement: StatementPayments) -> None:
    for fee_date, entries in statement.by_date.items():
        occurrences: dict[tuple, int] = {}
        for entry in entries:
            signature = (entry.amount, entry.descr)
            number = occurrences.get(signature, 0)
            occurrences[signature] = number + 1
            entry.key = f"s|{fee_date.isoformat()}|{entry.amount}|{entry.descr}|{number}"


def reconcile_statement_with_calendar(csv_filename: str, dbh: DBHandler,
                                       marks: ReconciliationMarks | None = None) -> ReconciliationResult | None:
    marks = marks or ReconciliationMarks()
    statement = extract_statement_payments(csv_filename, dbh)
    _assign_statement_keys(statement)
    calendar_by_date = dbh.get_paymentsum_for_period(statement.period[0], statement.period[1])
    if calendar_by_date is None:
        return None

    all_dates = sorted(set(statement.by_date) | set(calendar_by_date))
    leftovers: dict[date, tuple[list[PaymentEntry], list[PaymentEntry]]] = {}
    totals = {"statement": 0, "calendar": 0, "statement_matched": 0, "calendar_matched": 0}

    for fee_date in all_dates:
        statement_entries = statement.by_date.get(fee_date, [])
        calendar_entries = calendar_by_date.get(fee_date, [])
        for entry in statement_entries + calendar_entries:
            entry.fee_date = fee_date
        only_statement, only_calendar = _diff_amounts(statement_entries, calendar_entries)
        totals["statement"] += len(statement_entries)
        totals["calendar"] += len(calendar_entries)
        totals["statement_matched"] += len(statement_entries) - len(only_statement)
        totals["calendar_matched"] += len(calendar_entries) - len(only_calendar)
        if only_statement or only_calendar:
            leftovers[fee_date] = (only_statement, only_calendar)

    leftover_by_key = {entry.key: entry for sides in leftovers.values() for side in sides for entry in side}
    links: list[ManualLink] = []
    linked_keys: set[str] = set()
    for keys in marks.links:
        if all(key in leftover_by_key for key in keys) and linked_keys.isdisjoint(keys):
            linked_keys.update(keys)
            linked_entries = [leftover_by_key[key] for key in keys]
            links.append(ManualLink(keys, [e for e in linked_entries if e.from_statement],
                                    [e for e in linked_entries if not e.from_statement]))
    hidden_entries = sorted((e for key, e in leftover_by_key.items() if key in marks.hidden and key not in linked_keys),
                            key=lambda e: (e.fee_date, e.amount))
    skipped_keys = linked_keys | marks.hidden

    discrepancies: list[DateDiscrepancy] = []
    for fee_date, (only_statement, only_calendar) in leftovers.items():
        only_statement = [e for e in only_statement if e.key not in skipped_keys]
        only_calendar = [e for e in only_calendar if e.key not in skipped_keys]
        split_groups, only_statement, only_calendar = _merge_split_payments(
            fee_date, only_statement, only_calendar, marks.rejected)
        pairs, only_statement, only_calendar = _pair_probable_matches(only_statement, only_calendar, marks.rejected)
        groups, only_statement, only_calendar = _regroup_contract_payments(
            fee_date, only_statement, only_calendar, marks.rejected)
        groups = split_groups + groups
        if only_statement or only_calendar or pairs or groups:
            discrepancies.append(DateDiscrepancy(fee_date, only_statement, only_calendar, pairs, groups))

    fee_totals = {(fee_date, entry.fee_category): entry.amount
                  for fee_date, entries in statement.by_date.items() for entry in entries if entry.fee_category}
    return ReconciliationResult(statement.period, discrepancies, fee_totals, hidden_entries, links,
                                totals["statement"], totals["calendar"],
                                totals["statement_matched"], totals["calendar_matched"])
