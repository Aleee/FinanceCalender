import csv
import decimal
import re
from decimal import Decimal
from typing import Optional

import lovely_logger as log
from datetime import datetime, date

from gui.settings import SettingsHandler

DATE_COLUMNINDEX: int = 0
CODE_COLUMNINDEX: int = 1
UNP_COLUMNINDEX: int = 2
NAME_COLUMNINDEX: int = 3
SUM_COLUMNINDEX: int = 4
DESCR_COLUMNINDEX: int = 5


def read_transaction_csv(filename: str, sh: SettingsHandler) -> tuple | bool:

    results: dict = {}
    unknown_unp: list = []

    with open(filename, newline="", encoding="windows-1251") as f:

        reader = csv.reader(f, delimiter=";")
        columns_to_parse: list = list(map(int, sh.settings.value("CSVparser/columnstoparse").split(",")))
        known_unp: list = [x for x in sh.settings.value("CSVparser/knownunp").split(",") if x]

        for row, content in enumerate(reader):
            if row == int(sh.settings.value("CSVparser/rowperiod")) - 1:
                try:
                    match = re.search(r'С (\d{2}\.\d{2}\.\d{4}) ПО (\d{2}\.\d{2}\.\d{4})', content[columns_to_parse[DATE_COLUMNINDEX]])
                except IndexError:
                    log.w("Парсинг CSV: не удалось найти значение в строке ROW_PERIOD")
                    return False
                if match:
                    date_from: Optional[re.Match[str]] = match.group(1)
                    date_to: Optional[re.Match[str]] = match.group(2)
                    try:
                        date_from: date = datetime.strptime(match.group(1), "%d.%m.%Y").date()
                        date_to: date = datetime.strptime(match.group(2), "%d.%m.%Y").date()
                    except ValueError:
                        log.w("Парсинг CSV: не удалось преобразовать даты в строке ROW_PERIOD")
                        return False
                else:
                    log.w("Парсинг CSV: в строке ROW_PERIOD не обнаружено ожидаемого паттерна")
                    return False
            elif row >= int(sh.settings.value("CSVparser/rowtransactionstart")) - 1:
                try:
                    # Исключение всех строк с кодом, отличным от кода поступлений
                    transaction_code: str = content[columns_to_parse[CODE_COLUMNINDEX]]
                    if transaction_code != str(sh.settings.value("CSVparser/transactioncode")):
                        continue

                    # Исключение строк, не содержащих упоминания о комиссии, и получение комиссии
                    transaction_name: str = content[columns_to_parse[DESCR_COLUMNINDEX]]
                    matches = re.findall(r'комиссия\s+(\d+(?:[.,]\d+)?)', transaction_name)
                    if len(matches) == 0:
                        continue
                    elif len(matches) > 1:
                        log.w(f"Парсинг CSV: в следующей строке найдено более 1 искомой группы: {transaction_name}")
                        return False
                    try:
                        fee: Decimal = Decimal(str(matches[0]).replace(",", "."))
                    except decimal.ConversionSyntax:
                        log.w(f"Парсинг CSV: не удалось преобразовать в число следующее значение: {str(matches[0])}")
                        return False

                    # Получение даты
                    try:
                        transaction_date: date = datetime.strptime(content[columns_to_parse[DATE_COLUMNINDEX]], "%d.%m.%Y").date()
                    except ValueError:
                        log.w(f"Парсинг CSV: не удалось получить дату из следующей строки: {content}")
                        return False

                    # Сверка УНП со списком доверенных
                    unp: str = content[columns_to_parse[UNP_COLUMNINDEX]]
                    if unp not in known_unp:
                        unknown_unp.append((unp, transaction_date, transaction_name))

                    if transaction_date in results:
                        results[transaction_date][0] += 1
                        results[transaction_date][1] += fee
                    else:
                        results[transaction_date] = [1, fee]

                except IndexError:
                    break

    return results, (date_from, date_to), unknown_unp
