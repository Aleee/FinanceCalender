import csv
import html

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

import lovely_logger as log

from base.casting import str_int
from base.dbhandler import DBHandler
from base.feeparser import (CODE_COLUMNINDEX, DATE_COLUMNINDEX, DESCR_COLUMNINDEX, SUM_COLUMNINDEX,
                            RECEIVER_COLUMNINDEX, FEE_IN_TEXT_PATTERN, INCOME_FEE_CODE, CSVParseError,
                            parse_date, parse_period, OUTGOING_FEE_CODES)
from base.formatting import (str_decimal, dec_html, COLOR_STATEMENT, COLOR_CALENDAR, COLOR_OK,
                             COLOR_HEADER_BG)


PAYROLL_KEYWORDS: tuple[str, ...] = (
    "окончательный расчет",
    "отпускные",
    "заработная плата",
    "отчисления в фсзн",
    "подоходный налог",
)
PAYROLL_DESCRIPTION: str = "Выплаты работникам (зарплата/отпускные/ФСЗН/налог)"


# ---------------------------------------------------------------------------
# 1. Извлечение эталонных сумм платежей из выписки
# ---------------------------------------------------------------------------

@dataclass
class StatementPayments:
    period: tuple[date, date]
    by_date: dict[date, list[tuple[Decimal, str]]] = field(default_factory=dict)

    def add(self, dt: date, amount: Decimal, descr: str) -> None:
        self.by_date.setdefault(dt, []).append((amount, descr))


