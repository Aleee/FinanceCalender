import shutil
import sqlite3
from collections import defaultdict
from contextlib import closing, contextmanager
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from pathlib import Path
from datetime import date
from platform import node
from typing import Any, Callable, Optional
from uuid import uuid4

from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import lovely_logger as log

from base.changelog import ChangeRecord
from base.date import str_date, date_str, date_displstr
from base.edition import is_viewer
from base.formatting import str_decimal
from base.liability import EVENT_COLUMN_NAMES, LiabilityCategory, RowType
from base.migrations import (MIGRATIONS, MigrationError, INCREASE_CHANGE_COUNTER, SERVICE_META_KEYS, CHANGELOG_TABLE,
                             CHANGELOG_DATA_TABLES, CHANGELOG_ACTIONS, CHANGELOG_AUTHOR_KEY, CHANGELOG_MACHINE_KEY,
                             changelog_triggers)
from base.paths import db_path, backup_dir
from base.payment import Payment, PaymentEntry, PaymentInfo
from base.syncdiff import (DbDiff, TableDiff, MergePlan, MergeWarnings, DETAILED_TABLES, KEY_COLUMNS, REFERENCES,
                           TABLE_DERIVED_COLUMNS, key_sql, table_key)
from base.workcalendar import clear_calendar_cache
from base.version import DB_VERSION as _DB_VERSION
from base.contract import PaymentDueType, DaysType, MonthType, ContractDocumentData, DocumentTitle, SavedContractValues
from base.contracthistory import ContractObligation, ContractPayment
from base.monthly import MonthlyEntry, MonthlyEvent, relative_term_text
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.finplanmodel import FinPlanTableModel


