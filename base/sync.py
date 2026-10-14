import hashlib
import json
import os
import shutil
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

import lovely_logger as log

from base.backup import replace_db_file
from base.paths import backup_dir, sync_base_path
from base.syncdiff import Conflict, DbDiff, MergeWarnings, plan_merge

if TYPE_CHECKING:
    from base.dbhandler import DBHandler

MASTER_DB_NAME = "master.db"
MASTER_INFO_NAME = "master.json"
MASTER_BACKUPS_DIR = "master_backups"
MASTER_LONG_BACKUPS_DIR = "master_backups_long"
SHORT_BACKUPS_KEEP_DAYS = 3
BACKUP_TIME_FORMAT = "%Y%m%d-%H%M%S"
PRECISE_BACKUP_TIME_FORMAT = BACKUP_TIME_FORMAT + "-%f"
BACKUP_PREFIX = "master_"
TEMP_SUFFIX = ".tmp"
STATE_KEYS = ("db_uuid", "sync_token", "db_version", "change_counter")

STAGE_CONNECT = "Подключение к общей базе"
STAGE_COMPARE = "Сверка версий"
STAGE_DOWNLOAD = "Скачивание общей базы"
STAGE_CHECK = "Проверка скачанной базы"
STAGE_APPLY = "Обновление локальной копии"
STAGE_SNAPSHOT = "Подготовка базы к отправке"
STAGE_BACKUP = "Сохранение резервной копии"
STAGE_UPLOAD = "Отправка базы"
STAGE_ANALYZE = "Анализ ваших изменений"
STAGE_COMPARE_CHANGES = "Сравнение изменений"
STAGE_MERGE = "Объединение изменений"

stage_listener: Callable[[str], None] | None = None


def set_stage_listener(listener: Callable[[str], None] | None) -> None:
    global stage_listener
    stage_listener = listener


def report_stage(text: str) -> None:
    if stage_listener is not None:
        stage_listener(text)


class SyncError(Exception):
    pass


class NetworkError(SyncError):
    pass


class AuthError(SyncError):
    pass


class MasterChangedError(SyncError):
    pass


class MasterUpdatingError(SyncError):
    pass


class SyncAction(Enum):
    NOTHING = "nothing"
    PULL = "pull"
    PUSH = "push"
    MERGE = "merge"
    CONFLICT = "conflict"
    NO_MASTER = "no_master"
    FOREIGN_DB = "foreign_db"
    CLIENT_OUTDATED = "client_outdated"


@dataclass
class LocalState:
    db_uuid: str
    sync_token: str
    db_version: int
    change_counter: int

    @property
    def has_changes(self) -> bool:
        return self.change_counter > 0


@dataclass
class SyncReport:
    their_changes: DbDiff | None = None
    my_changes: DbDiff | None = None
    master_info: "MasterInfo | None" = None
    warnings: MergeWarnings | None = None
    conflicts: list[Conflict] = field(default_factory=list)
    merge_pushed: bool = False


@dataclass
class MasterInfo:
    db_uuid: str
    sync_token: str
    db_version: int
    author: str
    machine: str
    uploaded_at: str
    app_version: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "MasterInfo":
        try:
            return cls(**json.loads(text))
        except (ValueError, TypeError) as e:
            raise SyncError(f"Файл {MASTER_INFO_NAME} повреждён или имеет неизвестный формат: {e}") from e


def read_local_state(dbh: "DBHandler") -> LocalState:
    return state_from_values({key: dbh.get_setting(key, None) for key in STATE_KEYS})


def read_file_state(dbh: "DBHandler", path: Path) -> LocalState:
    values = dbh.read_file_settings(str(path), STATE_KEYS)
    if values is None:
        raise SyncError(f"Не удалось прочитать служебные ключи синхронизации из файла {path}")
    return state_from_values(values)


def state_from_values(values: dict[str, str | None]) -> LocalState:
    missing = [key for key, value in values.items() if value is None]
    if missing:
        raise SyncError(f"В базе данных нет служебных ключей синхронизации: {', '.join(missing)}")
    try:
        return LocalState(values["db_uuid"], values["sync_token"], int(values["db_version"]), int(values["change_counter"]))
    except ValueError as e:
        raise SyncError(f"Служебные ключи синхронизации содержат недопустимые значения: {e}") from e


