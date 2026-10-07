import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date
from enum import Enum, auto
from typing import Optional

import lovely_logger as log

from base.casting import str_int
from base.formatting import dec_strcommaspace, str_decimal
from base.dbhandler import DBHandler

# --- Роли столбцов, в порядке, в котором они перечислены в CSVparser/columnstoparse ---
DATE_COLUMNINDEX: int = 0
CODE_COLUMNINDEX: int = 1
UNP_COLUMNINDEX: int = 2
SUM_COLUMNINDEX: int = 4
DESCR_COLUMNINDEX: int = 5
RECEIVER_COLUMNINDEX: int = 6

# Комиссия банка, "спрятанная" внутри зачисления (эквайринг/ЕРИП) — всегда код 6
INCOME_FEE_CODE: str = "6"
# Комиссии, которые банк списывает отдельным требованием — код 2
OUTGOING_FEE_CODE: str = "2"

FEE_IN_TEXT_PATTERN = re.compile(r"комиссия\s+(\d{1,3}(?:[ \xa0]\d{3})*(?:[.,]\d+)?)")


class CSVParseError(Exception):
    """Ошибка разбора банковской выписки"""


@dataclass
class DailyFees:

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


class FeeKind(Enum):

    NONE = auto()
    EMBEDDED = auto()
    INCOME = auto()
    OUTGOING = auto()
    SUSPICIOUS_NO_KEYWORDS = auto()
    SUSPICIOUS_NOT_BANK_UNP = auto()


SUSPICIOUS_REASONS: dict[FeeKind, str] = {
    FeeKind.SUSPICIOUS_NO_KEYWORDS: "УНП банка, но нет ключевых слов",
    FeeKind.SUSPICIOUS_NOT_BANK_UNP: "Есть ключевые слова, но УНП не из списка банков",
}


@dataclass
class FeeRecord:

    fee_date: date
    amount: Decimal
    unp: str
    receiver: str
    description: str
    is_known_unp: bool = True


@dataclass
class SuspiciousRecord:

    record: FeeRecord
    reason: str


@dataclass
class FeeCategoryResult:

    daily: dict[date, DailyFees] = field(default_factory=dict)
    unknown_unp: list[tuple[str, date, str]] = field(default_factory=list)
    suspicious: list[SuspiciousRecord] = field(default_factory=list)
    records: list[FeeRecord] = field(default_factory=list)

    def add(
        self, dt: date, amount: Decimal, unp: str, receiver: str, description: str, is_known_unp: bool = True
    ) -> None:
        self.daily.setdefault(dt, DailyFees()).add(amount)
        self.records.append(FeeRecord(dt, amount, unp, receiver, description, is_known_unp))
        if not is_known_unp:
            self.unknown_unp.append((unp, dt, receiver))

    def add_suspicious(
        self, dt: date, amount: Decimal, unp: str, receiver: str, description: str, reason: str
    ) -> None:
        self.suspicious.append(SuspiciousRecord(FeeRecord(dt, amount, unp, receiver, description), reason))

    @property
    def payments(self) -> dict[date, Decimal]:
        return {dt: agg.total for dt, agg in self.daily.items()}

    @property
    def comments(self) -> dict[date, str]:
        return {dt: agg.as_comment() for dt, agg in self.daily.items()}


@dataclass
class StatementParseResult:
    period: tuple[date, date]
    income_fees: FeeCategoryResult  # код 6: зашитые (сумма из текста) и УНП банка + ключевые слова (из "Дебет")
    outgoing_fees: FeeCategoryResult  # код 2 + УНП банка, сумма из "Дебет" — списанные отдельно


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


def read_bank_unp(dbh: DBHandler) -> list[str]:
    return [x for x in dbh.get_setting("CSVparser/knownunp").split(",") if x]


def classify_fee(
    transaction_code: str, unp: str, description: str, bank_unp: list[str], keyword_templates: set[str]
) -> FeeKind:
    is_bank_unp = unp in bank_unp
    has_keywords = any(kw in description.lower() for kw in keyword_templates)

    if transaction_code == INCOME_FEE_CODE:
        if FEE_IN_TEXT_PATTERN.search(description):
            return FeeKind.EMBEDDED
        if is_bank_unp and has_keywords:
            return FeeKind.INCOME
        if is_bank_unp:
            return FeeKind.SUSPICIOUS_NO_KEYWORDS
        if has_keywords:
            return FeeKind.SUSPICIOUS_NOT_BANK_UNP
    elif transaction_code == OUTGOING_FEE_CODE and is_bank_unp:
        return FeeKind.OUTGOING
    return FeeKind.NONE


def read_debit(content: list[str], columns_to_parse: list[int]) -> Decimal:
    debit_raw = content[columns_to_parse[SUM_COLUMNINDEX]]
    debit = str_decimal(debit_raw)
    if debit is None:
        raise CSVParseError(f"Не удалось преобразовать в число значение Дебета: {debit_raw!r}")
    return debit


def read_transaction_csv(filename: str, dbh: DBHandler) -> StatementParseResult:

    columns_to_parse: list[int] = list(
        map(int, dbh.get_setting("CSVparser/columnstoparse").split(","))
    )
    bank_unp: list[str] = read_bank_unp(dbh)
    keyword_templates: set[str] = {
        sub.strip().lower()
        for sub in dbh.get_setting("CSVparser/patterns").split(",")
        if sub.strip()
    }
    # 1 и 9 - дефолты из gui/settingsdialog.py (DEF_ROW_PERIOD, DEF_ROW_TRANSACTIONSTART)
    row_period: int = str_int(dbh.get_setting("CSVparser/rowperiod"), 1) - 1
    row_transactions_start: int = str_int(dbh.get_setting("CSVparser/rowtransactionstart"), 9) - 1

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
            is_outgoing_fee_code = transaction_code == OUTGOING_FEE_CODE
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

            fee_kind = classify_fee(transaction_code, unp, description, bank_unp, keyword_templates)
            if fee_kind == FeeKind.NONE:
                continue

            transaction_date = parse_date(raw_date, row_index)

            # Категория А: зашитая в тексте поступления комиссия (код 6), сумма из текста
            if fee_kind == FeeKind.EMBEDDED:
                matches = FEE_IN_TEXT_PATTERN.findall(description)
                if len(matches) > 1:
                    raise CSVParseError(
                        f"Строка {row_index}: найдено более одного совпадения суммы комиссии: {description}"
                    )
                fee = str_decimal(matches[0])
                if fee is None:
                    raise CSVParseError(f"Не удалось преобразовать в число: {matches[0]!r}")
                income_fees.add(transaction_date, fee, unp, receiver, description, unp in bank_unp)

            # Категория А: прочие комиссии (код 6, УНП банка + ключевые слова), сумма из "Дебет"
            elif fee_kind == FeeKind.INCOME:
                income_fees.add(transaction_date, read_debit(content, columns_to_parse), unp, receiver, description)

            # Категория Б: код 2 и УНП банка, сумма из "Дебет"
            elif fee_kind == FeeKind.OUTGOING:
                outgoing_fees.add(transaction_date, read_debit(content, columns_to_parse), unp, receiver, description)

            else:
                amount = str_decimal(content[columns_to_parse[SUM_COLUMNINDEX]]) or Decimal("0")
                income_fees.add_suspicious(
                    transaction_date, amount, unp, receiver, description, SUSPICIOUS_REASONS[fee_kind]
                )

    if period is None:
        raise CSVParseError("В файле не найдена строка с периодом выписки")

    return StatementParseResult(period=period, income_fees=income_fees, outgoing_fees=outgoing_fees)
