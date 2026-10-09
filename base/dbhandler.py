import shutil
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from pathlib import Path
from datetime import date
from typing import Any, Callable, Optional
from uuid import uuid4

from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import lovely_logger as log

from base.date import str_date, date_str, date_displstr
from base.formatting import str_decimal
from base.liability import LiabilityCategory, RowType
from base.migrations import MIGRATIONS, MigrationError, INCREASE_CHANGE_COUNTER
from base.paths import db_path, backup_dir
from base.payment import Payment
from base.workcalendar import clear_calendar_cache
from base.version import DB_VERSION as _DB_VERSION
from base.contract import PaymentDueType, DaysType, MonthType, ContractDocumentData, DocumentTitle, SavedContractValues
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.finplanmodel import FinPlanTableModel


class DBHandler:

    DB_VERSION: int = _DB_VERSION
    EVENT_TABLE_COLUMNUM: int = 18
    PAYMENT_TABLE_COLUMNUM: int = 5

    DATE_FORMAT = "yyyy-MM-dd"

    def __init__(self, settings_handler):
        self.settings_handler = settings_handler
        self.db: QSqlDatabase = QSqlDatabase.addDatabase("QSQLITE")

        self.personal_data_max_id: int = 0
        self.after_commit_actions: list[Callable[[], None]] = []
        self.migration_failed: bool = False

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
        if not Path(db_path()).is_file():
            log.e(f"Не удалось открыть базу данных по стандартному пути (файла не существует): {db_path()}")
            return False
        return True

    def get_db_version(self) -> int | None:
        query = QSqlQuery("SELECT value FROM meta WHERE key = 'db_version'")
        if not query.exec():
            log.e(f"Не удалось проверить версию базы данных. Ошибка: {query.lastError().text()}")
            self.db.close()
            return None
        try:
            query.next()
            version = int(query.value(0))
        except (ValueError, TypeError) as e:
            log.e(f"Недопустимное значение версии базы данных. Ошибка: {e}")
            self.db.close()
            return None
        return version

    def is_db_newer_than_client(self) -> bool:
        self.db.setDatabaseName(db_path())
        if not self.db.open():
            return False
        version = self.get_db_version()
        self.db.close()
        return version is not None and version > self.DB_VERSION

    def check_db_file_integrity(self, alternative_path: str = "") -> bool:
        checked_path: str = alternative_path if alternative_path else db_path()
        self.db.setDatabaseName(checked_path)
        if not self.db.open():
            log.e(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {checked_path}")
            return False
        version = self.get_db_version()
        if version != self.DB_VERSION:
            log.e(f"Версия базы данных не соответствует версии клиента (загружаемая: {version}, требуемая: {self.DB_VERSION})")
            self.db.close()
            return False
        query = QSqlQuery("SELECT COUNT(*) FROM pragma_table_info('event')")
        if not query.exec():
            log.e(f"Не удалось проверить количество столбцов в таблице event. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) != self.EVENT_TABLE_COLUMNUM:
            log.e(f"Количество столбцов в таблице event ({query.value(0)}) не соответствует ожидаемому ({self.EVENT_TABLE_COLUMNUM}).")
            self.db.close()
            return False
        query = QSqlQuery("SELECT COUNT(*) FROM pragma_table_info('payment')")
        if not query.exec():
            log.e(f"Не удалось проверить количество столбцов в таблице payment. Ошибка: {query.lastError().text()}")
            self.db.close()
            return False
        query.next()
        if query.value(0) != self.PAYMENT_TABLE_COLUMNUM:
            log.e(f"Количество столбцов в таблице payment ({query.value(0)}) не соответствует ожидаемому ({self.PAYMENT_TABLE_COLUMNUM}).")
            self.db.close()
            return False
        self.db.close()
        return True

    def migrate_db(self, alternative_path: str = "") -> bool:
        migrated_path: str = alternative_path if alternative_path else db_path()
        self.after_commit_actions.clear()
        self.migration_failed = False
        self.db.setDatabaseName(migrated_path)
        if not self.db.open():
            log.e(f"Не удалось открыть базу данных для обновления структуры: {migrated_path}")
            return False
        version = self.get_db_version()
        if version is None:
            self.db.close()
            return False
        if version == self.DB_VERSION:
            self.db.close()
            return True
        if version > self.DB_VERSION:
            log.e(f"Версия базы данных ({version}) новее версии клиента ({self.DB_VERSION}), обновление структуры невозможно")
            self.db.close()
            return False
        self.migration_failed = True
        if not alternative_path and not self._save_pre_migration_copy(version):
            self.db.close()
            return False
        if not self.db.transaction():
            log.e(f"Не удалось начать транзакцию для обновления структуры базы данных: {self.db.lastError().text()}")
            self.db.close()
            return False
        try:
            for target_version in range(version + 1, self.DB_VERSION + 1):
                self._apply_migration(target_version)
            if not alternative_path and not self._increase_change_counter():
                raise MigrationError("Не удалось отметить изменение базы данных после обновления структуры")
            if not self.db.commit():
                raise MigrationError(f"Не удалось подтвердить транзакцию: {self.db.lastError().text()}")
        except Exception as e:
            log.x(f"Обновление структуры базы данных не удалось, изменения отменены: {e}")
            self.db.rollback()
            self.db.close()
            return False
        self.db.close()
        self.migration_failed = False
        log.i(f"Структура базы данных обновлена: версия {version} -> {self.DB_VERSION}")
        for action in self.after_commit_actions:
            try:
                action()
            except Exception as e:
                log.x(f"Не удалось выполнить действие после обновления структуры базы данных: {e}")
        return True

    def _apply_migration(self, target_version: int) -> None:
        steps = MIGRATIONS.get(target_version)
        if steps is None:
            raise MigrationError(f"Не описана миграция до версии {target_version}")
        for step in steps:
            if callable(step):
                step(self)
                continue
            query = QSqlQuery()
            if not query.exec(step):
                raise MigrationError(f"Ошибка SQL: {query.lastError().text()}. Запрос: {step}")
        if not self.set_setting("db_version", target_version):
            raise MigrationError(f"Не удалось записать версию базы данных {target_version}")

    def _increase_change_counter(self) -> bool:
        query = QSqlQuery()
        if not query.exec(INCREASE_CHANGE_COUNTER):
            log.e(f"Не удалось увеличить счётчик изменений базы данных: {query.lastError().text()}")
            return False
        return True

    def mark_db_changed(self, path: str) -> bool:
        self.db.setDatabaseName(path)
        if not self.db.open():
            log.e(f"Не удалось открыть базу данных, чтобы отметить изменение: {path}")
            return False
        marked = self._increase_change_counter()
        self.db.close()
        return marked

    @contextmanager
    def _file_connection(self, path: str):
        name = f"file_{uuid4().hex}"
        try:
            self._open_file_connection(name, path)
            yield name
        finally:
            self._close_file_connection(name)

    @staticmethod
    def _open_file_connection(name: str, path: str) -> None:
        connection = QSqlDatabase.addDatabase("QSQLITE", name)
        connection.setDatabaseName(path)
        opened = connection.open()
        error = connection.lastError().text()
        del connection
        if not opened:
            raise RuntimeError(f"Не удалось открыть базу данных {path}: {error}")

    @staticmethod
    def _close_file_connection(name: str) -> None:
        connection = QSqlDatabase.database(name, False)
        connection.close()
        del connection
        QSqlDatabase.removeDatabase(name)

    @staticmethod
    def _file_execute(connection_name: str, sql: str, *values: Any) -> list[list]:
        query = QSqlQuery(QSqlDatabase.database(connection_name, False))
        query.prepare(sql)
        for value in values:
            query.addBindValue(value)
        error = "" if query.exec() else query.lastError().text()
        rows: list[list] = []
        while not error and query.next():
            rows.append([query.value(i) for i in range(query.record().count())])
        query.finish()
        del query
        if error:
            raise RuntimeError(f"Ошибка SQL: {error}. Запрос: {sql}")
        return rows

    def read_file_settings(self, path: str, keys: tuple[str, ...]) -> dict[str, str | None] | None:
        try:
            with self._file_connection(path) as connection:
                values: dict[str, str | None] = {}
                for key in keys:
                    rows = self._file_execute(connection, "SELECT value FROM meta WHERE key = ?", key)
                    values[key] = str(rows[0][0]) if rows else None
                return values
        except Exception as e:
            log.x(f"Не удалось прочитать служебные ключи из файла {path}: {e}")
            return None

    def check_file_integrity(self, path: str) -> bool:
        try:
            with self._file_connection(path) as connection:
                return self._file_execute(connection, "PRAGMA integrity_check")[0][0] == "ok"
        except Exception as e:
            log.x(f"Не удалось проверить целостность файла {path}: {e}")
            return False

    def copy_db_file(self, target_path: str) -> bool:
        try:
            with self._file_connection(db_path()) as connection:
                self._file_execute(connection, "VACUUM INTO ?", target_path)
        except Exception as e:
            log.x(f"Не удалось сохранить копию базы данных в {target_path}: {e}")
            return False
        return True

    def create_sync_snapshot(self, snapshot_path: str, new_token: str) -> int | None:
        try:
            with self._file_connection(db_path()) as source:
                counter = int(self._file_execute(source, "SELECT value FROM meta WHERE key = 'change_counter'")[0][0])
                self._file_execute(source, "VACUUM INTO ?", snapshot_path)
            with self._file_connection(snapshot_path) as snapshot:
                self._file_execute(snapshot, "UPDATE meta SET value = ? WHERE key = 'sync_token'", new_token)
                self._file_execute(snapshot, "UPDATE meta SET value = '0' WHERE key = 'change_counter'")
                triggers = self._file_execute(snapshot, "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger'")[0][0]
                indexes = self._file_execute(snapshot, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'idx_meta_key'")[0][0]
                if triggers == 0 or indexes == 0:
                    raise RuntimeError("В снимке базы данных нет триггеров или индекса таблицы meta")
        except Exception as e:
            log.x(f"Не удалось создать снимок базы данных для синхронизации: {e}")
            return None
        return counter

    def finish_push(self, new_token: str, snapshot_counter: int) -> bool:
        if not self.db.transaction():
            log.e(f"Не удалось начать транзакцию после отправки: {self.db.lastError().text()}")
            return False
        query = QSqlQuery()
        query.prepare("UPDATE meta SET value = '0' WHERE key = 'change_counter' AND CAST(value AS INTEGER) = ?")
        query.addBindValue(snapshot_counter)
        if not (self.set_setting("sync_token", new_token) and query.exec() and self.db.commit()):
            log.e(f"Не удалось записать результат отправки в базу данных: {self.db.lastError().text()} {query.lastError().text()}")
            self.db.rollback()
            return False
        return True

    @staticmethod
    def _save_pre_migration_copy(version: int) -> bool:
        copy_path: Path = Path(backup_dir()) / f"before_migration_v{version}.db"
        try:
            shutil.copy(db_path(), copy_path)
        except OSError as e:
            log.x(f"Не удалось сохранить копию базы данных перед обновлением структуры: {e}")
            return False
        log.i(f"Копия базы данных перед обновлением структуры: {copy_path}")
        return True

    def make_migrated_copy(self, source_path: str) -> str | None:
        temp_path: Path = Path(db_path()).with_name("db_restore_temp.db")
        try:
            shutil.copy(source_path, temp_path)
        except OSError as e:
            log.x(f"Не удалось скопировать {source_path} во временный файл {temp_path}: {e}")
            return None
        if (self.migrate_db(str(temp_path)) and self.check_db_file_integrity(str(temp_path))
                and self.mark_db_changed(str(temp_path))):
            return str(temp_path)
        temp_path.unlink(missing_ok=True)
        return None

    def open_db_connection(self) -> bool:
        self.db.setDatabaseName(db_path())
        if not self.db.open():
            log.c(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {db_path()}")
            return False
        clear_calendar_cache()
        return True

    def get_setting(self, key: str, default: str | None = "") -> str | None:
        if not self.is_db_connected():
            return default
        query = QSqlQuery()
        query.prepare("SELECT value FROM meta WHERE key = ?")
        query.addBindValue(key)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке прочитать настройку {key} из таблицы meta: {query.lastError().text()}")
            return default
        if query.next() and not query.isNull(0):
            return str(query.value(0))
        return default

    def set_setting(self, key: str, value: Any) -> bool:
        if not self.is_db_connected():
            return False
        query = QSqlQuery()
        query.prepare("UPDATE meta SET value = ? WHERE key = ?")
        query.addBindValue(str(value))
        query.addBindValue(key)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке обновить настройку {key} в таблице meta: {query.lastError().text()}")
            return False
        if query.numRowsAffected() > 0:
            return True
        query.prepare("INSERT INTO meta (key, value) VALUES (?, ?)")
        query.addBindValue(key)
        query.addBindValue(str(value))
        if not query.exec():
            log.e(f"Ошибка SQL при попытке добавить настройку {key} в таблицу meta: {query.lastError().text()}")
            return False
        return True

    def is_db_connected(self) -> bool:
        return self.db.isOpen()

    def run_in_transaction(self, action: Callable[[], bool]) -> bool:
        if not self.db.transaction():
            log.e(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            return False
        try:
            succeeded: bool = action()
        except Exception as e:
            log.x(f"Ошибка внутри транзакции, изменения отменены: {e}")
            self.db.rollback()
            return False
        if succeeded and self.db.commit():
            return True
        log.e(f"Транзакция отменена: {self.db.lastError().text()}")
        self.db.rollback()
        return False

    def delete_payments_by_event(self, event_id: int) -> bool:
        query = QSqlQuery()
        query.prepare("DELETE FROM payment WHERE eventid = ?")
        query.addBindValue(event_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке удалить платежи обязательства {event_id}: {query.lastError().text()}")
            return False
        return True

    def switch_db_files(self, new_file_path: str = "", close_current_connection: bool = False) -> bool:
        if close_current_connection:
            self.db.close()
        try:
            Path(db_path()).unlink(missing_ok=True)
            shutil.copy(new_file_path, db_path())
            return True
        except FileNotFoundError:
            log.c(f"Файл {new_file_path} не найден, рабочая база данных {db_path()} могла быть удалена")
        except Exception as e:
            log.x(f"При замене файла БД произошла ошибка, рабочая база данных {db_path()} могла быть удалена: {e}")
        return False

    def load_fulfillmentdata_from_db(self, begin_date: QDate, end_date: QDate) -> list | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT * FROM fulfillmentdata WHERE startdate = ? AND enddate = ?")
        query.addBindValue(date_str(begin_date))
        query.addBindValue(date_str(end_date))
        if not query.exec():
            log.e(f"Ошибка SQL при попытке загрузить данные из таблицы fulfillmentdata: {query.lastError().text()}")
            return None
        if not query.next():
            return None
        return [query.value(2), query.value(3), query.value(4), query.value(5), query.value(6)]

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
            log.e(f"Не удалось сохранить данные в таблицу fulfillmentdata: {query.lastError().text()}")
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
            log.e(f"Не удалось выполнить запрос для таблицы finplan. Ошибка: {query.lastError().text()}")
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
        return self.run_in_transaction(lambda: self._write_finplan(year, finplan_structure, finplanmodel))

    def _write_finplan(self, year: int, finplan_structure: dict, finplanmodel: FinPlanTableModel) -> bool:
        query = QSqlQuery()
        query.prepare("DELETE FROM finplan WHERE year = ?")
        query.addBindValue(year)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке удалить данные из таблицы finplan: {query.lastError().text()}")
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
                log.e(f"Ошибка SQL при попытке внести данные в таблицу finplan: {query.lastError().text()}")
                return False
        return True

    def load_fulfillmentpayments_from_db(self, start_date: QDate, end_date: QDate) -> None | list:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT E.category, P.sum, P.paymentdate, E.receiver, E.name, E.subcategory, E.nds, E.hidden FROM payment AS P "
                          f"INNER JOIN event AS E ON P.eventid = E.id "
                          f"WHERE P.paymentdate BETWEEN \'{date_str(start_date)}\' AND \'{date_str(end_date)}\' "
                          f"ORDER BY E.category ASC, CAST(P.sum AS decimal) DESC")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке загрузить платежи для таблицы исполнения плана: {query.lastError().text()}")
            return None
        values: list = []
        while query.next():
            values.append([query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5), query.value(6), int(query.value(7) or 0)])
        return values

    def load_fulfillmentplanvalues_from_db(self, year: int, start_month: int, end_month: int) -> None | dict:
        if not self.is_db_connected():
            return None
        query = QSqlQuery(f"SELECT category, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12 FROM finplan WHERE year = {year}")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные из таблицы finplan: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить данные об оплаченных комиссиях из таблицы event: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить список подразделений: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить список должностей: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке создания новой должности: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке переименования должности: {query.lastError().text()}")
            return False
        return True

    def delete_position(self, position_id: int) -> bool:
        if not self.is_db_connected():
            return False
        return self.run_in_transaction(lambda: self._remove_position(position_id))

    def _remove_position(self, position_id: int) -> bool:
        query = QSqlQuery()
        query.prepare("UPDATE personal SET position = NULL WHERE position = ?")
        query.addBindValue(position_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке очистки должности перед удалением: {query.lastError().text()}")
            return False
        query = QSqlQuery()
        query.prepare("DELETE FROM position WHERE id = ?")
        query.addBindValue(position_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке удаления должности: {query.lastError().text()}")
            return False
        return True

    def resolve_position_to_personal(self, position_id: int) -> int | None:
        if not self.is_db_connected() or not position_id:
            return None
        query = QSqlQuery()
        query.prepare("SELECT id FROM personal WHERE position = ? AND archived = 0 LIMIT 1")
        query.addBindValue(position_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке разрешения должности в работника: {query.lastError().text()}")
            return None
        return int(query.value(0)) if query.next() else None

    def load_personal_data(self, as_dict: bool = False) -> tuple | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name, department, archived, position FROM personal")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные о персонале из таблицы personal: {query.lastError().text()}")
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
            log.e(
                f"Ошибка SQL при попытке получить данные о частоте встречаемости персонала из таблицы event: {query.lastError().text()}")
            return None
        freq_dict = defaultdict(dict)
        while query.next():
            freq_dict[int(query.value(0))][int(query.value(1))] = query.value(2)

        return values, freq_dict, self.personal_data_max_id

    def save_personal_data(self, data: list) -> bool:
        if not self.is_db_connected():
            return False
        return self.run_in_transaction(lambda: self._write_personal_data(data))

    def _write_personal_data(self, data: list) -> bool:
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
                log.e(f"Ошибка SQL при попытке сохранения записей в таблице personal: {query.lastError().text()}")
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
            log.e(f"Не удалось получить перечень платежей за период с {date_from} по {date_to}: {query.lastError().text()}")
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
        if query.lastError().isValid():
            log.e(f"Ошибка SQL при попытке получить значения столбца {column} из таблицы event: {query.lastError().text()}")
            return None
        while query.next():
            results.append(query.value(0))
        return results if not as_set else set(results)

    def load_payment_totals(self, current_date: QDate) -> dict[int, tuple[Decimal, Decimal, str]] | None:
        if not self.is_db_connected():
            return None
        cents = "CAST(ROUND(CAST(payment.sum AS REAL) * 100) AS INTEGER)"
        query = QSqlQuery()
        query.prepare(f"SELECT eventid, SUM({cents}), "
                      f"SUM(CASE WHEN paymentdate = ? THEN {cents} ELSE 0 END), "
                      f"MAX(paymentdate) "
                      f"FROM payment GROUP BY eventid")
        query.addBindValue(date_str(current_date))
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить итоги по платежам из таблицы payment: {query.lastError().text()}")
            return None
        totals: dict[int, tuple[Decimal, Decimal, str]] = {}
        while query.next():
            last_date = query.value(3)
            totals[query.value(0)] = (Decimal(query.value(1) or 0) / 100,
                                      Decimal(query.value(2) or 0) / 100,
                                      "" if self._is_null(last_date) else str(last_date))
        return totals

    @staticmethod
    def paid_load_filter(threshold: str) -> str:
        cents = "CAST(ROUND(CAST({}.{} AS REAL) * 100) AS INTEGER)"
        return ("event.id NOT IN (SELECT p.eventid FROM payment p JOIN event e ON e.id = p.eventid "
                "GROUP BY p.eventid "
                f"HAVING MAX(p.paymentdate) <= '{threshold}' "
                f"AND SUM({cents.format('p', 'sum')}) >= {cents.format('e', 'totalamount')})")

    def load_contractors(self) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name FROM contractor")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contractor: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contract: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contractdocument: {query.lastError().text()}")
            return None
        documents: list = []
        while query.next():
            documents.append((query.value(0), query.value(1)))
        return documents

    def load_document_titles(self) -> dict[int, DocumentTitle] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT d.id, c.contractor_id, ctr.name, d.contract_id, c.name, c.date, d.document_name "
                          "FROM contractdocument d "
                          "JOIN contract c ON c.id = d.contract_id "
                          "LEFT JOIN contractor ctr ON ctr.id = c.contractor_id")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить названия документов: {query.lastError().text()}")
            return None
        titles: dict[int, DocumentTitle] = {}
        while query.next():
            titles[int(query.value(0))] = DocumentTitle(
                document_id=int(query.value(0)),
                contractor_id=int(query.value(1) or 0),
                contractor_name=query.value(2) or "",
                contract_id=int(query.value(3)),
                contract_number=query.value(4) or "",
                contract_date=QDate.fromString(query.value(5) or "", self.DATE_FORMAT),
                document_name=query.value(6) or "",
            )
        return titles

    def load_documenttypes(self) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name FROM contractdocumenttype")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contractdocumenttype: {query.lastError().text()}")
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
            log.e(f"Ошибка SQL при попытке получить данные для создания ContractDocumentData {query.lastError().text()}")
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
            self.db.rollback()
            log.e(f"Ошибка SQL при попытке записать данные документа в таблицу contractdocument: {query.lastError().text()}")
            return None

        if is_new:
            data.document_id = int(query.lastInsertId())
        elif query.numRowsAffected() == 0:
            self.db.rollback()
            log.e(f"Не удалось обновить документ: запись contractdocument с id={data.document_id} не найдена")
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
            log.e(f"Ошибка SQL при попытке записать условия оплаты документа в таблицу contractpaymentterm: {query.lastError().text()}")
            return None

        if not self.db.commit():
            log.e(f"Не удалось завершить транзакцию: {self.db.lastError().text()}")
            msg_box = ErrorInfoMessageBox("Не удалось установить связь с базой данных")
            msg_box.exec()
            return None
        return data.document_id

    def _load_id_name_list(self, sql: str, params: tuple, err_msg: str) -> list[tuple[int, str]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare(sql)
        for p in params:
            query.addBindValue(p)
        if not query.exec():
            log.e(f"{err_msg}: {query.lastError().text()}")
            return None
        result = []
        while query.next():
            name = query.value(1)
            result.append((int(query.value(0)), "" if query.isNull(1) else str(name)))
        result.sort(key=lambda r: r[1].casefold())
        return result

    def load_contractors_for_combobox(self) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            "SELECT id, name FROM contractor", (),
            "Ошибка SQL при попытке получить список контрагентов")

    def load_contracts_for_combobox(self, contractor_id: int) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            "SELECT id, '№ ' || COALESCE(name, '') || CASE WHEN COALESCE(date, '') = '' THEN '' "
            "ELSE ' от ' || strftime('%d.%m.%Y', date) END FROM contract WHERE contractor_id = ?", (contractor_id,),
            "Ошибка SQL при попытке получить список договоров")

    def load_contract_documents_for_combobox(self, contract_id: int) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            "SELECT id, document_name FROM contractdocument WHERE contract_id = ?", (contract_id,),
            "Ошибка SQL при попытке получить список документов договора")

    def load_last_contract_id(self, contractor_id: int) -> int | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT lastcontractid FROM contractor WHERE id = ?")
        query.addBindValue(contractor_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить lastcontractid: {query.lastError().text()}")
            return None
        if query.next() and not query.isNull(0):
            return int(query.value(0))
        return None

    def save_last_contract_id(self, contractor_id: int, contract_id: int) -> bool:
        if not self.is_db_connected():
            return False
        query = QSqlQuery()
        query.prepare("UPDATE contractor SET lastcontractid = ? WHERE id = ?")
        query.addBindValue(contract_id)
        query.addBindValue(contractor_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке сохранить lastcontractid: {query.lastError().text()}")
            return False
        return True

    def load_document_parents(self, document_id: int) -> tuple[int, int] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT c.contractor_id, cd.contract_id FROM contractdocument cd JOIN contract c ON c.id = cd.contract_id WHERE cd.id = ?")
        query.addBindValue(document_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке найти договор и контрагента документа: {query.lastError().text()}")
            return None
        if query.next() and not query.isNull(0) and not query.isNull(1):
            return int(query.value(0)), int(query.value(1))
        return None

    def load_document_descriptions(self, document_id: int) -> list[str] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT descr FROM event WHERE type = ? AND contractdocument_id = ?")
        query.addBindValue(int(RowType.LIABILITY))
        query.addBindValue(document_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить основания платежей документа: {query.lastError().text()}")
            return None
        result = []
        while query.next():
            if not query.isNull(0):
                result.append(str(query.value(0)))
        return result

    def save_contractdocumentvalues(self, values_to_save: SavedContractValues) -> bool:
        if not self.is_db_connected():
            return False

        data_dict = asdict(values_to_save)
        pk_field = "contractdocumentid"
        other_fields = [field for field in data_dict.keys() if field != pk_field]

        update_assignments = ", ".join([f"{f} = excluded.{f}" for f in other_fields])
        fields_str = ", ".join(data_dict.keys())
        placeholders_str = ", ".join([f":{f}" for f in data_dict.keys()])

        sql = f"""
            INSERT INTO contractsavedvalues ({fields_str})
            VALUES ({placeholders_str})
            ON CONFLICT({pk_field}) DO UPDATE SET
                {update_assignments}
        """

        query = QSqlQuery()
        if not query.prepare(sql):
            log.e(f"Ошибка SQL при попытке подготовки запроса к таблице contractsavedvalues: {query.lastError().text()}")
            return False
        for key, value in data_dict.items():
            query.bindValue(f":{key}", value)
        if not query.exec():
            log.e(f"Ошибка SQL при выполнении запроса к таблице contractsavedvalues: {query.lastError().text()}")
            return False

        return True

    def load_contractdocumentvalues(self, document_id: int) -> Optional[SavedContractValues]:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT contractdocumentid, receiver, category, subcategory, name, nds, paymenttype, descr, responsible, hidden "
                      "FROM contractsavedvalues WHERE contractdocumentid = :id")
        query.bindValue(":id", document_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить сохраненные значения документа: {query.lastError().text()}")
            return None
        if not query.next():
            return None

        return SavedContractValues(
            contractdocumentid=int(query.value(0)),
            receiver=query.value(1) or "",
            category=int(query.value(2) or 0),
            subcategory=int(query.value(3) or 0),
            name=query.value(4) or "",
            nds=int(query.value(5) or 0),
            paymenttype=int(query.value(6) or 0),
            descr=query.value(7) or "",
            responsible=int(query.value(8) or 0),
            hidden=int(query.value(9) or 0))