def decide_action(local: LocalState, master: MasterInfo | None) -> SyncAction:
    if master is None:
        return SyncAction.NO_MASTER
    if master.db_uuid != local.db_uuid:
        return SyncAction.FOREIGN_DB
    if master.db_version > local.db_version:
        return SyncAction.CLIENT_OUTDATED
    master_changed = master.sync_token != local.sync_token
    if master_changed and local.has_changes:
        return SyncAction.CONFLICT
    if master_changed:
        return SyncAction.PULL
    if local.has_changes:
        return SyncAction.PUSH
    return SyncAction.NOTHING


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SyncChannel(ABC):
    @abstractmethod
    def read_master_info(self) -> MasterInfo | None:
        ...

    def last_master_info(self) -> MasterInfo | None:
        return self.read_master_info()

    @abstractmethod
    def download_master(self, destination: Path) -> None:
        ...

    @abstractmethod
    def upload_master(self, source: Path, info: MasterInfo) -> None:
        ...

    @abstractmethod
    def backup_master(self) -> None:
        ...

    @abstractmethod
    def remove_old_backups(self, long_keep_days: int) -> None:
        ...


class FolderChannel(SyncChannel):
    def __init__(self, folder: Path):
        self.folder: Path = Path(folder)

    @property
    def master_db_path(self) -> Path:
        return self.folder / MASTER_DB_NAME

    @property
    def master_info_path(self) -> Path:
        return self.folder / MASTER_INFO_NAME

    @property
    def backups_path(self) -> Path:
        return self.folder / MASTER_BACKUPS_DIR

    def read_master_info(self) -> MasterInfo | None:
        if not self.master_info_path.is_file():
            return None
        try:
            return MasterInfo.from_json(self.master_info_path.read_text(encoding="utf-8"))
        except OSError as e:
            raise SyncError(f"Не удалось прочитать {self.master_info_path}: {e}") from e

    def download_master(self, destination: Path) -> None:
        if not self.master_db_path.is_file():
            raise SyncError(f"Файл общей базы не найден: {self.master_db_path}")
        try:
            shutil.copyfile(self.master_db_path, destination)
        except OSError as e:
            raise SyncError(f"Не удалось скопировать общую базу: {e}") from e
        if file_md5(destination) != file_md5(self.master_db_path):
            raise SyncError("Скопированный файл общей базы не совпадает с исходным")

    def upload_master(self, source: Path, info: MasterInfo) -> None:
        temp_db_path = self.master_db_path.with_name(MASTER_DB_NAME + TEMP_SUFFIX)
        temp_info_path = self.master_info_path.with_name(MASTER_INFO_NAME + TEMP_SUFFIX)
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, temp_db_path)
            if file_md5(temp_db_path) != file_md5(source):
                raise SyncError("Загруженный файл общей базы не совпадает с исходным")
            os.replace(temp_db_path, self.master_db_path)
            temp_info_path.write_text(info.to_json(), encoding="utf-8")
            os.replace(temp_info_path, self.master_info_path)
        except OSError as e:
            raise SyncError(f"Не удалось записать общую базу в {self.folder}: {e}") from e
        finally:
            temp_db_path.unlink(missing_ok=True)
            temp_info_path.unlink(missing_ok=True)

    @property
    def long_backups_path(self) -> Path:
        return self.folder / MASTER_LONG_BACKUPS_DIR

    def backup_master(self) -> None:
        if not self.master_db_path.is_file():
            return
        backup_name = master_backup_name()
        try:
            self.backups_path.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.master_db_path, self.backups_path / backup_name)
            if not any(is_backup_of_today(name) for name in self.backup_names(self.long_backups_path)):
                self.long_backups_path.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.master_db_path, self.long_backups_path / backup_name)
        except OSError as e:
            raise SyncError(f"Не удалось сохранить копию прежней общей базы: {e}") from e

    @staticmethod
    def backup_names(folder: Path) -> list[str]:
        return [item.name for item in folder.iterdir()] if folder.is_dir() else []

    def remove_old_backups(self, long_keep_days: int) -> None:
        try:
            self.remove_old_backups_in(self.backups_path, SHORT_BACKUPS_KEEP_DAYS)
            self.remove_old_backups_in(self.long_backups_path, long_keep_days)
        except OSError as e:
            raise SyncError(f"Не удалось удалить старые копии общей базы: {e}") from e

    @staticmethod
    def remove_old_backups_in(folder: Path, keep_days: int) -> None:
        if not folder.is_dir():
            return
        minimum_time = datetime.now() - timedelta(days=keep_days)
        for item in folder.iterdir():
            backup_time = backup_time_from_name(item.name)
            if backup_time is not None and backup_time < minimum_time:
                item.unlink(missing_ok=True)


