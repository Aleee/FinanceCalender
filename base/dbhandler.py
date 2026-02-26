import os
import shutil
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import lovely_logger as log

from base.casting import str_int
from base.event import Event, term_filter_flags, RowType, TermRoleFlags
from base.date import str_date, date_str, date_displstr
from base.payment import Payment
from gui.finplanmodel import FinPlanTableModel
from gui.settings import SettingsHandler


class DBHandler:

    DEFAULT_DB_RELPATH = "db/db.db"
    EVENT_TABLE_COLUMNUM = 14
    PAYMENT_TABLE_COLUMNUM = 5

    def __init__(self, settings_handler):
        self.settings_handler = settings_handler
        self.db: QSqlDatabase = QSqlDatabase.addDatabase("QSQLITE")

    def check_if_db_files_exists(self) -> bool:
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
        query = QSqlQuery("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='event_temp'")
        if not query.exec():
            log.w(f"Не удалось проверить наличие таблицы event_temp. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) == 1:
            log.w(f"При инициализации обнаружена таблица event_temp. Возможно, предыдущее сохранение было завершено некорректно.")
            query = QSqlQuery("DROP TABLE event_temp")
            query.exec()
        query = QSqlQuery("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='payment_temp'")
        if not query.exec():
            log.w(f"Не удалось проверить наличие таблицы payment_temp. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) == 1:
            log.w(f"При инициализации обнаружена таблица payment_temp. Возможно, предыдущее сохранение было завершено некорректно. Таблица будет удалена.")
            query = QSqlQuery("DROP TABLE payment_temp")
            query.exec()


        self.db.close()
        return True

    def open_db_connection(self) -> bool:
        db_path: str = os.path.abspath(self.DEFAULT_DB_RELPATH)
        self.db.setDatabaseName(db_path)
        if not self.db.open():
            log.c(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {db_path}")
            return False
        return True

    def switch_db_files(self, new_file_path: str = "", close_current_connection: bool = False) -> bool:
        if close_current_connection:
            QSqlDatabase.database().close()
        try:
            Path(os.path.abspath(self.DEFAULT_DB_RELPATH)).unlink(missing_ok=True)
            shutil.copy(new_file_path, os.path.abspath(self.DEFAULT_DB_RELPATH))
            return True
        except FileNotFoundError:
            log.w(f"Файл {new_file_path} не найден")
        except Exception as e:
            log.x(f"При замене файла БД произошла ошибка: {e}")
        return False

    @staticmethod
    def load_eventspayments_from_db() -> tuple[list[Event], list[Payment]] | bool:

        events: list = []
        payments: list = []

        #                          0      1                      2       3        4            5         6          7        8         9        10        11       12
        query = QSqlQuery("SELECT id, category, subcategory, receiver, name, totalamount, todayshare, duedate, createdate, descr, responsible, notes, paymenttype, nds FROM event")
        if not query.exec():
            log.c(f"Не удалось выполнить запрос для таблицы event. Ошибка: {query.lastError().text()}")
            return False
        try:
            while query.next():
                pquery = QSqlQuery()
                pquery.prepare("SELECT id, sum, paymentdate, createdate FROM payment WHERE eventid = ?")
                pquery.addBindValue(query.value(0))
                if not pquery.exec():
                    log.c(f"Не удалось выполнить запрос для таблицы payment. Ошибка: {pquery.lastError().text()}")
                    return False
                total_paid: Decimal = Decimal(0)
                last_payment_date: QDate = QDate()
                are_today_payments_present: bool = False
                while pquery.next():
                    # Проверка на сброс сегодняшней суммы: при отсутствии оплат на текущую дату столбец обнуляется
                    today_date_cutoff: QDate = QDate().currentDate()
                    date_paid: QDate = str_date(pquery.value(2))
                    if date_paid == today_date_cutoff:
                        are_today_payments_present = True
                    # Выбор наиболее поздней даты для last_payment_date
                    if not last_payment_date.isValid() or date_paid > last_payment_date:
                        last_payment_date = date_paid
                    # Накопленная сумма платежей
                    sum_paid: Decimal = Decimal(pquery.value(1))
                    total_paid += sum_paid

                    payments.append(Payment(int(pquery.value(0)), int(query.value(0)), date_paid, sum_paid, str_date(pquery.value(3))))

                total_amount: Decimal = Decimal(query.value(5))
                remainamount: Decimal = total_amount - total_paid
                percentage: float = float(total_paid / total_amount)
                duedate: QDate = str_date(query.value(7))
                today_share: Decimal = Decimal(query.value(6))
                if today_share != 0 and not are_today_payments_present:
                    today_share = Decimal(0)
                if not duedate.isValid():
                    continue
                termflags: TermRoleFlags = term_filter_flags(remainamount, duedate, are_today_payments_present)

                #                         0         1           2                   3                    4                  5               6            7
                events.append(Event(query.value(3), 2, int(query.value(0)), int(query.value(1)), int(query.value(2)), query.value(4), remainamount, total_amount,
                                    #   8         9              10                  11                       12              13              14           15
                                    percentage, duedate, int(query.value(12)), str_date(query.value(8)), query.value(9), query.value(10), today_share, termflags,
                                    #      16                17                    18
                                    query.value(11), last_payment_date, int(query.value(13))))
        except TypeError as e:
            log.x(f"Некоторые данные из базы данных не смогли быть преобразованы при загрузке\n{str(e)}")
            QSqlDatabase.database().close()
            raise TypeError

        QSqlDatabase.database().close()
        return events, payments

    def save_eventspayments_to_db(self, event_model, payment_model) -> bool:
        if not self.open_db_connection():
            log.w("Не удалось открыть соединение с базой данных при попытке сохранения")
            return False

        query = QSqlQuery()

        def restore(tables: int = 0, delete_copies: bool = True):
            query = QSqlQuery()
            if not tables or tables == 1:
                query.exec("DELETE TABLE event")
                query.exec("CREATE TABLE event AS SELECT * FROM event_temp")
                if delete_copies:
                    query.exec("DELETE TABLE event")
            if not tables or tables == 2:
                query.exec("DELETE TABLE payment")
                query.exec("CREATE TABLE payment AS SELECT * FROM payment_temp")
                if delete_copies:
                    query.exec("DELETE TABLE payment")
            QSqlDatabase.database().close()

        # Резервные таблицы
        if not query.exec("CREATE TABLE event_temp AS SELECT * FROM event"):
            log.w(f"Ошибка SQL при попытке создать event_temp: {query.lastError().text()}")
            QSqlDatabase.database().close()
            return False
        if not query.exec("CREATE TABLE payment_temp AS SELECT * FROM payment"):
            log.w(f"Ошибка SQL при попытке создать payment_temp: {query.lastError().text()}")
            QSqlDatabase.database().close()
            if not query.exec("DELETE TABLE event_temp"):
                log.w(f"Ошибка SQL при попытке удалить event_temp после ошибки при создании payment_temp: {query.lastError().text()}")
                QSqlDatabase.database().close()
            return False

        # Удаление текущих данных
        if not query.exec("DELETE FROM event"):
            log.w(f"Ошибка SQL при попытке удаления данных из event: {query.lastError().text()}")
            return False
        if not query.exec("DELETE FROM payment"):
            log.w(f"Ошибка SQL при попытке удаления данных из payment: {query.lastError().text()}")
            restore(tables=1, delete_copies=True)
            return False

        # Заполнение новыми данными
        for payment in payment_model.payment_list:
            query.prepare("INSERT INTO payment VALUES (?, ?, ?, ?, ?)")
            query.addBindValue(payment.payment_id)
            query.addBindValue(payment.event_id)
            query.addBindValue(float(payment.payment_sum))
            query.addBindValue(date_str(payment.payment_date))
            query.addBindValue(date_str(payment.create_date))
            if not query.exec():
                log.w(f"Ошибка SQL при попытке заполнения таблицы payment: {query.lastError().text()}")
                restore(tables=2)
                return False

        for event in event_model.event_list:
            if event.type != RowType.EVENT:
                continue
            query.prepare("INSERT INTO event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
            query.addBindValue(event.id)
            query.addBindValue(event.category)
            query.addBindValue(event.subcategory)
            query.addBindValue(event.receiver)
            query.addBindValue(event.name)
            query.addBindValue(float(event.totalamount))
            query.addBindValue(float(event.todayshare))
            query.addBindValue(date_str(event.duedate))
            query.addBindValue(date_str(event.createdate))
            query.addBindValue(event.descr)
            query.addBindValue(event.responsible)
            query.addBindValue(event.notes)
            query.addBindValue(event.paymenttype)
            query.addBindValue(event.nds)
            if not query.exec():
                log.w(f"Ошибка SQL при попытке заполнения таблицы event: {query.lastError().text()}")
                restore(tables=0)
                return False

        if not query.exec("DROP TABLE event_temp"):
            log.w(f"Ошибка SQL при попытке удаления event_temp: {query.lastError().text()}")
        if not query.exec("DROP TABLE payment_temp"):
            log.w(f"Ошибка SQL при попытке удаления payment_temp: {query.lastError().text()}")

        QSqlDatabase.database().close()
        return True

    def load_fulfillmentdata_from_db(self, begin_date: QDate, end_date: QDate) -> list | None:
        if not self.open_db_connection():
            return None
        query = QSqlQuery()
        query.prepare("SELECT * FROM fulfillmentdata WHERE startdate = ? AND enddate = ?")
        query.addBindValue(date_str(begin_date))
        query.addBindValue(date_str(end_date))
        if not query.exec():
            QSqlDatabase.database().close()
            return None
        query.next()
        QSqlDatabase.database().close()
        return [query.value(2), query.value(3), query.value(4), query.value(5), query.value(6)] if query.value(0) else None

    def save_fulfillmentdata_to_db(self, begin_date: QDate, end_date: QDate, values: list) -> None:
        if not self.open_db_connection():
            return
        query = QSqlQuery()
        query.prepare("INSERT OR REPLACE INTO fulfillmentdata VALUES(?, ?, ?, ?, ?, ?, ?)")
        query.addBindValue(date_str(begin_date))
        query.addBindValue(date_str(end_date))
        for value in values:
            query.addBindValue(value)
        if not query.exec():
            log.c(f"Не удалось сохранить данные в таблицу fulfillmentdata: {query.lastError().text()}")
        QSqlDatabase.database().close()
        return

    def load_finplan_from_db(self, year: int, finplan_structure: dict) -> dict | None:
        if not self.open_db_connection():
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
            QSqlDatabase.database().close()
            return None
        results_available: bool = False
        while query.next():
            results_available = True
            category: int = int(query.value(1))
            try:
                values[category] = [query.value(2), query.value(3), query.value(4), query.value(5), query.value(6), query.value(7), query.value(8), query.value(9),
                                    query.value(10), query.value(11), query.value(12), query.value(13)]
            except KeyError:
                log.w(f"В словаре финансового плана не найдена категория {category}, полученная из базы данных")
                continue
        # На случай, если данные по указанному году ранее не задавались
        if not results_available:
            for key in values.keys():
                values[key] = [0] * 12

        QSqlDatabase.database().close()
        return values

    def save_finplan_to_db(self, year: int, finplan_structure: dict, finplanmodel: FinPlanTableModel):
        if not self.open_db_connection():
            log.w("Не удалось открыть соединение с базой данных при попытке сохранения")
            return False
        query = QSqlQuery()
        query.prepare("DELETE FROM finplan WHERE year = ?")
        query.addBindValue(year)
        if not query.exec():
            log.w(f"Ошибка SQL при попытке удалить данные из таблицы finplan: {query.lastError().text()}")
            QSqlDatabase.database().close()
            return False
        for category in finplan_structure.keys():
            query.prepare("INSERT INTO finplan VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
            query.addBindValue(year)
            query.addBindValue(category)
            for month in range(1, 13):
                value = finplanmodel.index(finplanmodel.categories.index(category), month).data()
                value = 0 if value == "" else value
                query.addBindValue(value)
            if not query.exec():
                log.w(f"Ошибка SQL при попытке внести данные в таблицу finplan: {query.lastError().text()}")
                QSqlDatabase.database().close()
                return False
        return True

    def load_fulfillmentpayments_from_db(self, start_date: QDate, end_date: QDate) -> None | list:
        if not self.open_db_connection():
            return None
        query = QSqlQuery(f"SELECT E.category, P.sum, P.paymentdate, E.receiver, E.name, E.subcategory FROM payment AS P "
                          f"INNER JOIN event AS E ON P.eventid = E.id "
                          f"WHERE P.paymentdate BETWEEN \'{date_str(start_date)}\' AND \'{date_str(end_date)}\' "
                          f"ORDER BY E.category ASC, CAST(P.sum AS decimal) DESC")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке загрузить платежи для таблицы исполнения плана: {query.lastError().text()}")
            QSqlDatabase.database().close()
            return None
        values = []
        while query.next():
            values.append([query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5)])
        return values

    def load_fulfillmentplanvalues_from_db(self, year: int, start_month: int, end_month: int) -> None | dict:
        if not self.open_db_connection():
            return None
        query = QSqlQuery(f"SELECT category, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12 FROM finplan WHERE year = {year}")
        if not query.exec():
            log.w(f"Ошибка SQL при попытке получить данные из таблицы finplan: {query.lastError().text()}")
            QSqlDatabase.database().close()
            return None
        values = {}
        while query.next():
            category = int(query.value(0))
            values[category] = sum([query.value(n) for n in range(start_month, end_month + 1)])
        return values if values else None
