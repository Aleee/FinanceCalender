import csv

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from base.dbhandler import DBHandler
from base.feeparser import (CODE_COLUMNINDEX, DATE_COLUMNINDEX, DESCR_COLUMNINDEX, SUM_COLUMNINDEX,
                            RECEIVER_COLUMNINDEX, FEE_IN_TEXT_PATTERN, INCOME_FEE_CODE, CSVParseError,
                            parse_date, parse_period, OUTGOING_FEE_CODES)
from base.formatting import str_decimal, dec_strcommaspace


# Ключевые слова для строк, относящихся к выплатам работникам. Совпадение
# ищется независимо от кода операции (в отличие от outgoing-комиссий) —
# все такие строки за одну дату схлопываются в ОДИН суммовый платёж,
# как их, судя по всему, и заносят в календарь одной записью на дату.
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


def extract_statement_payments(filename: str, sh) -> StatementPayments:
    """
    Возвращает по каждой дате список сумм (с описанием операции), которые
    должны быть списаны со счёта: обычные операции по "Дебету" — поштучно,
    каждая своей суммой и своим назначением платежа; комиссии — ОДНИМ
    суммовым платежом на дату per категория, ровно так, как их создаёт
    FeeDialog.make_fee_payments (см. base.feeparser):

    - комиссии банка, зашитые в текст зачислений с кодом 6 (income_fees);
    - комиссии, уплаченные/списанные отдельно, коды 2 и 6 по ключевым
      словам из настроек (outgoing_fees), сумма из "Дебет".

    Чистые поступления без комиссии в тексте не включаются — это не платежи.
    """

    columns_to_parse: list[int] = list(
        map(int, sh.settings.value("CSVparser/columnstoparse").split(","))
    )
    row_period: int = int(sh.settings.value("CSVparser/rowperiod")) - 1
    row_transactions_start: int = int(sh.settings.value("CSVparser/rowtransactionstart")) - 1
    keyword_templates: set[str] = {
        sub.strip().lower()
        for sub in sh.settings.value("CSVparser/patterns").split(",")
        if sub.strip()
    }

    period: Optional[tuple[date, date]] = None
    payments = StatementPayments(period=(None, None))  # period проставим в конце

    # Комиссии агрегируются по дате — по одной сумме на категорию, а не
    # по одной сумме на транзакцию, иначе сверка с календарём (где на дату
    # всегда 0/1/2 суммовых платежа) будет ложно находить расхождение.
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
                break  # конец таблицы транзакций

            try:
                transaction_code: str = content[columns_to_parse[CODE_COLUMNINDEX]]
                description: str = content[columns_to_parse[DESCR_COLUMNINDEX]]
                receiver: str = content[columns_to_parse[RECEIVER_COLUMNINDEX]]
                debit_raw: str = content[columns_to_parse[SUM_COLUMNINDEX]]
                raw_date: str = content[columns_to_parse[DATE_COLUMNINDEX]]
            except IndexError:
                break  # повреждённая строка / конец таблицы

            description_lower = description.lower()
            debit_stripped = debit_raw.strip()
            # Назначение платежа + контрагент в скобках — только для обычных
            # (не агрегируемых) строк, где это один конкретный контрагент.
            description_with_receiver = f"{description} ({receiver})" if receiver.strip() else description

            # --- Есть сумма по Дебету ---
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
                        # Уйдёт одним суммовым платежом за дату — не добавляем поштучно
                        outgoing_fee_totals[transaction_date] = (
                                outgoing_fee_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    elif is_payroll:
                        # Зарплата/отпускные/ФСЗН/налог за одну дату — тоже один суммовый платёж
                        payroll_totals[transaction_date] = (
                                payroll_totals.get(transaction_date, Decimal("0")) + debit_amount
                        )
                    else:
                        payments.add(transaction_date, debit_amount, description_with_receiver)
                    continue

            # --- Дебета нет — это поступление. Учитываем только зашитую в нём комиссию ---
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

    # Здесь и добавляем по ОДНОМУ суммовому платежу на дату на каждую
    # категорию комиссий — ровно так, как их создаёт FeeDialog.
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
    """
    Находит замыкающую скобочную группу в конце строки — считая баланс с
    конца, а не простым regex, потому что внутри контрагента тоже могут
    быть свои скобки (например: "...(ИЛИ) ВЕДЕНИЕ...(KOMИC. ДOX. ЗА
    ОТКРЫТИЕ И (ИЛИ) ВЕДЕНИЕ БАНК. СЧЕТОВ)"). Возвращает (текст_до, "(...)")
    или None, если строка не заканчивается сбалансированной скобкой.
    """
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
    """
    Схлопывает лишние пробелы/переносы и обрезает длинное назначение платежа
    для отчёта. Если строка заканчивается контрагентом в скобках (мы сами
    приписываем его в extract_statement_payments) — обрезаем только текст
    назначения, а контрагента не трогаем, иначе он потеряется из-за обрезки
    как раз в тех длинных описаниях, где он нужнее всего.
    """
    text = " ".join(text.split())
    if len(text) <= limit:
        return text

    split = _split_trailing_parenthetical(text)
    if split:
        head, suffix = split
        available = limit - len(suffix) - 1
        if available > 0:
            return head[:available].rstrip() + "…" + suffix

    return text[: limit - 1].rstrip() + "…"


def _diff_amounts(
    statement_entries: list[tuple[Decimal, str]], calendar_entries: list[tuple[Decimal, str]]
) -> tuple[list[tuple[Decimal, str]], list[tuple[Decimal, str]]]:
    """
    Попарно "гасит" одинаковые суммы между выпиской и календарём (сверка
    только по сумме, назначение платежа не участвует в сопоставлении —
    оно лишь переносится дальше вместе с несопоставленной суммой, чтобы
    показать в подробном отчёте, откуда она взялась).
    """
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
        header = f"Сверка выписки за период {period_from} - {period_to}."

        if not self.discrepancies:
            return f"{header}\nРасхождений не найдено: все платежи из выписки учтены в календаре."

        lines = [
            header,
            f"Найдено расхождений по датам: {len(self.discrepancies)}.",
            "",
        ]

        render_date = self._render_date_full if full else self._render_date_short
        for d in self.discrepancies:
            lines.extend(render_date(d))

        lines.append("")
        lines.append(
            f"Итого только в выписке: {self.only_in_statement_count} платежей "
            f"на {dec_strcommaspace(self.only_in_statement_sum, add_rub=True)}"
        )
        lines.append(
            f"Итого только в календаре: {self.only_in_calendar_count} платежей "
            f"на {dec_strcommaspace(self.only_in_calendar_sum, add_rub=True)}"
        )
        return "\n".join(lines)

    @staticmethod
    def _render_date_short(d: "DateDiscrepancy") -> list[str]:
        """Как раньше: суммы одной строкой через запятую, без назначения платежа."""
        date_label = d.fee_date.strftime("%d.%m.%Y")
        parts = []
        if d.only_in_statement:
            amounts = ", ".join(dec_strcommaspace(amount, add_rub=True) for amount, _ in d.only_in_statement)
            parts.append(
                f"в выписке, но нет в календаре — {len(d.only_in_statement)} "
                f"(на суммы: {amounts})"
            )
        if d.only_in_calendar:
            amounts = ", ".join(dec_strcommaspace(amount, add_rub=True) for amount, _ in d.only_in_calendar)
            parts.append(
                f"в календаре, но нет в выписке — {len(d.only_in_calendar)} "
                f"(на суммы: {amounts})"
            )
        return [f"- {date_label}: " + "; ".join(parts)]

    @staticmethod
    def _render_date_full(d: "DateDiscrepancy") -> list[str]:
        """Подробно: каждая сумма на отдельной строке, с назначением платежа/описанием записи."""
        date_label = d.fee_date.strftime("%d.%m.%Y")
        lines = [f"- {date_label}:"]
        if d.only_in_statement:
            lines.append("  В выписке, но нет в календаре:")
            for amount, descr in d.only_in_statement:
                lines.append(f"    • {dec_strcommaspace(amount, add_rub=True)} — {_clean_descr(descr)}")
        if d.only_in_calendar:
            lines.append("  В календаре, но нет в выписке:")
            for amount, descr in d.only_in_calendar:
                lines.append(f"    • {dec_strcommaspace(amount, add_rub=True)} — {_clean_descr(descr)}")
        return lines


def reconcile_statement_with_calendar(csv_filename: str, dbh: DBHandler, sh) -> ReconciliationResult | None:
    statement = extract_statement_payments(csv_filename, sh)
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