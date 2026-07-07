import os
import shutil
from collections import defaultdict
from decimal import Decimal
from idlelib import query
from pathlib import Path
from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import lovely_logger as log

from base.casting import str_int
from base.date import str_date, date_str, date_displstr, days_to_weekend, days_to_month
from base.liability import LiabilityCategory, FilterFlags, RowType
from base.payment import Payment
from gui.finplanmodel import FinPlanTableModel


class DBHandler:

    DB_VERSION: int = 1
    DEFAULT_DB_RELPATH: str = "db/db.db"
    EVENT_TABLE_COLUMNUM: int = 21
    PAYMENT_TABLE_COLUMNUM: int = 5

    def __init__(self, settings_handler):
        self.settings_handler = settings_handler
        self.db: QSqlDatabase = QSqlDatabase.addDatabase("QSQLITE")

        self.personal_data_max_id: int = 0

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

    def check_fees_paid_fordate(self, fee_date: QDate) -> Decimal | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT totalamount FROM event WHERE category = {LiabilityCategory.COMMISSION} AND duedate = '{date_str(fee_date)}' AND name LIKE '[A]%'")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные об оплаченных комиссиях из таблицы event: {query.lastError().text()}")
            return None
        if query.next():
            return Decimal(query.value(0))
        else:
            return Decimal("NaN")

    def load_personal_data(self, as_dict: bool = False) -> tuple | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name, department, archived FROM personal")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные о персонале из таблицы personal: {query.lastError().text()}")
            return None
        if as_dict:
            values: dict = {}
        else:
            values: list = []
        while query.next():
            if as_dict:
                values[query.value(0)] = (query.value(1), query.value(2), query.value(3))
            else:
                values.append([query.value(0), query.value(1), query.value(2), query.value(3)])
            self.personal_data_max_id = int(query.value(0)) if int(query.value(0)) > self.personal_data_max_id else self.personal_data_max_id

        query = QSqlQuery("SELECT category, responsible, COUNT(*) AS cnt FROM event WHERE responsible IN (SELECT id FROM personal) "
                          "GROUP BY category, responsible ORDER BY category, responsible")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные о частоте встречаемости персонала из таблицы event: {query.lastError().text()}")
            return None
        freq_dict = defaultdict(dict)
        while query.next():
            category = int(query.value(0))
            id = int(query.value(1))
            count = query.value(2)
            freq_dict[category][id] = count

        return values, freq_dict, self.personal_data_max_id

    def save_personal_data(self, data: list) -> bool:
        if not self.is_db_connected():
            return False
        query: QSqlQuery = QSqlQuery()
        for entry in data:
            if entry[0] <= self.personal_data_max_id:
                query.prepare("UPDATE personal SET name = ?, department = ?, archived = ? WHERE id = ?")
                for val in [entry[1], entry[2], entry[3], entry[0]]:
                    query.addBindValue(val)
                if not query.exec():
                    log.w(f"Ошибка SQL при попытке обновления имеющихся записей в таблице personal: {query.lastError().text()}")
                    return False
            else:
                query.prepare("INSERT INTO personal(id, name, department, archived) VALUES (?,?,?,?)")
                for val in [entry[0], entry[1], entry[2], entry[3]]:
                    query.addBindValue(val)
                if not query.exec():
                    log.w(f"Ошибка SQL при попытке создания новых записей в таблице personal: {query.lastError().text()}")
                    return False
        return True

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

    def insert_manualcalculated_data(self):
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
