import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date
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
# Комиссии, которые платим сами / которые банк списывает отдельным требованием — коды 2 и 6
OUTGOING_FEE_CODES: tuple[str, ...] = ("2", "6")

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


@dataclass
class FeeRecord:

    fee_date: date
    amount: Decimal
    unp: str
    receiver: str
    description: str
    is_known_unp: bool


@dataclass
class FeeCategoryResult:

    daily: dict[date, DailyFees] = field(default_factory=dict)
    unknown_unp: list[tuple[str, date, str]] = field(default_factory=list)
    records: list[FeeRecord] = field(default_factory=list)

    def add(self, dt: date, amount: Decimal, unp: str, receiver: str, description: str, is_known_unp: bool) -> None:
        self.daily.setdefault(dt, DailyFees()).add(amount)
        self.records.append(FeeRecord(dt, amount, unp, receiver, description, is_known_unp))
        if not is_known_unp:
            self.unknown_unp.append((unp, dt, receiver))

    @property
    def payments(self) -> dict[date, Decimal]:
        return {dt: agg.total for dt, agg in self.daily.items()}

    @property
    def comments(self) -> dict[date, str]:
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


def read_transaction_csv(filename: str, dbh: DBHandler) -> StatementParseResult:

    columns_to_parse: list[int] = list(
        map(int, dbh.get_setting("CSVparser/columnstoparse").split(","))
    )
    known_unp: list[str] = [
        x for x in dbh.get_setting("CSVparser/knownunp").split(",") if x
    ]
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
                    income_fees.add(transaction_date, fee, unp, receiver, description, unp in known_unp)
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
                outgoing_fees.add(transaction_date, fee, unp, receiver, description, unp in known_unp)

    if period is None:
        raise CSVParseError("В файле не найдена строка с периодом выписки")

    return StatementParseResult(period=period, income_fees=income_fees, outgoing_fees=outgoing_fees)
