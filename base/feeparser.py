import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date
from typing import Optional

import lovely_logger as log

from base.formatting import dec_strcommaspace, str_decimal
from gui.settings import SettingsHandler

# --- Роли столбцов, в порядке, в котором они перечислены в CSVparser/columnstoparse ---
DATE_COLUMNINDEX: int = 0
CODE_COLUMNINDEX: int = 1
UNP_COLUMNINDEX: int = 2
NAME_COLUMNINDEX: int = 3
SUM_COLUMNINDEX: int = 4
DESCR_COLUMNINDEX: int = 5
RECEIVER_COLUMNINDEX: int = 6

# Комиссия банка, "спрятанная" внутри зачисления (эквайринг/ЕРИП) — всегда код 6
INCOME_FEE_CODE: str = "6"
# Комиссии, которые платим сами / которые банк списывает отдельным требованием — коды 2 и 6
OUTGOING_FEE_CODES: tuple[str, ...] = ("2", "6")

FEE_IN_TEXT_PATTERN = re.compile(r"комиссия\s+(\d+(?:[.,]\d+)?)")


class CSVParseError(Exception):
    """Ошибка разбора банковской выписки"""


@dataclass
class DailyFees:
    """Агрегат по одной дате внутри одной категории комиссий"""

    count: int = 0
    total: Decimal = Decimal("0")
    amounts: list[Decimal] = field(default_factory=list)

    def add(self, amount: Decimal) -> None:
        self.count += 1
        self.total += amount
        self.amounts.append(amount)

    def as_comment(self) -> str:
        amounts_str = ", ".join(dec_strcommaspace(a, add_rub=True) for a in self.amounts)
        return f"Всего комиссий: {self.count} (в том числе на суммы: {amounts_str})"


@dataclass
class FeeCategoryResult:
    """Результат разбора одной из двух категорий комиссий"""

    daily: dict[date, DailyFees] = field(default_factory=dict)
    unknown_unp: list[tuple[str, date, str]] = field(default_factory=list)

    def add(self, dt: date, amount: Decimal) -> None:
        self.daily.setdefault(dt, DailyFees()).add(amount)

    @property
    def payments(self) -> dict[date, Decimal]:
        """Дата -> сумма комиссий за эту дату"""
        return {dt: agg.total for dt, agg in self.daily.items()}

    @property
    def comments(self) -> dict[date, str]:
        """Дата -> текст комментария к платежу."""
        return {dt: agg.as_comment() for dt, agg in self.daily.items()}


@dataclass
class StatementParseResult:
    period: tuple[date, date]
    income_fees: FeeCategoryResult  # код 6, сумма из текста — комиссии банка из поступлений
    outgoing_fees: FeeCategoryResult  # коды 2 и 6, сумма из "Дебет" — уплаченные/списанные отдельно


def parse_period(text: str) -> Optional[tuple[date, date]]:
    match = re.search(r"С (\d{2}\.\d{2}\.\d{4}) ПО (\d{2}\.\d{2}\.\d{4})", text)
    if not match:
        return None
    try:
        return (
            datetime.strptime(match.group(1), "%d.%m.%Y").date(),
            datetime.strptime(match.group(2), "%d.%m.%Y").date(),
        )
    except ValueError:
        return None


def parse_date(raw: str, row_index: int) -> date:
    try:
        return datetime.strptime(raw, "%d.%m.%Y").date()
    except ValueError:
        raise CSVParseError(f"Не удалось получить дату из строки {row_index}: {raw!r}")


def read_transaction_csv(filename: str, sh: SettingsHandler) -> StatementParseResult:
    """
    Разбирает банковскую выписку и возвращает две независимые категории комиссий:
    - income_fees: комиссии банка, удержанные из поступлений клиентов (код 6),
      сумма вычленяется из текста назначения платежа;
    - outgoing_fees: комиссии, которые платим сами / которые банк списывает
      отдельным платёжным требованием (коды 2 и 6, определяются по ключевым
      словам из настроек), сумма берётся полностью из столбца "Дебет".
    """

    columns_to_parse: list[int] = list(
        map(int, sh.settings.value("CSVparser/columnstoparse").split(","))
    )
    known_unp: list[str] = [
        x for x in sh.settings.value("CSVparser/knownunp").split(",") if x
    ]
    keyword_templates: set[str] = {
        sub.strip().lower()
        for sub in sh.settings.value("CSVparser/patterns").split(",")
        if sub.strip()
    }
    row_period: int = int(sh.settings.value("CSVparser/rowperiod")) - 1
    row_transactions_start: int = int(sh.settings.value("CSVparser/rowtransactionstart")) - 1

    period: Optional[tuple[date, date]] = None
    income_fees = FeeCategoryResult()
    outgoing_fees = FeeCategoryResult()

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
            except IndexError:
                log.e(f"Ошибка обработки строки {row_index}: столбец недостижим (IndexError)")
                break

            is_income_fee_code = transaction_code == INCOME_FEE_CODE
            is_outgoing_fee_code = transaction_code in OUTGOING_FEE_CODES
            if not (is_income_fee_code or is_outgoing_fee_code):
                continue  # нетранзакционные строки (сальдо/итоги) и прочие коды

            try:
                description: str = content[columns_to_parse[DESCR_COLUMNINDEX]]
                unp: str = content[columns_to_parse[UNP_COLUMNINDEX]]
                receiver: str = content[columns_to_parse[RECEIVER_COLUMNINDEX]]
                raw_date: str = content[columns_to_parse[DATE_COLUMNINDEX]]
            except IndexError:
                log.e(f"Ошибка обработки строки {row_index}: столбец недостижим (IndexError)")
                break

            description_lower = description.lower()
            matched_as_income_fee = False

            # --- Категория А: комиссия банка, зашитая в тексте поступления (код 6) ---
            if is_income_fee_code:
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
                    income_fees.add(transaction_date, fee)
                    if unp not in known_unp:
                        income_fees.unknown_unp.append((unp, transaction_date, receiver))
                    matched_as_income_fee = True

            # --- Категория Б: комиссии по ключевым словам, коды 2 и 6, сумма из "Дебет" ---
            if (
                not matched_as_income_fee
                and is_outgoing_fee_code
                and any(kw in description_lower for kw in keyword_templates)
            ):
                debit_raw = content[columns_to_parse[SUM_COLUMNINDEX]]
                fee = str_decimal(debit_raw)
                if fee is None:
                    raise CSVParseError(f"Не удалось преобразовать в число значение Дебета: {debit_raw!r}")
                transaction_date = parse_date(raw_date, row_index)
                outgoing_fees.add(transaction_date, fee)
                if unp not in known_unp:
                    outgoing_fees.unknown_unp.append((unp, transaction_date, receiver))

    if period is None:
        raise CSVParseError("В файле не найдена строка с периодом выписки")

    return StatementParseResult(period=period, income_fees=income_fees, outgoing_fees=outgoing_fees)
