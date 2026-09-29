import os
import shutil
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from idlelib import query
from pathlib import Path
from datetime import date
from typing import Any, Optional

from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import lovely_logger as log

from base.casting import str_int
from base.date import str_date, date_str, date_displstr, days_to_weekend, days_to_month
from base.formatting import str_decimal
from base.liability import LiabilityCategory, FilterFlags, RowType
from base.payment import Payment
from base.contract import PaymentDueType, DaysType, MonthType, ContractDocumentData
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.finplanmodel import FinPlanTableModel


class DBHandler:

    DB_VERSION: int = 2
    DEFAULT_DB_RELPATH: str = "db/db.db"
    EVENT_TABLE_COLUMNUM: int = 22
    PAYMENT_TABLE_COLUMNUM: int = 5

    DATE_FORMAT = "yyyy-MM-dd"

    def __init__(self, settings_handler):
        self.settings_handler = settings_handler
        self.db: QSqlDatabase = QSqlDatabase.addDatabase("QSQLITE")

        self.personal_data_max_id: int = 0

    @staticmethod
    def _is_null(value: Any) -> bool:
        return value is None or (hasattr(value, "isNull") and value.isNull())

    def _enum_from_db(self, enum_cls, value: Any):
        if self._is_null(value) or value == "":
            return None
        return enum_cls(value)

    @staticmethod
    def _enum_to_db(member: Optional[Enum]) -> Optional[str]:
        return None if member is None else member.value

    def check_db_files_exists(self) -> bool:
        db_path: str = os.path.abspath(self.DEFAULT_DB_RELPATH)
        if not Path(db_path).is_file():
            log.w(f"Не удалось открыть базу данных по стандартному пути (файла не существует): {db_path}")
            return False
        return True

    def check_db_file_integrity(self, alternative_path: str = "") -> bool:
        if alternative_path:
            db_path: str = alternative_path
        else:
            db_path: str = os.path.abspath(self.DEFAULT_DB_RELPATH)
        self.db.setDatabaseName(db_path)
        if not self.db.open():
            log.w(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {db_path}")
            return False
        query = QSqlQuery("SELECT value FROM meta WHERE key = 'db_version'")
        if not query.exec():
            log.w(f"Не удалось проверить версию базы данных. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        try:
            query.next()
            version = int(query.value(0))
        except (ValueError, TypeError) as e:
            log.w(f"Недопустимное значение версии базы данных. Ошибка: {e}")
            self.db.close()
            return False
        if version != self.DB_VERSION:
            log.w(f"Версия базы данных не соответствует версии клиента (загружаемая: {version}, требуемая: {self.DB_VERSION})")
            self.db.close()
            return False
        query = QSqlQuery("SELECT COUNT(*) FROM pragma_table_info('event')")
        if not query.exec():
            log.w(f"Не удалось проверить количество столбцов в таблице event. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) != self.EVENT_TABLE_COLUMNUM:
            log.w(f"Количество столбцов в таблице event ({query.value(0)}) не соответствует ожидаемому ({self.EVENT_TABLE_COLUMNUM}).")
            self.db.close()
            return False
        query = QSqlQuery("SELECT COUNT(*) FROM pragma_table_info('payment')")
        if not query.exec():
            log.w(f"Не удалось проверить количество столбцов в таблице payment. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) != self.PAYMENT_TABLE_COLUMNUM:
            log.w(f"Количество столбцов в таблице payment ({query.value(0)}) не соответствует ожидаемому ({self.PAYMENT_TABLE_COLUMNUM}).")
            self.db.close()
            return False
        self.db.close()
        return True

    def open_db_connection(self) -> bool:
        db_path: str = os.path.abspath(self.DEFAULT_DB_RELPATH)
        self.db.setDatabaseName(db_path)
        if not self.db.open():
            log.c(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {db_path}")
            return False
        return True

    def is_db_connected(self) -> bool:
        return self.db.isOpen()

    def switch_db_files(self, new_file_path: str = "", close_current_connection: bool = False) -> bool:
        if close_current_connection:
            db = QSqlDatabase.database()
            connection_name = db.connectionName()
            db.close()
            del db
            QSqlDatabase.removeDatabase(connection_name)
        try:
            Path(os.path.abspath(self.DEFAULT_DB_RELPATH)).parent.mkdir(parents=True, exist_ok=True)
            Path(os.path.abspath(self.DEFAULT_DB_RELPATH)).unlink(missing_ok=True)
            shutil.copy(new_file_path, os.path.abspath(self.DEFAULT_DB_RELPATH))
            return True
        except FileNotFoundError:
            log.w(f"Файл {new_file_path} не найден")
        except Exception as e:
            log.x(f"При замене файла БД произошла ошибка: {e}")
        return False

    def load_fulfillmentdata_from_db(self, begin_date: QDate, end_date: QDate) -> list | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT * FROM fulfillmentdata WHERE startdate = ? AND enddate = ?")
        query.addBindValue(date_str(begin_date))
        query.addBindValue(date_str(end_date))
        if not query.exec():
            return None
        query.next()
        return [query.value(2), query.value(3), query.value(4), query.value(5), query.value(6)] if query.value(0) else None

    def save_fulfillmentdata_to_db(self, begin_date: QDate, end_date: QDate, values: list) -> None:
        if not self.is_db_connected():
            return
        query = QSqlQuery()
        query.prepare("INSERT OR REPLACE INTO fulfillmentdata VALUES(?, ?, ?, ?, ?, ?, ?)")
        query.addBindValue(date_str(begin_date))
        query.addBindValue(date_str(end_date))
        for value in values:
            query.addBindValue(value)
        if not query.exec():
            log.c(f"Не удалось сохранить данные в таблицу fulfillmentdata: {query.lastError().text()}")
        return

    def load_finplan_from_db(self, year: int, finplan_structure: dict) -> dict | None:
        if not self.is_db_connected():
            return None
        # Создаем базовый словарь для заполнения, оставляя только самостоятельные категории
        finplan_structure_copy = finplan_structure.copy()
        for key, value in list(finplan_structure_copy.items()):
            if value[0]:
                finplan_structure_copy.pop(key)
        values: dict = dict.fromkeys(finplan_structure_copy, None)

        query = QSqlQuery()
        query.prepare("SELECT * FROM finplan WHERE year = ?")
        query.addBindValue(year)
        if not query.exec():
            log.c(f"Не удалось выполнить запрос для таблицы finplan. Ошибка: {query.lastError().text()}")
            return None
        results_available: bool = False
        while query.next():
            results_available = True
            category: int = int(query.value(1))
            try:
                plan_values = [query.value(2), query.value(3), query.value(4), query.value(5), query.value(6), query.value(7), query.value(8), query.value(9),
                               query.value(10), query.value(11), query.value(12), query.value(13)]
                values[category] = [None if x == "" else x for x in plan_values]
            except KeyError:
                log.w(f"В словаре финансового плана не найдена категория {category}, полученная из базы данных")
                continue
        # На случай, если данные по указанному году ранее не задавались
        if not results_available:
            for key in values.keys():
                values[key] = [0] * 12
        return values

    def save_finplan_to_db(self, year: int, finplan_structure: dict, finplanmodel: FinPlanTableModel):
        if not self.is_db_connected():
            log.w("Отсутствует соединение с базой данных")
            return False
        query = QSqlQuery()
        query.prepare("DELETE FROM finplan WHERE year = ?")
        query.addBindValue(year)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке удалить данные из таблицы finplan: {query.lastError().text()}")
            return False
        for category in finplan_structure.keys():
            query.prepare("INSERT INTO finplan VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
            query.addBindValue(year)
            query.addBindValue(category)
            for month in range(1, 13):
                value = finplanmodel.index(finplanmodel.categories.index(category), month).data(FinPlanTableModel.internalValueRole)
                value = None if value == "" else value
                query.addBindValue(value)
            if not query.exec():
                log.w(f"Ошибка SQL при попытке внести данные в таблицу finplan: {query.lastError().text()}")
                return False
        return True

    def load_fulfillmentpayments_from_db(self, start_date: QDate, end_date: QDate) -> None | list:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT E.category, P.sum, P.paymentdate, E.receiver, E.name, E.subcategory, E.nds FROM payment AS P "
                          f"INNER JOIN event AS E ON P.eventid = E.id "
                          f"WHERE P.paymentdate BETWEEN \'{date_str(start_date)}\' AND \'{date_str(end_date)}\' "
                          f"ORDER BY E.category ASC, CAST(P.sum AS decimal) DESC")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке загрузить платежи для таблицы исполнения плана: {query.lastError().text()}")
            return None
        values: list = []
        while query.next():
            values.append([query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5), query.value(6)])
        return values

    def load_fulfillmentplanvalues_from_db(self, year: int, start_month: int, end_month: int) -> None | dict:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT category, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12 FROM finplan WHERE year = {year}")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы finplan: {query.lastError().text()}")
            return None
        values: dict = {}
        while query.next():
            category = int(query.value(0))
            plan_values = [None if query.value(n) == '' else query.value(n) for n in range(start_month, end_month + 1)]
            values[category] = sum(x or 0 for x in plan_values) if not all(x is None for x in plan_values) else None
        return values if values else None

    def check_fees_paid_fordate(self, fee_date: QDate, liability_category: int) -> Decimal | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT totalamount FROM event WHERE category = {liability_category} AND duedate = '{date_str(fee_date)}' AND name LIKE '[A]%'")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные об оплаченных комиссиях из таблицы event: {query.lastError().text()}")
            return None
        if query.next():
            return Decimal(query.value(0))
        else:
            return Decimal("NaN")

    def load_departments(self) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name FROM department ORDER BY id")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить список подразделений: {query.lastError().text()}")
            return None
        result = []
        while query.next():
            result.append((int(query.value(0)), query.value(1)))
        return result

    def load_positions(self, as_dict: bool = False):
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, department, name FROM position ORDER BY department, name")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить список должностей: {query.lastError().text()}")
            return None
        values: dict | list = {} if as_dict else []
        while query.next():
            pos_id, dept_id, name = int(query.value(0)), int(query.value(1)), query.value(2)
            if as_dict:
                values[pos_id] = (dept_id, name)
            else:
                values.append([pos_id, dept_id, name])
        return values

    def add_position(self, department: int, name: str) -> int | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("INSERT INTO position(department, name) VALUES (?, ?)")
        query.addBindValue(department)
        query.addBindValue(name)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке создания новой должности: {query.lastError().text()}")
            return None
        return int(query.lastInsertId())

    def rename_position(self, position_id: int, name: str) -> bool:
        if not self.is_db_connected():
            return False
        query = QSqlQuery()
        query.prepare("UPDATE position SET name = ? WHERE id = ?")
        query.addBindValue(name)
        query.addBindValue(position_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке переименования должности: {query.lastError().text()}")
            return False
        return True

    def delete_position(self, position_id: int) -> bool:
        if not self.is_db_connected():
            return False
        query = QSqlQuery()
        query.prepare("UPDATE personal SET position = NULL WHERE position = ?")
        query.addBindValue(position_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке очистки должности перед удалением: {query.lastError().text()}")
            return False
        query = QSqlQuery()
        query.prepare("DELETE FROM position WHERE id = ?")
        query.addBindValue(position_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке удаления должности: {query.lastError().text()}")
            return False
        return True

    def resolve_position_to_personal(self, position_id: int) -> int | None:
        """Возвращает id активного работника, занимающего указанную должность, либо None ('нет назначения')."""
        if not self.is_db_connected() or not position_id:
            return None
        query = QSqlQuery()
        query.prepare("SELECT id FROM personal WHERE position = ? AND archived = 0 LIMIT 1")
        query.addBindValue(position_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке разрешения должности в работника: {query.lastError().text()}")
            return None
        return int(query.value(0)) if query.next() else None

    def load_personal_data(self, as_dict: bool = False) -> tuple | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name, department, archived, position FROM personal")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные о персонале из таблицы personal: {query.lastError().text()}")
            return None
        values: dict | list = {} if as_dict else []
        while query.next():
            position = int(query.value(4)) if query.value(4) else 0
            if as_dict:
                values[query.value(0)] = (query.value(1), query.value(2), query.value(3), position)
            else:
                values.append([query.value(0), query.value(1), query.value(2), query.value(3), position])
            self.personal_data_max_id = int(query.value(0)) if int(
                query.value(0)) > self.personal_data_max_id else self.personal_data_max_id

        query = QSqlQuery(
            "SELECT category, responsible, COUNT(*) AS cnt FROM event WHERE responsible IN (SELECT id FROM personal) "
            "GROUP BY category, responsible ORDER BY category, responsible")
        if not query.exec():
            log.w(
                f"Ошибка SQL при попытке получить данные о частоте встречаемости персонала из таблицы event: {query.lastError().text()}")
            return None
        freq_dict = defaultdict(dict)
        while query.next():
            freq_dict[int(query.value(0))][int(query.value(1))] = query.value(2)

        return values, freq_dict, self.personal_data_max_id

    def save_personal_data(self, data: list) -> bool:
        if not self.is_db_connected():
            return False
        query: QSqlQuery = QSqlQuery()
        for entry in data:
            position_value = entry[4] if entry[4] else None
            if entry[0] <= self.personal_data_max_id:
                query.prepare("UPDATE personal SET name = ?, department = ?, archived = ?, position = ? WHERE id = ?")
                for val in [entry[1], entry[2], entry[3], position_value, entry[0]]:
                    query.addBindValue(val)
            else:
                query.prepare("INSERT INTO personal(id, name, department, archived, position) VALUES (?,?,?,?,?)")
                for val in [entry[0], entry[1], entry[2], entry[3], position_value]:
                    query.addBindValue(val)
            if not query.exec():
                log.w(f"Ошибка SQL при попытке сохранения записей в таблице personal: {query.lastError().text()}")
                return False
        return True

    def get_paymentsum_for_period(self, date_from: date, date_to: date) -> dict[date, list[Decimal]] | None:
        if not self.is_db_connected():
            return None
        query: QSqlQuery = QSqlQuery()
        query.prepare(
            "SELECT payment.paymentdate, payment.sum, "
            "COALESCE(event.name, ''), event.receiver "
            "FROM payment "
            "LEFT JOIN event ON event.id = payment.eventid "
            "WHERE payment.paymentdate BETWEEN ? AND ?"
        )
        query.addBindValue(date_from.isoformat())
        query.addBindValue(date_to.isoformat())
        if not query.exec():
            log.w(f"Не удалось получить перечень платежей за период с {date_from} по {date_to}: {query.lastError().text()}")
            return None

        by_date: dict[date, list[Decimal]] = {}

        while query.next():
            paymentdate = str_date(query.value(0), python_date=True)
            amount = str_decimal(query.value(1))
            descr = query.value(2) + f" ({query.value(3)})"
            by_date.setdefault(paymentdate, []).append((amount, descr))

        return by_date

    def load_column_values(self, column: str, as_set: bool = True) -> set | list | None:
        if not self.is_db_connected():
            return None
        results: list = []
        query: QSqlQuery = QSqlQuery(f"SELECT {column} FROM event WHERE type = 2")
        while query.next():
            results.append(query.value(0))
        return results if not as_set else set(results)

    def insert_filterflags(self):
        if not self.is_db_connected():
            return False
        current_date = QDate.currentDate()
        current_date_str = current_date.toString("yyyy-MM-dd")

        date_diff_sql = f"(julianday(duedate) - julianday('{current_date_str}'))"
        days_week = days_to_weekend(current_date)
        days_month = days_to_month(current_date)
        remain_num = "CAST(remainamount AS NUMERIC)"
        today_num = "CAST(todayshare AS NUMERIC)"

        sql_query = f"""
            UPDATE event 
            SET filterflags = CASE 
                -- Если тип строки не LIABILITY, сбрасываем флаг в NONE
                WHEN type != {RowType.LIABILITY.value} THEN {int(FilterFlags.NONE)}

                -- Если оплачено (remainamount <= 0 И todayshare == 0)
                WHEN {remain_num} <= 0 AND {today_num} = 0 THEN {int(FilterFlags.PAID)}

                -- Если НЕ оплачено, собираем битовую маску из NOTPAID + условий по датам
                ELSE {int(FilterFlags.NOTPAID)} 
                    + CASE WHEN {date_diff_sql} < 0 THEN {int(FilterFlags.DUE)} ELSE 0 END
                    + CASE WHEN {date_diff_sql} = 0 THEN {int(FilterFlags.TODAY)} ELSE 0 END
                    + CASE WHEN {date_diff_sql} > -1 AND {date_diff_sql} <= {days_week} THEN {int(FilterFlags.WEEK)} ELSE 0 END
                    + CASE WHEN {date_diff_sql} > -1 AND {date_diff_sql} <= {days_month} THEN {int(FilterFlags.MONTH)} ELSE 0 END
            END
            WHERE id IN (SELECT id FROM event) -- обновляет все записи, на которые не наложен filter()
            """
        query: QSqlQuery = QSqlQuery(sql_query)
        if not query.exec():
            return False
        return True

    def insert_manualcalculated_data(self) -> bool:
        if not self.is_db_connected():
            return False
        current_date = QDate.currentDate()
        query = QSqlQuery()
        if not query.exec("UPDATE event SET remainamount = event.totalamount, todayshare = '0.0', lastpaymentdate = ''"):
            return False
        query = QSqlQuery()
        query.prepare(f"UPDATE event "
                      f"SET remainamount = remain_amount, todayshare = today_share, lastpaymentdate = lastpayment_date "
                      f"FROM ("
                      f"SELECT event.id AS event_id, "
                      f"ROUND(CAST(event.totalamount AS REAL) - COALESCE(SUM(CAST(payment.sum AS REAL)), 0.0), 2) AS remain_amount, "
                      f"ROUND(SUM(CASE WHEN payment.paymentdate = '{date_str(current_date)}' THEN CAST(payment.sum AS REAL) ELSE 0.0 END), 2) AS today_share, "
                      f"MAX(payment.paymentdate) AS lastpayment_date "
                      f"FROM payment "
                      f"LEFT JOIN event ON event.id = payment.eventid "
                      f"GROUP BY event.id) "
                      f"WHERE id = event_id")
        if not query.exec():
            return False
        return True

    def load_contractors(self) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name FROM contractor")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы contractor: {query.lastError().text()}")
            return None
        contracors: list = []
        while query.next():
            contracors.append((query.value(0), query.value(1)))
        return contracors

    def add_contractor(self, contractor_name: str) -> int | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("INSERT INTO contractor (name) VALUES (?)")
        query.addBindValue(contractor_name)
        if not query.exec():
            return None
        return query.lastInsertId()

    def load_contracts(self, contractor_id: int) -> list[tuple[int, str, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT id, name, date FROM contract WHERE contractor_id = ?")
        query.addBindValue(contractor_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы contract: {query.lastError().text()}")
            return None
        contracts: list = []
        while query.next():
            contracts.append((query.value(0), query.value(1), query.value(2)))
        return contracts

    def add_contract(self, contractor_id: int, contract_name: str, contract_date: str) -> int | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("INSERT INTO contract (contractor_id, name, date) VALUES (?, ?, ?)")
        query.addBindValue(contractor_id)
        query.addBindValue(contract_name)
        query.addBindValue(contract_date)
        if not query.exec():
            return None
        return query.lastInsertId()

    def load_documents(self, contract_id: int) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT id, document_name FROM contractdocument WHERE contract_id = ?")
        query.addBindValue(contract_id)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы contractdocument: {query.lastError().text()}")
            return None
        documents: list = []
        while query.next():
            documents.append((query.value(0), query.value(1)))
        return documents

    def load_documenttypes(self) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name FROM contractdocumenttype")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы contractdocumenttype: {query.lastError().text()}")
            return None
        documenttypes: list = []
        while query.next():
            documenttypes.append((query.value(0), query.value(1)))
        return documenttypes

    def load_document_data(self, document_id: int) -> Optional[ContractDocumentData]:

        @staticmethod
        def _val(query: QSqlQuery, index: int):
            v = query.value(index)
            return None if v is None or v == "" else v

        @staticmethod
        def _int_or_none(value) -> Optional[int]:
            return None if value is None or value == "" else int(value)

        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT d.id, c.contractor_id, ctr.name, d.contract_id, c.name, c.date, d.document_type, "
                      "d.position_id, d.document_name, d.description, t.payment_type, t.days_count, t.days_type, "
                      "t.has_calendar_condition, t.month_day, t.month_type "
                      "FROM contractdocument d "
                      "JOIN contract c ON c.id = d.contract_id "
                      "LEFT JOIN contractor ctr ON ctr.id = c.contractor_id "
                      "LEFT JOIN contractpaymentterm t ON t.document_id = d.id "
                      "WHERE d.id = :id")
        query.bindValue(":id", document_id)
        if not query.exec() or not query.next():
            log.w(f"Ошибка SQL при попытке получить данные для создания ContractDocumentData {query.lastError().text()}")
            return None

        v = [_val(query, i) for i in range(16)]

        payment_type = self._enum_from_db(PaymentDueType, v[10])
        if payment_type is None:
            log.w(f"Для документа {document_id} не заданы условия оплаты (нет записи в contractpaymentterm)")
            return None

        return ContractDocumentData(
            document_id=int(v[0]),
            contractor_id=int(v[1] or 0),
            contractor_name=v[2] or "",
            contract_id=int(v[3]),
            contract_number=v[4] or "",
            contract_date=QDate.fromString(v[5] or "", self.DATE_FORMAT),
            document_type=int(v[6] or 0),
            position_id=int(v[7] or 0),
            document_name=v[8] or "",
            description=v[9] or "",
            payment_type=payment_type,
            days_count=int(v[11] or 0),
            days_type=self._enum_from_db(DaysType, v[12]),
            has_calendar_condition=bool(int(v[13] or 0)),
            month_day=_int_or_none(v[14]),
            month_type=self._enum_from_db(MonthType, v[15]),
        )

    def save_document_data(self, data: ContractDocumentData) -> Optional[int]:
        if not self.is_db_connected():
            return None

        if not self.db.transaction():
            log.e(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            msg_box = ErrorInfoMessageBox("Не удалось установить связь с базой данных")
            msg_box.exec()
            return None

        position_id = data.position_id if data.position_id else None
        is_new = not data.document_id or data.document_id <= 0

        query = QSqlQuery()
        if is_new:
            query.prepare("""
                INSERT INTO contractdocument
                    (contract_id, document_type, document_name, description, position_id)
                VALUES
                    (:contract_id, :document_type, :document_name, :description, :position_id)
            """)
        else:
            query.prepare("""
                UPDATE contractdocument SET
                    contract_id   = :contract_id,
                    document_type = :document_type,
                    document_name = :document_name,
                    description   = :description,
                    position_id   = :position_id
                WHERE id = :id
            """)
            query.bindValue(":id", data.document_id)

        query.bindValue(":contract_id", data.contract_id)
        query.bindValue(":document_type", data.document_type)
        query.bindValue(":document_name", data.document_name)
        query.bindValue(":description", data.description)
        query.bindValue(":position_id", position_id)

        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить записать данные ContractDocumentData {query.lastError().text()}")
            return None

        if is_new:
            data.document_id = int(query.lastInsertId())
        elif query.numRowsAffected() == 0:
            self.db.rollback()
            log.w(f"Ошибка SQL при попытке получить записать данные ContractDocumentData {query.lastError().text()}")
            return None

        query = QSqlQuery()
        query.prepare("""
            INSERT INTO contractpaymentterm
                (document_id, payment_type, days_count, days_type,
                 has_calendar_condition, month_day, month_type)
            VALUES
                (:document_id, :payment_type, :days_count, :days_type,
                 :has_calendar_condition, :month_day, :month_type)
            ON CONFLICT(document_id) DO UPDATE SET
                payment_type           = excluded.payment_type,
                days_count             = excluded.days_count,
                days_type              = excluded.days_type,
                has_calendar_condition = excluded.has_calendar_condition,
                month_day              = excluded.month_day,
                month_type             = excluded.month_type
        """)
        query.bindValue(":document_id", data.document_id)
        query.bindValue(":payment_type", self._enum_to_db(data.payment_type))
        query.bindValue(":days_count", data.days_count or 0)
        query.bindValue(":days_type", self._enum_to_db(data.days_type))
        query.bindValue(":has_calendar_condition", 1 if data.has_calendar_condition else 0)
        query.bindValue(":month_day", data.month_day)
        query.bindValue(":month_type", self._enum_to_db(data.month_type))

        if not query.exec():
            self.db.rollback()
            log.w(f"Ошибка SQL при попытке получить записать данные ContractDocumentData {query.lastError().text()}")
            return None

        if not self.db.commit():
            log.e(f"Не удалось завершить транзакцию: {self.db.lastError().text()}")
            msg_box = ErrorInfoMessageBox("Не удалось установить связь с базой данных")
            msg_box.exec()
            return None
        return data.document_id

