import os
import shutil
from pathlib import Path
import lovely_logger as log
from PySide6.QtCore import QDateTime, QDate

from base.dbhandler import DBHandler
from gui.settings import SettingsHandler


def save_backup(sh: SettingsHandler, dbh: DBHandler) -> QDateTime:
    backup_path: str = sh.settings.value("Backup/path")
    if not backup_path or not Path(backup_path).is_dir():
        log.w(f"Путь для резервного копирования не указан или неверен: {backup_path}")
        return QDateTime()
    backup_filepath: Path = Path(backup_path).joinpath("backup_" + QDateTime().currentDateTime().toString("yyyyMMdd-hhmmss") + ".db")
    try:
        shutil.copy(os.path.abspath(dbh.DEFAULT_DB_RELPATH), backup_filepath)
        return QDateTime().currentDateTime()
    except FileNotFoundError:
        log.w(f"Файл для копирования {os.path.abspath(dbh.DEFAULT_DB_RELPATH)} не найден")
    except Exception as e:
        log.x(f"При попытке создать резервную копию произошла ошибка: {e}")
    return QDateTime()


def clean_backup_folder(sh: SettingsHandler) -> bool:
    backup_foldername: str = sh.settings.value("Backup/path")
    if not backup_foldername or not Path(backup_foldername).is_dir():
        log.w("Не удалось очистить папку с резервными копиями: путь не указан или не существует")
        return False
    try:
        cleanup_period: int = int(sh.settings.value("Backup/cleanupperiod"))
    except ValueError, TypeError:
        log.w("Не удалось очистить папку с резервными копиями: не удалось получить настройки хранения")
        return False
    minumum_date = QDate().currentDate().addDays(-cleanup_period)
    filenames: list[str] = [item.name for item in Path(backup_foldername).iterdir() if item.is_file()]
    for fname in filenames:
        try:
            date_substring: str = fname[7:15]
        except IndexError:
            continue
        filedate: QDate = QDate.fromString(date_substring, "yyyyMMdd")
        if not filedate.isValid():
            continue
        if filedate < minumum_date:
            Path(os.path.join(backup_foldername, fname)).unlink(missing_ok=True)
    return True