def extract_statement_payments(filename: str, dbh) -> StatementPayments:

    columns_to_parse: list[int] = list(
        map(int, dbh.get_setting("CSVparser/columnstoparse").split(","))
    )
    # 1 и 9 - дефолты из gui/settingsdialog.py (DEF_ROW_PERIOD, DEF_ROW_TRANSACTIONSTART)
    row_period: int = str_int(dbh.get_setting("CSVparser/rowperiod"), 1) - 1
    row_transactions_start: int = str_int(dbh.get_setting("CSVparser/rowtransactionstart"), 9) - 1
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
                    is_outgoing_fee = (
                            transaction_code in OUTGOING_FEE_CODES
                            and any(kw in description_lower for kw in keyword_templates)
                    )
                    is_payroll = any(kw in description_lower for kw in PAYROLL_KEYWORDS)
                    if is_outgoing_fee:
                        outgoing_fee_totals[transaction_date] = (
                                outgoing_fee_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    elif is_payroll:
                        payroll_totals[transaction_date] = (
                                payroll_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    else:
                        payments.add(transaction_date, debit_amount, description_with_receiver)
                    continue

            # Дебета нет
            if transaction_code == INCOME_FEE_CODE:
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
        payments.add(transaction_date, total, "Комиссии в поступлениях")
    for transaction_date, total in outgoing_fee_totals.items():
        payments.add(transaction_date, total, "Комиссии к уплате")
    for transaction_date, total in payroll_totals.items():
        payments.add(transaction_date, total, PAYROLL_DESCRIPTION)

    payments.period = period
    return payments


# ---------------------------------------------------------------------------
# 2. Сравнение (только по суммам, мультимножество) и отчёт
# ---------------------------------------------------------------------------

def _split_trailing_parenthetical(text: str) -> Optional[tuple[str, str]]:
    if not text.endswith(")"):
        return None
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                head_end = i - 1 if i > 0 and text[i - 1] == " " else i
                return text[:head_end], text[i:]
    return None


def _clean_descr(text: str, limit: int = 100) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text

    split = _split_trailing_parenthetical(text)
    if split:
        head, suffix = split
        available = limit - len(suffix) - 2
        if available > 0:
            return head[:available].rstrip() + "… " + suffix

    return text[: limit - 1].rstrip() + "…"


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


def _diff_amounts(statement_entries: list[tuple[Decimal, str]], calendar_entries: list[tuple[Decimal, str]]) \
        -> tuple[list[tuple[Decimal, str]], list[tuple[Decimal, str]]]:

    remaining_calendar = list(calendar_entries)
    unmatched_statement: list[tuple[Decimal, str]] = []
    for amount, descr in statement_entries:
        match_index = next(
            (i for i, (cal_amount, _) in enumerate(remaining_calendar) if cal_amount == amount), None
        )
        if match_index is None:
            unmatched_statement.append((amount, descr))
        else:
            remaining_calendar.pop(match_index)
    return unmatched_statement, remaining_calendar


@dataclass
class DateDiscrepancy:
    fee_date: date
    only_in_statement: list[tuple[Decimal, str]]
    only_in_calendar: list[tuple[Decimal, str]]


@dataclass
class ReconciliationResult:
    period: tuple[date, date]
    discrepancies: list[DateDiscrepancy]

    @property
    def only_in_statement_count(self) -> int:
        return sum(len(d.only_in_statement) for d in self.discrepancies)

    @property
    def only_in_statement_sum(self) -> Decimal:
        return sum(
            (sum((amount for amount, _ in d.only_in_statement), Decimal("0")) for d in self.discrepancies),
            Decimal("0"),
        )

    @property
    def only_in_calendar_count(self) -> int:
        return sum(len(d.only_in_calendar) for d in self.discrepancies)

    @property
    def only_in_calendar_sum(self) -> Decimal:
        return sum(
            (sum((amount for amount, _ in d.only_in_calendar), Decimal("0")) for d in self.discrepancies),
            Decimal("0"),
        )

    @property
    def has_discrepancies(self) -> bool:
        return bool(self.discrepancies)

    def format_report(self, full: bool = False) -> str:
        period_from = self.period[0].strftime("%d.%m.%Y")
        period_to = self.period[1].strftime("%d.%m.%Y")
        header = f"<h3>Сверка выписки за период {period_from} – {period_to}</h3>"

        if not self.discrepancies:
            return (f"{header}<p style='color:{COLOR_OK};'>"
                    f"Расхождений не найдено: все платежи из выписки учтены в календаре.</p>")

        lines = [
            header,
            "<table cellspacing='0' cellpadding='3'>",
            _summary_row("Только в выписке:", self.only_in_statement_count,
                         self.only_in_statement_sum, COLOR_STATEMENT),
            _summary_row("Только в календаре:", self.only_in_calendar_count,
                         self.only_in_calendar_sum, COLOR_CALENDAR),
            "</table>",
            "<br>",
            "<table width='100%' cellspacing='0' cellpadding='4' border='0'>",
        ]

        if full:
            for d in self.discrepancies:
                lines.extend(self._render_date_full(d))
        else:
            lines.append(
                f"<tr bgcolor='{COLOR_HEADER_BG}'><th align='left'>Дата</th>"
                f"<th align='left' width='45%' style='color:{COLOR_STATEMENT};'>Есть в выписке, нет в календаре</th>"
                f"<th align='left' width='45%' style='color:{COLOR_CALENDAR};'>Есть в календаре, нет в выписке</th></tr>"
            )
            for d in self.discrepancies:
                lines.extend(self._render_date_short(d))

        lines.append("</table>")
        return "\n".join(lines)

    @staticmethod
    def _render_date_short(d: "DateDiscrepancy") -> list[str]:
        date_label = d.fee_date.strftime("%d.%m.%Y")
        statement_amounts = ", ".join(dec_html(amount) for amount, _ in d.only_in_statement)
        calendar_amounts = ", ".join(dec_html(amount) for amount, _ in d.only_in_calendar)
        return [
            f"<tr><td valign='top'><b>{date_label}</b></td>"
            f"<td valign='top' style='color:{COLOR_STATEMENT};'>{statement_amounts}</td>"
            f"<td valign='top' style='color:{COLOR_CALENDAR};'>{calendar_amounts}</td></tr>"
        ]

    @staticmethod
    def _render_date_full(d: "DateDiscrepancy") -> list[str]:
        date_label = d.fee_date.strftime("%d.%m.%Y")
        lines = [f"<tr bgcolor='{COLOR_HEADER_BG}'><td colspan='2'><b>{date_label}</b></td></tr>"]
        groups = (
            ("Есть в выписке, но нет в календаре", d.only_in_statement, COLOR_STATEMENT),
            ("Есть в календаре, но нет в выписке", d.only_in_calendar, COLOR_CALENDAR),
        )
        for title, entries, color in groups:
            if not entries:
                continue
            lines.append(f"<tr><td colspan='2' style='color:{color};'><i>{title}:</i></td></tr>")
            for amount, descr in entries:
                lines.append(
                    f"<tr><td align='right' width='130' style='color:{color};'>{dec_html(amount)}</td>"
                    f"<td>{html.escape(_clean_descr(descr))}</td></tr>"
                )
        return lines


def reconcile_statement_with_calendar(csv_filename: str, dbh: DBHandler) -> ReconciliationResult | None:
    statement = extract_statement_payments(csv_filename, dbh)
    calendar_by_date = dbh.get_paymentsum_for_period(statement.period[0], statement.period[1])
    if calendar_by_date is None:
        return None

    all_dates = sorted(set(statement.by_date) | set(calendar_by_date))
    discrepancies: list[DateDiscrepancy] = []

    for fee_date in all_dates:
        only_statement, only_calendar = _diff_amounts(
            statement.by_date.get(fee_date, []), calendar_by_date.get(fee_date, [])
        )
        if only_statement or only_calendar:
            discrepancies.append(DateDiscrepancy(fee_date, only_statement, only_calendar))

    return ReconciliationResult(period=statement.period, discrepancies=discrepancies)