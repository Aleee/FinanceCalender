import os
import shutil
import time
from pathlib import Path
import lovely_logger as log
from PySide6.QtCore import QDateTime, QDate
from PySide6.QtSql import QSqlDatabase

from base.dbhandler import DBHandler
from base.lockinfo import lock_holders
from base.paths import db_path, backup_dir
from gui.settings import SettingsHandler

BACKUP_FILE_PREFIXES = ("backup_", "before_sync_", "before_restore_")
SERVICE_COPY_PREFIXES = ("conflict_", "discarded_", "db_corrupt_", "before_sync_", "before_restore_")
SERVICE_COPY_KEEP_DAYS = 90
RENAME_ATTEMPTS = 5
RENAME_PAUSE_SECONDS = 0.5


def save_backup(sh: SettingsHandler, dbh: DBHandler) -> QDateTime:
    backup_path: str = sh.backup_path()
    if not Path(backup_path).is_dir():
        log.e(f"Путь для резервного копирования не указан или неверен: {backup_path}")
        return QDateTime()
    backup_filepath: Path = Path(backup_path).joinpath("backup_" + QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss") + ".db")
    try:
        backup_filepath.unlink(missing_ok=True)
    except OSError as e:
        log.x(f"Не удалось заменить существующую резервную копию {backup_filepath}: {e}")
        return QDateTime()
    if not dbh.copy_db_file(str(backup_filepath)):
        return QDateTime()
    return QDateTime.currentDateTime()


def clean_backup_folder(sh: SettingsHandler) -> bool:
    backup_foldername: str = sh.backup_path()
    if not Path(backup_foldername).is_dir():
        log.e("Не удалось очистить папку с резервными копиями: путь не указан или не существует")
        return False
    try:
        cleanup_period: int = int(sh.settings.value("Backup/cleanupperiod", 30))
    except (ValueError, TypeError):
        log.e("Не удалось очистить папку с резервными копиями: не удалось получить настройки хранения")
        return False
    minimum_date: QDate = QDate.currentDate().addDays(-cleanup_period)
    filenames: list[str] = [item.name for item in Path(backup_foldername).iterdir() if item.is_file()]
    for fname in filenames:
        prefix: str | None = next((p for p in BACKUP_FILE_PREFIXES if fname.startswith(p)), None)
        if prefix is None:  # чтобы не трогать посторонние файлы в папке бэкапов
            continue
        date_substring: str = fname[len(prefix):len(prefix) + 8]
        filedate: QDate = QDate.fromString(date_substring, "yyyyMMdd")
        if not filedate.isValid():
            continue
        if filedate < minimum_date:
            try:
                Path(os.path.join(backup_foldername, fname)).unlink(missing_ok=True)
            except OSError as e:
                log.x(f"Не удалось удалить старую резервную копию {fname}: {e}")
                return False
    return True


def clean_service_copies() -> bool:
    minimum_date: QDate = QDate.currentDate().addDays(-SERVICE_COPY_KEEP_DAYS)
    folder: Path = Path(backup_dir())
    if not folder.is_dir():
        return True
    for item in folder.iterdir():
        prefix: str | None = next((p for p in SERVICE_COPY_PREFIXES if item.name.startswith(p)), None)
        if prefix is None or not item.is_file():
            continue
        filedate: QDate = QDate.fromString(item.name[len(prefix):len(prefix) + 8], "yyyyMMdd")
        if filedate.isValid() and filedate < minimum_date:
            try:
                item.unlink(missing_ok=True)
            except OSError as e:
                log.x(f"Не удалось удалить старую служебную копию {item.name}: {e}")
                return False
    return True


def restore_backup(dbh: DBHandler, db_file_path: str) -> bool:
    migrated_path: str | None = dbh.make_migrated_copy(db_file_path)
    if migrated_path is None:
        log.e(f"Файл {db_file_path} не подходит для восстановления")
        dbh.open_db_connection()
        return False
    try:
        if not save_pre_restore_copy(dbh):
            dbh.open_db_connection()
            return False
        if not replace_db_file(dbh, migrated_path):
            return False
    finally:
        Path(migrated_path).unlink(missing_ok=True)
    log.i(f"База данных восстановлена из файла {db_file_path}")
    return True


def save_pre_restore_copy(dbh: DBHandler) -> bool:
    copy_path: Path = Path(backup_dir()) / ("before_restore_" + QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss") + ".db")
    try:
        copy_path.unlink(missing_ok=True)
    except OSError as e:
        log.x(f"Не удалось заменить существующую копию перед восстановлением {copy_path}: {e}")
        return False
    return dbh.copy_db_file(str(copy_path))


def describe_busy_file(path: Path) -> str:
    connections: str = ", ".join(f"{name}: {'открыто' if QSqlDatabase.database(name, False).isOpen() else 'закрыто'}"
                                 for name in QSqlDatabase.connectionNames()) or "нет"
    try:
        neighbours: str = ", ".join(f"{item.name} ({item.stat().st_size} байт)" for item in sorted(path.parent.iterdir()))
    except OSError as e:
        neighbours = f"не удалось прочитать папку ({e})"
    return f"соединения Qt: {connections}; файлы в папке: {neighbours}; процессы, держащие файл: {lock_holders(path)}"


def rename_with_retry(source: Path, target: Path) -> None:
    for attempt in range(1, RENAME_ATTEMPTS + 1):
        try:
            source.rename(target)
            return
        except PermissionError as e:
            if attempt in (1, RENAME_ATTEMPTS):
                log.w(f"Диагностика занятого файла {source.name}, попытка {attempt} из {RENAME_ATTEMPTS}: {describe_busy_file(source)}")
            if attempt == RENAME_ATTEMPTS:
                raise
            log.w(f"Файл {source.name} занят, попытка {attempt} из {RENAME_ATTEMPTS}: {e}")
            time.sleep(RENAME_PAUSE_SECONDS)


def replace_db_file(dbh: DBHandler, db_file_path: str) -> bool:
    temp_file_created: bool = False
    database: QSqlDatabase = QSqlDatabase.database()
    database.close()
    del database
    default_db_path = Path(db_path())
    temp_db_path: Path = default_db_path.parent / "db_temp.db"
    try:
        temp_db_path.unlink(missing_ok=True)
        rename_with_retry(default_db_path, temp_db_path)
        temp_file_created = True
        shutil.copy(Path(db_file_path), default_db_path)
        temp_db_path.unlink(missing_ok=True)
        dbh.open_db_connection()
        return True
    except FileNotFoundError:
        log.e(f"Файл {db_file_path} не найден")
    except Exception as e:
        log.x(f"При замене файла БД произошла ошибка: {e}")
    if temp_file_created:
        try:
            default_db_path.unlink(missing_ok=True)
            temp_db_path.rename(default_db_path)
        except OSError as e:
            log.c(f"Не удалось вернуть прежний файл БД после неудачного восстановления, он лежит в {temp_db_path}: {e}")
    dbh.open_db_connection()
    return False