def master_backup_name() -> str:
    return f"{BACKUP_PREFIX}{datetime.now().strftime(PRECISE_BACKUP_TIME_FORMAT)}.db"


def backup_time_from_name(name: str) -> datetime | None:
    if not (name.startswith(BACKUP_PREFIX) and name.endswith(".db")):
        return None
    time_text = name[len(BACKUP_PREFIX):-len(".db")]
    for time_format in (PRECISE_BACKUP_TIME_FORMAT, BACKUP_TIME_FORMAT):
        try:
            return datetime.strptime(time_text, time_format)
        except ValueError:
            continue
    return None


def is_backup_of_today(name: str) -> bool:
    backup_time = backup_time_from_name(name)
    return backup_time is not None and backup_time.date() == datetime.now().date()


@dataclass
class SyncParams:
    author: str
    machine: str
    app_version: str
    long_backup_keep_days: int = 30
    backup_interval_minutes: int = 0


def master_token(master: MasterInfo | None) -> str | None:
    return None if master is None else master.sync_token


def master_has_token(channel: SyncChannel, token: str) -> bool:
    try:
        return master_token(channel.read_master_info()) == token
    except SyncError:
        return False


def backups_cleanup_due(previous_master: MasterInfo | None) -> bool:
    if previous_master is None:
        return True
    try:
        return datetime.fromisoformat(previous_master.uploaded_at).date() < datetime.now().date()
    except ValueError:
        return True


def master_backup_due(previous_master: MasterInfo | None, interval_minutes: int) -> bool:
    if previous_master is None or interval_minutes <= 0:
        return True
    try:
        age: timedelta = datetime.now() - datetime.fromisoformat(previous_master.uploaded_at)
    except ValueError:
        return True
    return not timedelta(0) <= age < timedelta(minutes=interval_minutes)


def save_sync_base(source: Path) -> None:
    target = Path(sync_base_path())
    temp = target.with_name(target.name + TEMP_SUFFIX)
    try:
        shutil.copyfile(source, temp)
        os.replace(temp, target)
    except OSError as e:
        temp.unlink(missing_ok=True)
        log.w(f"Не удалось сохранить базу для сравнения при конфликтах: {e}")


def find_sync_base(dbh: "DBHandler", local: LocalState) -> Path | None:
    path = Path(sync_base_path())
    if not path.is_file():
        return None
    values = dbh.read_file_settings(str(path), ("db_uuid", "sync_token"))
    if values is None or values["db_uuid"] != local.db_uuid or values["sync_token"] != local.sync_token:
        return None
    return path


def push_master(dbh: "DBHandler", channel: SyncChannel, params: SyncParams, overwrite: bool = False,
                master: MasterInfo | None = None) -> None:
    local = read_local_state(dbh)
    if master is None:
        report_stage(STAGE_CONNECT)
        master = channel.read_master_info()
    action = decide_action(local, master)
    allowed = {SyncAction.PUSH, SyncAction.NO_MASTER} | ({SyncAction.CONFLICT} if overwrite else set())
    if action not in allowed:
        raise SyncError(f"Отправка невозможна в состоянии «{action.value}»")
    report_stage(STAGE_SNAPSHOT)
    new_token = uuid4().hex
    with tempfile.TemporaryDirectory() as folder:
        snapshot = Path(folder) / MASTER_DB_NAME
        counter = dbh.create_sync_snapshot(str(snapshot), new_token)
        if counter is None or not dbh.check_file_integrity(str(snapshot)):
            raise SyncError("Не удалось подготовить снимок базы данных для отправки")
        if master_token(channel.read_master_info()) != master_token(master):
            raise MasterChangedError("Общая база изменилась во время подготовки отправки")
        info = MasterInfo(local.db_uuid, new_token, local.db_version, params.author, params.machine,
                          datetime.now().isoformat(timespec="seconds"), params.app_version)
        stage_started = time.monotonic()
        if overwrite or master_backup_due(master, params.backup_interval_minutes):
            report_stage(STAGE_BACKUP)
            channel.backup_master()
            log.d(f"Отправка общей базы: копия прежней общей базы за {elapsed_ms(stage_started)} мс")
        stage_started = time.monotonic()
        report_stage(STAGE_UPLOAD)
        try:
            channel.upload_master(snapshot, info)
        except SyncError as e:
            if not master_has_token(channel, new_token):
                raise
            log.w(f"Отправка завершилась ошибкой ({e}), но общая база уже обновлена")
        log.d(f"Отправка общей базы: загрузка за {elapsed_ms(stage_started)} мс")
        save_sync_base(snapshot)
    if backups_cleanup_due(master):
        try:
            channel.remove_old_backups(params.long_backup_keep_days)
        except SyncError as e:
            log.w(f"Не удалось удалить старые копии общей базы: {e}")
    if not dbh.finish_push(new_token, counter):
        raise SyncError("Общая база обновлена, но не удалось записать результат в локальную копию (подробности см. в логе)")