class DBHandler:

    DB_VERSION: int = _DB_VERSION
    ARCHIVE_MARK: str = "CASE WHEN archived = 0 THEN '' ELSE ' (архив)' END"
    EVENT_TABLE_COLUMNUM: int = 17
    PAYMENT_TABLE_COLUMNUM: int = 5
    CHANGELOG_KEEP_MONTHS: int = 6

    DATE_FORMAT = "yyyy-MM-dd"

    def __init__(self, settings_handler):
        self.settings_handler = settings_handler
        self.db: QSqlDatabase = QSqlDatabase.addDatabase("QSQLITE")

        self.personal_data_max_id: int = 0
        self.after_commit_actions: list[Callable[[], None]] = []
        self.migration_failed: bool = False
        self.db_busy: bool = False
        self.in_transaction: bool = False

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

    def _open_connection(self, path: str, read_only: bool = False) -> bool:
        self.db.setConnectOptions("QSQLITE_OPEN_READONLY" if read_only else "")
        self.db.setDatabaseName(path)
        return self.db.open()

    def check_db_files_exists(self) -> bool:
        if not Path(db_path()).is_file():
            log.e(f"Не удалось открыть базу данных по стандартному пути (файла не существует): {db_path()}")
            return False
        return True

    @staticmethod
    def _is_file_locked(path: str) -> bool:
        try:
            with closing(sqlite3.connect(path, timeout=0)) as connection:
                connection.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        except sqlite3.Error as e:
            return "locked" in str(e) or "busy" in str(e)
        return False

    def get_db_version(self) -> int | None:
        self.db_busy = False
        query = QSqlQuery("SELECT value FROM meta WHERE key = 'db_version'")
        if not query.exec():
            self.db_busy = self._is_file_locked(self.db.databaseName())
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
        if not self._open_connection(db_path()):
            return False
        version = self.get_db_version()
        self.db.close()
        return version is not None and version > self.DB_VERSION

    def check_db_file_integrity(self, alternative_path: str = "") -> bool:
        checked_path: str = alternative_path if alternative_path else db_path()
        if not self._open_connection(checked_path):
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
        if not self._open_connection(migrated_path):
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
        if not self._open_connection(path):
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

    @staticmethod
    def local_db_path() -> str:
        return db_path()

    def read_db_diff(self, old_path: str, new_path: str) -> DbDiff | None:
        try:
            with self._file_connection(new_path) as connection:
                self._file_execute(connection, "ATTACH DATABASE ? AS old", old_path)
                diff = DbDiff()
                for table in DETAILED_TABLES:
                    diff.tables[table] = self._read_table_diff(connection, table)
                diff.other_tables = self._read_other_tables_diff(connection)
                return diff
        except Exception as e:
            log.x(f"Не удалось сравнить файлы базы данных {old_path} и {new_path}: {e}")
            return None

    def _common_columns(self, connection: str, table: str, other_schema: str = "old") -> list[str]:
        other_columns = [row[1] for row in self._file_execute(connection, f'PRAGMA {other_schema}.table_info("{table}")')]
        main_columns = [row[1] for row in self._file_execute(connection, f'PRAGMA main.table_info("{table}")')]
        return [column for column in main_columns if column in other_columns]

    def apply_merge(self, target_path: str, source_path: str, plan: MergePlan,
                    my_changes: DbDiff) -> dict[str, dict[int, int]] | None:
        try:
            with self._file_connection(target_path) as connection:
                self._file_execute(connection, "ATTACH DATABASE ? AS mine", source_path)
                self._file_execute(connection, "BEGIN")
                for key, value in self.changelog_session().items():
                    self._file_execute(connection, "DELETE FROM main.meta WHERE key = ?", key)
                    self._file_execute(connection, "INSERT INTO main.meta (key, value) VALUES (?, ?)", key, value)
                for table in reversed(DETAILED_TABLES):
                    self._delete_rows(connection, table, plan.deletes.get(table, []))
                id_maps: dict[str, dict[int, int]] = {}
                for table in DETAILED_TABLES:
                    added_ids = [row_id for row_id in my_changes.added_ids(table) if row_id not in plan.skip_added.get(table, [])]
                    id_maps[table] = self._copy_added_rows(connection, table, added_ids, id_maps)
                for table in DETAILED_TABLES:
                    self._update_rows(connection, table, plan.updates.get(table, []), id_maps)
                self._file_execute(connection, "COMMIT")
                return id_maps
        except Exception as e:
            log.x(f"Не удалось добавить строки из {source_path} в {target_path}: {e}")
            return None

    def _delete_rows(self, connection: str, table: str, ids: list[int]) -> None:
        for row_id in ids:
            self._file_execute(connection, f'DELETE FROM main."{table}" WHERE {key_sql(table, f'main."{table}"')} = ?', row_id)
        if not ids:
            return
        removed = ", ".join(str(row_id) for row_id in ids)
        for child, references in REFERENCES.items():
            for column, parent in references.items():
                if parent == table and self._file_execute(connection, f'SELECT COUNT(*) FROM main."{child}" WHERE "{column}" IN ({removed})')[0][0]:
                    raise RuntimeError(f"К удалённым строкам таблицы {table} остались привязаны строки таблицы {child}")

    def _update_rows(self, connection: str, table: str, updates: list[tuple[int, list[str]]],
                     id_maps: dict[str, dict[int, int]]) -> None:
        for row_id, columns in updates:
            fields = ", ".join(f'"{column}"' for column in columns)
            rows = self._file_execute(connection, f'SELECT {fields} FROM mine."{table}" WHERE {key_sql(table, f'mine."{table}"')} = ?', row_id)
            if not rows:
                raise RuntimeError(f"В таблице {table} нет строки с ключом {row_id}")
            values = dict(zip(columns, rows[0]))
            self._map_references(connection, table, values, id_maps)
            assignments = ", ".join(f'"{column}" = ?' for column in columns)
            self._file_execute(connection, f'UPDATE main."{table}" SET {assignments} WHERE {key_sql(table, f'main."{table}"')} = ?', *values.values(), row_id)

    def _map_references(self, connection: str, table: str, values: dict[str, Any], id_maps: dict[str, dict[int, int]]) -> None:
        for column, parent in REFERENCES.get(table, {}).items():
            value = values.get(column)
            if not value:
                continue
            if value in id_maps.get(parent, {}):
                values[column] = id_maps[parent][value]
            elif not self._file_execute(connection, f'SELECT 1 FROM main."{parent}" WHERE "{table_key(parent)}" = ?', value):
                raise RuntimeError(f"Строка таблицы {table} ссылается на отсутствующую строку {value} таблицы {parent}")

    def _copy_added_rows(self, connection: str, table: str, ids: list[int], id_maps: dict[str, dict[int, int]]) -> dict[int, int]:
        columns = self._common_columns(connection, table, "mine")
        key = table_key(table)
        has_own_id = key == "id"
        next_id = 0
        if has_own_id:
            sequence = self._file_execute(connection, "SELECT seq FROM main.sqlite_sequence WHERE name = ?", table)
            last_id = self._file_execute(connection, f'SELECT MAX("{key}") FROM main."{table}"')[0][0]
            next_id = max(int(sequence[0][0]) if sequence else 0, int(last_id or 0)) + 1
        fields = ", ".join(f'"{column}"' for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        id_map: dict[int, int] = {}
        for old_id in sorted(ids):
            rows = self._file_execute(connection, f'SELECT {fields} FROM mine."{table}" WHERE {key_sql(table, f'mine."{table}"')} = ?', old_id)
            if not rows:
                raise RuntimeError(f"В таблице {table} нет строки с ключом {old_id}")
            values = dict(zip(columns, rows[0]))
            self._map_references(connection, table, values, id_maps)
            if has_own_id:
                values[key] = next_id
                next_id += 1
            self._file_execute(connection, f'INSERT INTO main."{table}" ({fields}) VALUES ({placeholders})', *values.values())
            id_map[old_id] = values.get(key, old_id)
        return id_map

    def find_merge_warnings(self, path: str, added: dict[str, list[int]], touched_event_ids: list[int],
                            touched_payment_ids: list[int]) -> MergeWarnings | None:
        warnings = MergeWarnings()

        def id_list(ids: list[int]) -> str:
            return ", ".join(str(row_id) for row_id in ids) or "NULL"

        contractors, contracts, documents = id_list(added["contractor"]), id_list(added["contract"]), id_list(added["contractdocument"])
        events, payments = id_list(added["event"]), id_list(added["payment"])
        touched_events, touched_payments = id_list(touched_event_ids), id_list(touched_payment_ids)
        title = "(SELECT e.receiver || ' — ' || e.name FROM event e WHERE e.id = n.eventid)"
        try:
            with self._file_connection(path) as connection:
                warnings.duplicate_contractors = self._query_dicts(
                    connection, ["name"],
                    f"SELECT n.name FROM contractor n WHERE n.id IN ({contractors}) AND EXISTS ("
                    f"SELECT 1 FROM contractor o WHERE o.id NOT IN ({contractors}) AND o.name IS n.name) ORDER BY n.id")
                warnings.duplicate_contracts = self._query_dicts(
                    connection, ["contractor_name", "name", "date"],
                    f"SELECT r.name, n.name, n.date FROM contract n LEFT JOIN contractor r ON r.id = n.contractor_id "
                    f"WHERE n.id IN ({contracts}) AND EXISTS ("
                    f"SELECT 1 FROM contract o WHERE o.id NOT IN ({contracts}) AND o.contractor_id IS n.contractor_id "
                    f"AND o.name IS n.name AND o.date IS n.date) ORDER BY n.id")
                warnings.duplicate_documents = self._query_dicts(
                    connection, ["contractor_name", "contract_number", "contract_date", "document_name"],
                    f"SELECT r.name, c.name, c.date, n.document_name FROM contractdocument n "
                    f"LEFT JOIN contract c ON c.id = n.contract_id LEFT JOIN contractor r ON r.id = c.contractor_id "
                    f"WHERE n.id IN ({documents}) AND EXISTS ("
                    f"SELECT 1 FROM contractdocument o WHERE o.id NOT IN ({documents}) AND o.contract_id IS n.contract_id "
                    f"AND o.document_name IS n.document_name) ORDER BY n.id")
                warnings.duplicate_events = self._query_dicts(
                    connection, ["receiver", "name", "totalamount", "duedate"],
                    f"SELECT n.receiver, n.name, n.totalamount, n.duedate FROM event n WHERE n.id IN ({events}) AND EXISTS ("
                    f"SELECT 1 FROM event o WHERE o.id NOT IN ({events}) AND o.receiver IS n.receiver AND o.name IS n.name "
                    f"AND o.totalamount IS n.totalamount AND o.duedate IS n.duedate) ORDER BY n.id")
                warnings.duplicate_payments = self._query_dicts(
                    connection, ["event_title", "sum", "paymentdate"],
                    f"SELECT {title}, n.sum, n.paymentdate FROM payment n WHERE n.id IN ({payments}) AND EXISTS ("
                    f"SELECT 1 FROM payment o WHERE o.id NOT IN ({payments}) AND o.eventid IS n.eventid "
                    f"AND o.paymentdate IS n.paymentdate AND o.sum IS n.sum) ORDER BY n.id")
                warnings.overpaid_events = self._query_dicts(
                    connection, ["receiver", "name", "totalamount", "duedate", "paid"],
                    f"SELECT e.receiver, e.name, e.totalamount, e.duedate, ROUND(SUM(CAST(p.sum AS REAL)), 2) "
                    f"FROM event e JOIN payment p ON p.eventid = e.id "
                    f"WHERE e.id IN ({touched_events}) OR e.id IN (SELECT eventid FROM payment WHERE id IN ({touched_payments})) "
                    f"GROUP BY e.id "
                    f"HAVING ROUND(SUM(CAST(p.sum AS REAL)), 2) > ROUND(CAST(e.totalamount AS REAL), 2) ORDER BY e.id")
            return warnings
        except Exception as e:
            log.x(f"Не удалось проверить результат объединения в файле {path}: {e}")
            return None

    def _query_dicts(self, connection: str, names: list[str], sql: str) -> list[dict]:
        return [dict(zip(names, row)) for row in self._file_execute(connection, sql)]

    @staticmethod
    def _derived_fields(table: str, alias: str, schema: str) -> list[str]:
        def document_fields(document_id: str) -> list[str]:
            source = (f"FROM {schema}.contractdocument d JOIN {schema}.contract c ON c.id = d.contract_id "
                      f"LEFT JOIN {schema}.contractor r ON r.id = c.contractor_id WHERE d.id = {document_id}")
            return [f"(SELECT {column} {source})" for column in ("r.name", "c.name", "c.date", "d.document_name")]

        responsible = f"(SELECT p.name FROM {schema}.personal p WHERE p.id = {alias}.responsible)"
        if table == "payment":
            return [f"(SELECT e.receiver || ' — ' || e.name FROM {schema}.event e WHERE e.id = {alias}.eventid)"]
        if table == "event":
            return [responsible]
        if table == "contract":
            return [f"(SELECT r.name FROM {schema}.contractor r WHERE r.id = {alias}.contractor_id)"]
        if table == "contractdocument":
            return document_fields(f"{alias}.id")[:3]
        if table == "contractpaymentterm":
            return document_fields(f"{alias}.document_id")
        if table == "contractsavedvalues":
            return document_fields(f"{alias}.contractdocumentid") + [responsible]
        if table in KEY_COLUMNS:
            return [key_sql(table, alias)]
        return []

    def _read_table_diff(self, connection: str, table: str) -> TableDiff:
        columns = self._common_columns(connection, table)
        if any(column not in columns for column in KEY_COLUMNS.get(table, (table_key(table),))):
            return TableDiff()
        names = columns + list(TABLE_DERIVED_COLUMNS.get(table, ()))

        def select(alias: str, schema: str) -> str:
            return ", ".join([f'{alias}."{column}"' for column in columns] + self._derived_fields(table, alias, schema))

        def read(sql: str) -> list[list]:
            return self._file_execute(connection, sql)

        def visible(alias: str, schema: str) -> str:
            if not is_viewer():
                return ""
            if table == "event":
                return f' AND COALESCE({alias}."hidden", 0) = 0'
            if table == "payment":
                return f' AND {alias}."eventid" IN (SELECT id FROM {schema}."event" WHERE COALESCE(hidden, 0) = 0)'
            return ""

        added = read(f'SELECT {select("n", "main")} FROM main."{table}" n '
                     f'WHERE {key_sql(table, "n")} NOT IN (SELECT {key_sql(table, "k")} FROM old."{table}" k){visible("n", "main")} '
                     f'ORDER BY {key_sql(table, "n")}')
        removed = read(f'SELECT {select("o", "old")} FROM old."{table}" o '
                       f'WHERE {key_sql(table, "o")} NOT IN (SELECT {key_sql(table, "k")} FROM main."{table}" k){visible("o", "old")} '
                       f'ORDER BY {key_sql(table, "o")}')
        differs = " OR ".join(f'n."{column}" IS NOT o."{column}"' for column in columns)
        changed = read(f'SELECT {select("n", "main")}, {select("o", "old")} FROM main."{table}" n '
                       f'JOIN old."{table}" o ON {key_sql(table, "n")} = {key_sql(table, "o")} '
                       f'WHERE ({differs}){visible("n", "main")}{visible("o", "old")} ORDER BY {key_sql(table, "n")}')
        width = len(names)
        return TableDiff([dict(zip(names, row)) for row in added],
                         [dict(zip(names, row)) for row in removed],
                         [(dict(zip(names, row[width:])), dict(zip(names, row[:width]))) for row in changed])

    def _read_other_tables_diff(self, connection: str) -> dict[str, tuple[int, int]]:
        tables = [row[0] for row in self._file_execute(
            connection, "SELECT name FROM main.sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        service_keys = ", ".join(f"'{key}'" for key in SERVICE_META_KEYS)
        result: dict[str, tuple[int, int]] = {}
        for table in tables:
            columns = self._common_columns(connection, table)
            if table in DETAILED_TABLES or table == CHANGELOG_TABLE or not columns:
                continue
            fields = ", ".join(f'"{column}"' for column in columns)
            condition = f" WHERE key NOT IN ({service_keys})" if table == "meta" else ""
            new_rows = f'SELECT {fields} FROM main."{table}"{condition}'
            old_rows = f'SELECT {fields} FROM old."{table}"{condition}'
            only_new = int(self._file_execute(connection, f"SELECT COUNT(*) FROM ({new_rows} EXCEPT {old_rows})")[0][0])
            only_old = int(self._file_execute(connection, f"SELECT COUNT(*) FROM ({old_rows} EXCEPT {new_rows})")[0][0])
            if only_new or only_old:
                result[table] = (only_new, only_old)
        return result

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
        if not self._open_connection(db_path(), read_only=is_viewer()):
            log.c(f"Не удалось открыть базу данных по указанному пути (неизвестная ошибка): {db_path()}")
            return False
        clear_calendar_cache()
        if not is_viewer():
            self.start_changelog_session()
        return True

    def changelog_session(self) -> dict[str, str]:
        return {CHANGELOG_AUTHOR_KEY: self.settings_handler.sync_author(), CHANGELOG_MACHINE_KEY: node()}

    def start_changelog_session(self) -> None:
        for key, value in self.changelog_session().items():
            if self.get_setting(key, None) != value and not self.set_setting(key, value):
                log.w(f"Не удалось записать в базу данных автора изменений ({key})")
        query = QSqlQuery()
        if not query.exec(f"DELETE FROM {CHANGELOG_TABLE} WHERE changed_at < "
                          f"strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime', '-{self.CHANGELOG_KEEP_MONTHS} months')"):
            log.w(f"Не удалось удалить устаревшие записи журнала изменений: {query.lastError().text()}")

    def rebuild_changelog_triggers(self) -> None:
        for table in CHANGELOG_DATA_TABLES:
            query = QSqlQuery()
            if not query.exec(f'PRAGMA table_info("{table}")'):
                raise MigrationError(f"Не удалось прочитать столбцы таблицы {table}: {query.lastError().text()}")
            columns: list[str] = []
            while query.next():
                columns.append(query.value(1))
            statements = [f"DROP TRIGGER IF EXISTS trg_{table}_log_{action}" for action in CHANGELOG_ACTIONS]
            for statement in statements + changelog_triggers(table, columns):
                if not query.exec(statement):
                    raise MigrationError(f"Ошибка SQL: {query.lastError().text()}. Запрос: {statement}")

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
        if self.in_transaction:
            return action()
        if not self.db.transaction():
            log.e(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            return False
        self.in_transaction = True
        try:
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
        finally:
            self.in_transaction = False

    def delete_payments_by_event(self, event_id: int) -> bool:
        query = QSqlQuery()
        query.prepare("DELETE FROM payment WHERE eventid = ?")
        query.addBindValue(event_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке удалить оплаты платежа {event_id}: {query.lastError().text()}")
            return False
        return True

    def switch_db_files(self, new_file_path: str = "", close_current_connection: bool = False) -> bool:
        if close_current_connection:
            self.db.close()
        temp_path: Path = Path(db_path()).with_name("db_new.db")
        try:
            shutil.copy(new_file_path, temp_path)
            temp_path.replace(db_path())
            return True
        except FileNotFoundError:
            log.c(f"Файл {new_file_path} не найден, рабочая база данных {db_path()} не изменена")
        except Exception as e:
            log.x(f"При замене файла БД произошла ошибка, рабочая база данных {db_path()} не изменена: {e}")
        temp_path.unlink(missing_ok=True)
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
                          f"{'AND COALESCE(E.hidden, 0) = 0 ' if is_viewer() else ''}"
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
            f"SELECT category, responsible, COUNT(*) AS cnt FROM event WHERE responsible IN (SELECT id FROM personal)"
            f"{' AND COALESCE(hidden, 0) = 0' if is_viewer() else ''} "
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
                query.prepare("UPDATE personal SET name = ?, department = ?, archived = ?, position = ? WHERE id = ? "
                              "AND (name, department, archived, position) IS NOT (?, ?, ?, ?)")
                for val in [entry[1], entry[2], entry[3], position_value, entry[0],
                            entry[1], entry[2], entry[3], position_value]:
                    query.addBindValue(val)
            else:
                query.prepare("INSERT INTO personal(id, name, department, archived, position) VALUES (?,?,?,?,?)")
                for val in [entry[0], entry[1], entry[2], entry[3], position_value]:
                    query.addBindValue(val)
            if not query.exec():
                log.e(f"Ошибка SQL при попытке сохранения записей в таблице personal: {query.lastError().text()}")
                return False
        return True

    def get_paymentsum_for_period(self, date_from: date, date_to: date) -> dict[date, list[PaymentEntry]] | None:
        if not self.is_db_connected():
            return None
        query: QSqlQuery = QSqlQuery()
        query.prepare(
            "SELECT payment.paymentdate, payment.sum, "
            "COALESCE(event.name, ''), event.receiver, payment.id, payment.eventid, event.descr "
            "FROM payment "
            "LEFT JOIN event ON event.id = payment.eventid "
            "WHERE payment.paymentdate BETWEEN ? AND ?"
            f"{' AND COALESCE(event.hidden, 0) = 0' if is_viewer() else ''}"
        )
        query.addBindValue(date_from.isoformat())
        query.addBindValue(date_to.isoformat())
        if not query.exec():
            log.e(f"Не удалось получить перечень платежей за период с {date_from} по {date_to}: {query.lastError().text()}")
            return None

        by_date: dict[date, list[PaymentEntry]] = {}

        while query.next():
            paymentdate = str_date(query.value(0), python_date=True)
            amount = str_decimal(query.value(1))
            receiver = "" if self._is_null(query.value(3)) else query.value(3)
            basis = "" if self._is_null(query.value(6)) else query.value(6)
            descr = query.value(2) + f" ({receiver})"
            by_date.setdefault(paymentdate, []).append(
                PaymentEntry(amount, descr, receiver, query.value(4), query.value(5), f"{query.value(2)} {basis}",
                             key=f"c|{query.value(4)}"))

        return by_date

    def read_payment_info(self, payment_id: int) -> PaymentInfo | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT payment.paymentdate, payment.sum, payment.eventid, event.name, event.receiver, "
                      "event.duedate, event.totalamount "
                      "FROM payment JOIN event ON event.id = payment.eventid WHERE payment.id = ?")
        query.addBindValue(payment_id)
        if not query.exec() or not query.next():
            log.e(f"Не удалось прочитать оплату {payment_id} вместе с платежом: {query.lastError().text()}")
            return None
        payment_date = str_date(query.value(0), python_date=True)
        payment_sum = str_decimal(query.value(1))
        total_amount = str_decimal(query.value(6))
        event_id = query.value(2)
        name = "" if self._is_null(query.value(3)) else query.value(3)
        receiver = "" if self._is_null(query.value(4)) else query.value(4)
        due_date = None if self._is_null(query.value(5)) else str_date(query.value(5), python_date=True)
        if payment_date is None or payment_sum is None or total_amount is None:
            log.e(f"Не удалось распознать данные оплаты {payment_id}")
            return None

        query.prepare("SELECT sum FROM payment WHERE eventid = ?")
        query.addBindValue(event_id)
        if not query.exec():
            log.e(f"Не удалось прочитать оплаты платежа {event_id}: {query.lastError().text()}")
            return None
        paid_amount = Decimal(0)
        while query.next():
            paid_amount += str_decimal(query.value(0)) or Decimal(0)
        return PaymentInfo(payment_id, event_id, payment_date, payment_sum, name, receiver, due_date, total_amount,
                           paid_amount)

    def update_payment(self, payment_id: int, new_payment_date: date, new_payment_sum: Decimal,
                       new_total_amount: Decimal) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("UPDATE payment SET paymentdate = ?, sum = ? WHERE id = ?")
            query.addBindValue(date_str(new_payment_date))
            query.addBindValue(str(new_payment_sum))
            query.addBindValue(payment_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось изменить оплату {payment_id}: {query.lastError().text()}")
                return False
            query.prepare("UPDATE event SET totalamount = ? WHERE id = (SELECT eventid FROM payment WHERE id = ?)")
            query.addBindValue(str(new_total_amount))
            query.addBindValue(payment_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось изменить общую сумму платежа для оплаты {payment_id}: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def delete_payment(self, payment_id: int) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("DELETE FROM payment WHERE id = ?")
            query.addBindValue(payment_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось удалить оплату {payment_id}: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def load_column_values(self, column: str, as_set: bool = True) -> set | list | None:
        if not self.is_db_connected():
            return None
        results: list = []
        query: QSqlQuery = QSqlQuery(f"SELECT {column} FROM event WHERE type = 2{' AND COALESCE(hidden, 0) = 0' if is_viewer() else ''}")
        if query.lastError().isValid():
            log.e(f"Ошибка SQL при попытке получить значения столбца {column} из таблицы event: {query.lastError().text()}")
            return None
        while query.next():
            results.append(query.value(0))
        return results if not as_set else set(results)

    def load_payment_totals(self, current_date: QDate, event_id: int | None = None) -> dict[int, tuple[Decimal, Decimal, str]] | None:
        if not self.is_db_connected():
            return None
        cents = "CAST(ROUND(CAST(payment.sum AS REAL) * 100) AS INTEGER)"
        query = QSqlQuery()
        query.prepare(f"SELECT eventid, SUM({cents}), "
                      f"SUM(CASE WHEN paymentdate = ? THEN {cents} ELSE 0 END), "
                      f"MAX(paymentdate) "
                      f"FROM payment {'' if event_id is None else 'WHERE eventid = ? '}GROUP BY eventid")
        query.addBindValue(date_str(current_date))
        if event_id is not None:
            query.addBindValue(event_id)
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

    def load_events(self, threshold: str | None = None, event_id: int | None = None) -> list[tuple] | None:
        if not self.is_db_connected():
            return None
        sql = f"SELECT {', '.join(EVENT_COLUMN_NAMES)} FROM event"
        conditions: list[str] = []
        if event_id is not None:
            conditions.append(f"id = {int(event_id)}")
        elif threshold:
            conditions.append(self.paid_load_filter(threshold))
        if is_viewer():
            conditions.append("COALESCE(hidden, 0) = 0")
        if conditions:
            sql += f" WHERE {' AND '.join(conditions)}"
        query = QSqlQuery()
        if not query.exec(sql + " ORDER BY id"):
            log.e(f"Ошибка SQL при попытке получить данные из таблицы event: {query.lastError().text()}")
            return None
        column_count = query.record().count()
        events: list[tuple] = []
        while query.next():
            values = [query.value(column) for column in range(column_count)]
            events.append(tuple(None if self._is_null(value) else value for value in values))
        return events

    @staticmethod
    def _event_value(value: Any) -> Any:
        return value.rstrip() if isinstance(value, str) else value

    def insert_event(self, data: list) -> int | None:
        if len(data) != len(EVENT_COLUMN_NAMES):
            raise IndexError("В новую строку передано неверное количество данных")
        if not self.is_db_connected():
            return None
        columns = [name for name in EVENT_COLUMN_NAMES if name != "id"]
        values = [self._event_value(value) for name, value in zip(EVENT_COLUMN_NAMES, data) if name != "id"]
        new_ids: list[int] = []

        def action() -> bool:
            query = QSqlQuery()
            query.prepare(f"INSERT INTO event ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})")
            for value in values:
                query.addBindValue(value)
            if not query.exec():
                log.e(f"Не удалось добавить строку в таблицу event: {query.lastError().text()}")
                return False
            new_ids.append(int(query.lastInsertId()))
            return True

        return new_ids[0] if self.run_in_transaction(action) and new_ids else None

    def insert_payment(self, data: list) -> int | None:
        if len(data) != self.PAYMENT_TABLE_COLUMNUM - 1:
            raise IndexError("В новую оплату передано неверное количество данных")
        if not self.is_db_connected():
            return None
        new_ids: list[int] = []

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("INSERT INTO payment (eventid, paymentdate, sum, createdate) VALUES (?, ?, ?, ?)")
            for value in data:
                query.addBindValue(value)
            if not query.exec():
                log.e(f"Не удалось добавить строку в таблицу payment: {query.lastError().text()} "
                      f"[запрос: {query.lastQuery()}, значений: {len(query.boundValues())}, "
                      f"код: {query.lastError().nativeErrorCode()}, база открыта: {self.db.isOpen()}, "
                      f"в транзакции: {self.in_transaction}]")
                return False
            new_ids.append(int(query.lastInsertId()))
            return True

        return new_ids[0] if self.run_in_transaction(action) and new_ids else None

    def update_event(self, event_id: int, data: list) -> bool:
        if len(data) != len(EVENT_COLUMN_NAMES):
            raise IndexError("В строку передано неверное количество данных")
        if not self.is_db_connected():
            return False
        columns = [name for name in EVENT_COLUMN_NAMES if name != "id"]
        values = [self._event_value(value) for name, value in zip(EVENT_COLUMN_NAMES, data) if name != "id"]

        def action() -> bool:
            stored = self.load_events(event_id=event_id)
            if not stored:
                log.e(f"Не удалось изменить строку {event_id} в таблице event: строка не найдена")
                return False
            if [value for name, value in zip(EVENT_COLUMN_NAMES, stored[0]) if name != "id"] == values:
                return True
            query = QSqlQuery()
            query.prepare(f"UPDATE event SET {', '.join(f'{name} = ?' for name in columns)} WHERE id = ?")
            for value in values:
                query.addBindValue(value)
            query.addBindValue(event_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось сохранить изменения строки {event_id} в таблице event: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def update_event_field(self, event_id: int, field: str, value: Any) -> bool:
        if field not in EVENT_COLUMN_NAMES or field == "id":
            raise ValueError(f"Недопустимый столбец таблицы event: {field}")
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare(f"UPDATE event SET {field} = ? WHERE id = ?")
            query.addBindValue(self._event_value(value))
            query.addBindValue(event_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось изменить поле {field} строки {event_id} в таблице event: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def delete_event(self, event_id: int) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("DELETE FROM event WHERE id = ?")
            query.addBindValue(event_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось удалить строку {event_id} из таблицы event: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def load_changelog(self, event_id: int) -> tuple[list[ChangeRecord], dict[int, tuple[str, str]]] | None:
        if not self.is_db_connected():
            return None
        payment_ids = ("SELECT id FROM payment WHERE eventid = ? UNION "
                       f"SELECT recordid FROM {CHANGELOG_TABLE} WHERE tablename = 'payment' AND action IN ('insert', 'delete') "
                       "AND json_extract(COALESCE(newvalue, oldvalue), '$.eventid') = ?")
        queries = (f"SELECT id, changed_at, author, machine, tablename, recordid, action, field, oldvalue, newvalue FROM {CHANGELOG_TABLE} "
                   f"WHERE (tablename = 'event' AND recordid = ?) OR (tablename = 'payment' AND recordid IN ({payment_ids})) ORDER BY id",
                   "SELECT id, paymentdate, sum FROM payment WHERE eventid = ?")
        bindings = ((event_id, event_id, event_id), (event_id,))
        results: list[list[tuple]] = []
        for sql, values in zip(queries, bindings):
            query = QSqlQuery()
            query.prepare(sql)
            for value in values:
                query.addBindValue(value)
            if not query.exec():
                log.e(f"Не удалось прочитать журнал изменений платежа {event_id}: {query.lastError().text()}")
                return None
            rows: list[tuple] = []
            while query.next():
                rows.append(tuple(None if query.isNull(column) else query.value(column) for column in range(query.record().count())))
            results.append(rows)
        records = [ChangeRecord(row[0], row[1], row[2] or "", row[3] or "", row[4], row[5], row[6], row[7], row[8], row[9])
                   for row in results[0]]
        return records, {row[0]: (row[1] or "", row[2] or "") for row in results[1]}

    def load_event_backup(self, event_id: int) -> tuple[tuple, list[tuple]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        queries = (f"SELECT {', '.join(EVENT_COLUMN_NAMES)} FROM event WHERE id = ?",
                   "SELECT id, eventid, paymentdate, sum, createdate FROM payment WHERE eventid = ? ORDER BY id")
        results: list[list[tuple]] = []
        for sql in queries:
            query.prepare(sql)
            query.addBindValue(event_id)
            if not query.exec():
                log.e(f"Не удалось прочитать данные платежа {event_id}: {query.lastError().text()}")
                return None
            rows: list[tuple] = []
            while query.next():
                rows.append(tuple(None if query.isNull(column) else query.value(column)
                                  for column in range(query.record().count())))
            results.append(rows)
        return (results[0][0], results[1]) if results[0] else None

    def restore_event(self, event: tuple, payments: list[tuple]) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare(f"INSERT INTO event ({', '.join(EVENT_COLUMN_NAMES)}) "
                          f"VALUES ({', '.join('NULL' if value is None else '?' for value in event)})")
            for value in event:
                if value is not None:
                    query.addBindValue(value)
            if not query.exec():
                log.e(f"Не удалось восстановить строку в таблице event: {query.lastError().text()}")
                return False
            for payment in payments:
                query.prepare("INSERT INTO payment (id, eventid, paymentdate, sum, createdate) "
                              f"VALUES ({', '.join('NULL' if value is None else '?' for value in payment)})")
                for value in payment:
                    if value is not None:
                        query.addBindValue(value)
                if not query.exec():
                    log.e(f"Не удалось восстановить оплату в таблице payment: {query.lastError().text()}")
                    return False
            return True

        return self.run_in_transaction(action)

    @staticmethod
    def paid_load_filter(threshold: str) -> str:
        cents = "CAST(ROUND(CAST({}.{} AS REAL) * 100) AS INTEGER)"
        return ("event.id NOT IN (SELECT p.eventid FROM payment p JOIN event e ON e.id = p.eventid "
                "GROUP BY p.eventid "
                f"HAVING MAX(p.paymentdate) <= '{threshold}' "
                f"AND SUM({cents.format('p', 'sum')}) >= {cents.format('e', 'totalamount')})")

    def load_contractors(self) -> list[tuple[int, str, bool]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery("SELECT id, name, archived FROM contractor")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contractor: {query.lastError().text()}")
            return None
        contracors: list = []
        while query.next():
            contracors.append((query.value(0), query.value(1), bool(query.value(2))))
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

    def rename_contractor(self, contractor_id: int, contractor_name: str) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("UPDATE contractor SET name = ? WHERE id = ?")
            query.addBindValue(contractor_name)
            query.addBindValue(contractor_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось переименовать контрагента {contractor_id}: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def update_contract(self, contract_id: int, contract_name: str, contract_date: str) -> bool:
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare("UPDATE contract SET name = ?, date = ? WHERE id = ?")
            query.addBindValue(contract_name)
            query.addBindValue(contract_date)
            query.addBindValue(contract_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось изменить договор {contract_id}: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def set_archived(self, table: str, row_id: int, archived: bool) -> bool:
        if table not in ("contractor", "contract"):
            raise ValueError(f"Таблица {table} не поддерживает архив")
        if not self.is_db_connected():
            return False

        def action() -> bool:
            query = QSqlQuery()
            query.prepare(f"UPDATE {table} SET archived = ? WHERE id = ?")
            query.addBindValue(int(archived))
            query.addBindValue(row_id)
            if not query.exec() or query.numRowsAffected() != 1:
                log.e(f"Не удалось изменить признак архива у записи {row_id} таблицы {table}: {query.lastError().text()}")
                return False
            return True

        return self.run_in_transaction(action)

    def load_contracts(self, contractor_id: int) -> list[tuple[int, str, str, bool]] | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare("SELECT id, name, date, archived FROM contract WHERE contractor_id = ?")
        query.addBindValue(contractor_id)
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить данные из таблицы contract: {query.lastError().text()}")
            return None
        contracts: list = []
        while query.next():
            contracts.append((query.value(0), query.value(1), query.value(2), bool(query.value(3))))
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
        query = QSqlQuery("SELECT d.id, c.contractor_id, ctr.name, d.contract_id, c.name, c.date, d.document_name, d.monthly "
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
                monthly=bool(int(query.value(7) or 0)),
            )
        return titles

    def load_contract_history(self, contractor_id: int, contract_id: int | None = None,
                              document_id: int | None = None
                              ) -> tuple[list[ContractObligation], list[ContractPayment]] | None:
        if not self.is_db_connected():
            return None
        cents = "CAST(ROUND(CAST({} AS REAL) * 100) AS INTEGER)"
        where = "WHERE e.type = 2 AND c.contractor_id = ?"
        params = [contractor_id]
        if contract_id is not None:
            where += " AND c.id = ?"
            params.append(contract_id)
        if document_id is not None:
            where += " AND d.id = ?"
            params.append(document_id)
        if is_viewer():
            where += " AND COALESCE(e.hidden, 0) = 0"
        joins = ("JOIN contractdocument d ON d.id = e.contractdocument_id "
                 "JOIN contract c ON c.id = d.contract_id ")
        queries = (
            ("обязательств", f"SELECT e.id, e.name, e.duedate, COALESCE({cents.format('e.totalamount')}, 0), "
                             f"COALESCE(SUM({cents.format('p.sum')}), 0), d.document_name, c.id, c.name, c.date "
                             f"FROM event e {joins}LEFT JOIN payment p ON p.eventid = e.id {where} "
                             f"GROUP BY e.id ORDER BY e.duedate, e.id"),
            ("оплат", f"SELECT p.id, e.id, e.name, p.paymentdate, COALESCE({cents.format('p.sum')}, 0), "
                      f"d.document_name, c.id, c.name, c.date "
                      f"FROM payment p JOIN event e ON e.id = p.eventid {joins}{where} "
                      f"ORDER BY p.paymentdate, p.id"),
        )
        results: list[list[tuple]] = []
        for title, sql in queries:
            query = QSqlQuery()
            query.prepare(sql)
            for param in params:
                query.addBindValue(param)
            if not query.exec():
                log.e(f"Ошибка SQL при попытке получить историю {title} по контрагенту {contractor_id}: {query.lastError().text()}")
                return None
            rows: list[tuple] = []
            while query.next():
                rows.append(tuple(query.value(column) for column in range(query.record().count())))
            results.append(rows)

        def text(value: Any) -> str:
            return "" if self._is_null(value) else str(value)

        obligations = [ContractObligation(
            event_id=int(row[0]), name=text(row[1]), due_date=str_date(text(row[2])), total=Decimal(int(row[3])) / 100,
            paid=Decimal(int(row[4])) / 100, document_name=text(row[5]), contract_id=int(row[6]),
            contract_number=text(row[7]), contract_date=str_date(text(row[8]))) for row in results[0]]
        payments = [ContractPayment(
            payment_id=int(row[0]), event_id=int(row[1]), event_name=text(row[2]), payment_date=str_date(text(row[3])),
            amount=Decimal(int(row[4])) / 100, document_name=text(row[5]), contract_id=int(row[6]),
            contract_number=text(row[7]), contract_date=str_date(text(row[8]))) for row in results[1]]
        return obligations, payments

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
                      "t.has_calendar_condition, t.month_day, t.month_type, d.monthly, d.monthlyamount, d.monthlyname "
                      "FROM contractdocument d "
                      "JOIN contract c ON c.id = d.contract_id "
                      "LEFT JOIN contractor ctr ON ctr.id = c.contractor_id "
                      "LEFT JOIN contractpaymentterm t ON t.document_id = d.id "
                      "WHERE d.id = :id")
        query.bindValue(":id", document_id)
        if not query.exec() or not query.next():
            log.e(f"Ошибка SQL при попытке получить данные для создания ContractDocumentData {query.lastError().text()}")
            return None

        v = [_val(query, i) for i in range(19)]

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
            monthly=bool(int(v[16] or 0)),
            monthly_amount=str_decimal(v[17]),
            monthly_name=v[18] or "",
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
                    (contract_id, document_type, document_name, description, position_id, monthly, monthlyamount, monthlyname)
                VALUES
                    (:contract_id, :document_type, :document_name, :description, :position_id, :monthly, :monthlyamount, :monthlyname)
            """)
        else:
            query.prepare("""
                UPDATE contractdocument SET
                    contract_id   = :contract_id,
                    document_type = :document_type,
                    document_name = :document_name,
                    description   = :description,
                    position_id   = :position_id,
                    monthly       = :monthly,
                    monthlyamount = :monthlyamount,
                    monthlyname   = :monthlyname
                WHERE id = :id
            """)
            query.bindValue(":id", data.document_id)

        query.bindValue(":contract_id", data.contract_id)
        query.bindValue(":document_type", data.document_type)
        query.bindValue(":document_name", data.document_name)
        query.bindValue(":description", data.description)
        query.bindValue(":position_id", position_id)
        query.bindValue(":monthly", 1 if data.monthly else 0)
        query.bindValue(":monthlyamount", str(data.monthly_amount) if data.monthly and data.monthly_amount else None)
        query.bindValue(":monthlyname", data.monthly_name.strip() if data.monthly and data.monthly_name.strip() else None)

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

    def load_contractors_for_combobox(self, include_id: int | None = None) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            f"SELECT id, COALESCE(name, '') || {self.ARCHIVE_MARK} FROM contractor WHERE archived = 0 OR id IS ?", (include_id,),
            "Ошибка SQL при попытке получить список контрагентов")

    def load_contracts_for_combobox(self, contractor_id: int, include_id: int | None = None) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            "SELECT id, '№ ' || COALESCE(name, '') || CASE WHEN COALESCE(date, '') = '' THEN '' "
            f"ELSE ' от ' || strftime('%d.%m.%Y', date) END || {self.ARCHIVE_MARK} "
            "FROM contract WHERE contractor_id = ? AND (archived = 0 OR id IS ?)", (contractor_id, include_id),
            "Ошибка SQL при попытке получить список договоров")

    def load_contract_documents_for_combobox(self, contract_id: int) -> list[tuple[int, str]] | None:
        return self._load_id_name_list(
            "SELECT id, document_name FROM contractdocument WHERE contract_id = ?", (contract_id,),
            "Ошибка SQL при попытке получить список документов договора")

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
        query.prepare(f"SELECT descr FROM event WHERE type = ? AND contractdocument_id = ?{' AND COALESCE(hidden, 0) = 0' if is_viewer() else ''}")
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

    def load_monthly_entries(self, month: QDate) -> list[MonthlyEntry] | None:
        if not self.is_db_connected():
            return None
        start = QDate(month.year(), month.month(), 1)
        query = QSqlQuery()
        query.prepare(
            "SELECT e.contractdocument_id, e.id, e.duedate, e.totalamount, "
            "ROUND(COALESCE(p.paid, 0), 2) >= ROUND(CAST(e.totalamount AS REAL), 2) "
            "FROM event e "
            "JOIN contractdocument d ON d.id = e.contractdocument_id "
            "LEFT JOIN (SELECT pp.eventid, SUM(CAST(pp.sum AS REAL)) AS paid FROM payment pp GROUP BY pp.eventid) p ON p.eventid = e.id "
            "WHERE d.monthly = 1 AND e.type = ? AND e.duedate >= ? AND e.duedate < ? "
            "ORDER BY e.duedate, e.id")
        query.addBindValue(int(RowType.LIABILITY))
        query.addBindValue(start.toString(self.DATE_FORMAT))
        query.addBindValue(start.addMonths(1).toString(self.DATE_FORMAT))
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить платежи ежемесячных документов: {query.lastError().text()}")
            return None
        events: dict[int, MonthlyEvent] = {}
        while query.next():
            events.setdefault(int(query.value(0)), MonthlyEvent(
                int(query.value(1)), QDate.fromString(query.value(2) or "", self.DATE_FORMAT),
                str_decimal(str(query.value(3))), bool(int(query.value(4)))))

        query = QSqlQuery()
        query.prepare(
            "SELECT d.id, c.contractor_id, ctr.name, d.contract_id, c.name, c.date, d.document_name, d.monthlyamount, "
            "EXISTS (SELECT 1 FROM contractsavedvalues s WHERE s.contractdocumentid = d.id AND COALESCE(s.category, 0) <> 0), "
            "t.payment_type, t.days_count, t.days_type "
            "FROM contractdocument d "
            "JOIN contract c ON c.id = d.contract_id "
            "JOIN contractpaymentterm t ON t.document_id = d.id AND t.payment_type IN ('FIXED', 'RELATIVE') "
            "LEFT JOIN contractor ctr ON ctr.id = c.contractor_id "
            "WHERE d.monthly = 1 AND c.archived = 0 AND COALESCE(ctr.archived, 0) = 0 "
            "ORDER BY ctr.name, c.name, d.document_name")
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить перечень ежемесячных платежей: {query.lastError().text()}")
            return None
        entries = []
        while query.next():
            title = DocumentTitle(
                document_id=int(query.value(0)), contractor_id=int(query.value(1) or 0), contractor_name=query.value(2) or "",
                contract_id=int(query.value(3)), contract_number=query.value(4) or "",
                contract_date=QDate.fromString(query.value(5) or "", self.DATE_FORMAT), document_name=query.value(6) or "")
            relative_term = ""
            if query.value(9) == PaymentDueType.RELATIVE.value:
                relative_term = relative_term_text(int(query.value(10) or 0), self._enum_from_db(DaysType, query.value(11)))
            entries.append(MonthlyEntry(title, str_decimal(query.value(7)), events.get(title.document_id),
                                        bool(int(query.value(8))), relative_term=relative_term))
        return entries

    def load_last_event(self, document_id: int) -> dict | None:
        if not self.is_db_connected():
            return None
        query = QSqlQuery()
        query.prepare(f"SELECT {', '.join(EVENT_COLUMN_NAMES)} FROM event WHERE contractdocument_id = ? AND type = ? "
                      f"ORDER BY duedate DESC, id DESC LIMIT 1")
        query.addBindValue(document_id)
        query.addBindValue(int(RowType.LIABILITY))
        if not query.exec():
            log.e(f"Ошибка SQL при попытке получить последний платеж документа: {query.lastError().text()}")
            return None
        if not query.next():
            return None
        values = [query.value(column) for column in range(len(EVENT_COLUMN_NAMES))]
        return {name: None if self._is_null(value) else value for name, value in zip(EVENT_COLUMN_NAMES, values)}

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