def download_checked_master(dbh: "DBHandler", channel: SyncChannel, master: MasterInfo, folder: str) -> tuple[Path, LocalState]:
    downloaded = Path(folder) / MASTER_DB_NAME
    report_stage(STAGE_DOWNLOAD)
    channel.download_master(downloaded)
    report_stage(STAGE_CHECK)
    downloaded_state = read_file_state(dbh, downloaded)
    if downloaded_state.sync_token != master.sync_token:
        raise MasterUpdatingError("Общая база обновляется: файл базы данных и master.json не совпадают, повторите позже")
    if downloaded_state.db_uuid != master.db_uuid or downloaded_state.db_version != master.db_version:
        raise SyncError("Скачанная общая база не соответствует master.json")
    if not dbh.check_file_integrity(str(downloaded)):
        raise SyncError("Скачанная общая база не прошла проверку целостности")
    return downloaded, downloaded_state


def fetch_master(dbh: "DBHandler", channel: SyncChannel) -> None:
    master = channel.read_master_info()
    if master is None:
        raise SyncError("В общем хранилище нет базы данных")
    if master.db_version > dbh.DB_VERSION:
        raise SyncError("Общая база создана более новой версией программы. Обновите программу")
    with tempfile.TemporaryDirectory() as folder:
        downloaded, downloaded_state = download_checked_master(dbh, channel, master, folder)
        new_file = downloaded
        migrated_path: str | None = None
        if downloaded_state.db_version < dbh.DB_VERSION:
            migrated_path = dbh.make_migrated_copy(str(downloaded))
            if migrated_path is None:
                raise SyncError("Не удалось обновить структуру скачанной общей базы (подробности см. в логе)")
            new_file = Path(migrated_path)
        try:
            if not dbh.switch_db_files(str(new_file), close_current_connection=True):
                raise SyncError("Не удалось сохранить скачанную общую базу (подробности см. в логе)")
        finally:
            if migrated_path is not None:
                Path(migrated_path).unlink(missing_ok=True)


def pull_master(dbh: "DBHandler", channel: SyncChannel, allowed: tuple[SyncAction, ...] = (SyncAction.PULL,),
                master: MasterInfo | None = None, report: SyncReport | None = None) -> None:
    local = read_local_state(dbh)
    if master is None:
        report_stage(STAGE_CONNECT)
        master = channel.read_master_info()
    action = decide_action(local, master)
    if action not in allowed:
        raise SyncError(f"Подтягивание невозможно в состоянии «{action.value}»")
    with tempfile.TemporaryDirectory() as folder:
        downloaded, downloaded_state = download_checked_master(dbh, channel, master, folder)
        report_stage(STAGE_APPLY)
        new_file = downloaded
        migrated_path: str | None = None
        if downloaded_state.db_version < dbh.DB_VERSION:
            migrated_path = dbh.make_migrated_copy(str(downloaded))
            if migrated_path is None:
                raise SyncError("Не удалось обновить структуру скачанной общей базы (подробности см. в логе)")
            new_file = Path(migrated_path)
        local_copy = Path(backup_dir()) / f"before_sync_{datetime.now().strftime(PRECISE_BACKUP_TIME_FORMAT)}.db"
        try:
            if not dbh.copy_db_file(str(local_copy)):
                raise SyncError("Не удалось сохранить локальную копию перед заменой")
            if report is not None and action == SyncAction.PULL:
                report.their_changes = dbh.read_db_diff(dbh.local_db_path(), str(new_file))
                report.master_info = master
            if not replace_db_file(dbh, str(new_file)):
                raise SyncError("Не удалось заменить локальную копию общей базой (подробности см. в логе)")
            save_sync_base(new_file)
        finally:
            if migrated_path is not None:
                Path(migrated_path).unlink(missing_ok=True)


def collect_conflict_report(dbh: "DBHandler", channel: SyncChannel, report: SyncReport) -> None:
    local = read_local_state(dbh)
    report_stage(STAGE_CONNECT)
    master = channel.read_master_info()
    base = find_sync_base(dbh, local)
    if base is None or decide_action(local, master) != SyncAction.CONFLICT:
        return
    with tempfile.TemporaryDirectory() as folder:
        downloaded, _ = download_checked_master(dbh, channel, master, folder)
        report_stage(STAGE_COMPARE_CHANGES)
        report.their_changes = dbh.read_db_diff(str(base), str(downloaded))
        report.my_changes = dbh.read_db_diff(str(base), dbh.local_db_path())
        if report.their_changes is not None and report.my_changes is not None:
            report.conflicts = plan_merge(report.my_changes, report.their_changes).conflicts


def merge_into_master(dbh: "DBHandler", channel: SyncChannel, master: MasterInfo, report: SyncReport) -> bool:
    local = read_local_state(dbh)
    base = find_sync_base(dbh, local)
    if base is None or master.db_version != local.db_version:
        return False
    report_stage(STAGE_ANALYZE)
    my_changes = dbh.read_db_diff(str(base), dbh.local_db_path())
    if my_changes is None or my_changes.other_tables:
        return False
    with tempfile.TemporaryDirectory() as folder:
        downloaded, _ = download_checked_master(dbh, channel, master, folder)
        report_stage(STAGE_MERGE)
        their_changes = dbh.read_db_diff(str(base), str(downloaded))
        if their_changes is None:
            return False
        plan = plan_merge(my_changes, their_changes)
        if plan.conflicts:
            report.their_changes, report.my_changes = their_changes, my_changes
            report.master_info, report.conflicts = master, plan.conflicts
            return False
        merged = Path(folder) / "merged.db"
        shutil.copyfile(downloaded, merged)
        id_maps = dbh.apply_merge(str(merged), dbh.local_db_path(), plan, my_changes)
        if id_maps is None or not dbh.check_file_integrity(str(merged)):
            return False
        added = {table: list(id_map.values()) for table, id_map in id_maps.items()}
        changed_events = [new_row["id"] for _, new_row in my_changes.tables["event"].changed]
        changed_payments = [new_row["id"] for _, new_row in my_changes.tables["payment"].changed]
        warnings = dbh.find_merge_warnings(str(merged), added, added["event"] + changed_events, added["payment"] + changed_payments)
        save_conflict_copy(dbh)
        if not replace_db_file(dbh, str(merged)):
            raise SyncError("Не удалось заменить локальную копию объединённой базой (подробности см. в логе)")
        save_sync_base(downloaded)
    report.their_changes, report.my_changes, report.master_info, report.warnings = their_changes, my_changes, master, warnings
    return True


def save_conflict_copy(dbh: "DBHandler") -> None:
    copy_path = Path(backup_dir()) / f"conflict_{datetime.now().strftime(PRECISE_BACKUP_TIME_FORMAT)}.db"
    if not dbh.copy_db_file(str(copy_path)):
        raise SyncError("Не удалось сохранить локальную копию перед разрешением конфликта")


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def synchronize(dbh: "DBHandler", channel: SyncChannel, params: SyncParams, report: SyncReport | None = None,
                merge: bool = False) -> SyncAction:
    started = time.monotonic()
    report_stage(STAGE_CONNECT)
    master = channel.read_master_info()
    log.d(f"Синхронизация: чтение master.json за {elapsed_ms(started)} мс")
    report_stage(STAGE_COMPARE)
    action = decide_action(read_local_state(dbh), master)
    if action == SyncAction.PULL:
        pull_master(dbh, channel, master=master, report=report)
    elif action == SyncAction.PUSH:
        push_master(dbh, channel, params, master=master)
    elif action == SyncAction.CONFLICT and merge:
        report = report or SyncReport()
        if merge_into_master(dbh, channel, master, report):
            action = SyncAction.MERGE
            try:
                if read_local_state(dbh).has_changes:
                    push_master(dbh, channel, params, master=master)
                report.merge_pushed = True
            except SyncError as e:
                log.w(f"Объединённая база не отправлена, отправка будет повторена: {e}")
    log.d(f"Синхронизация: действие «{action.value}», всего {elapsed_ms(started)} мс")
    return action
