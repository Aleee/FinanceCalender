import hashlib
import json
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import lovely_logger as log

from base.backup import replace_db_file
from base.paths import backup_dir

if TYPE_CHECKING:
    from base.dbhandler import DBHandler

MASTER_DB_NAME = "master.db"
MASTER_INFO_NAME = "master.json"
MASTER_BACKUPS_DIR = "master_backups"
BACKUP_TIME_FORMAT = "%Y%m%d-%H%M%S"
BACKUP_PREFIX = "master_"
TEMP_SUFFIX = ".tmp"
STATE_KEYS = ("db_uuid", "sync_token", "db_version", "change_counter")


class SyncError(Exception):
    pass


class MasterChangedError(SyncError):
    pass


class MasterUpdatingError(SyncError):
    pass


class SyncAction(Enum):
    NOTHING = "nothing"
    PULL = "pull"
    PUSH = "push"
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
    def remove_old_backups(self, keep_days: int) -> None:
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
            raise SyncError(f"Файл мастера не найден: {self.master_db_path}")
        try:
            shutil.copyfile(self.master_db_path, destination)
        except OSError as e:
            raise SyncError(f"Не удалось скопировать мастер: {e}") from e
        if file_md5(destination) != file_md5(self.master_db_path):
            raise SyncError("Скопированный файл мастера не совпадает с исходным")

    def upload_master(self, source: Path, info: MasterInfo) -> None:
        temp_db_path = self.master_db_path.with_name(MASTER_DB_NAME + TEMP_SUFFIX)
        temp_info_path = self.master_info_path.with_name(MASTER_INFO_NAME + TEMP_SUFFIX)
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, temp_db_path)
            if file_md5(temp_db_path) != file_md5(source):
                raise SyncError("Загруженный файл мастера не совпадает с исходным")
            os.replace(temp_db_path, self.master_db_path)
            temp_info_path.write_text(info.to_json(), encoding="utf-8")
            os.replace(temp_info_path, self.master_info_path)
        except OSError as e:
            raise SyncError(f"Не удалось записать мастер в {self.folder}: {e}") from e
        finally:
            temp_db_path.unlink(missing_ok=True)
            temp_info_path.unlink(missing_ok=True)

    def backup_master(self) -> None:
        if not self.master_db_path.is_file():
            return
        backup_name = f"{BACKUP_PREFIX}{datetime.now().strftime(BACKUP_TIME_FORMAT)}.db"
        try:
            self.backups_path.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.master_db_path, self.backups_path / backup_name)
        except OSError as e:
            raise SyncError(f"Не удалось сохранить копию прежнего мастера: {e}") from e

    def remove_old_backups(self, keep_days: int) -> None:
        if not self.backups_path.is_dir():
            return
        minimum_time = datetime.now() - timedelta(days=keep_days)
        try:
            for item in self.backups_path.iterdir():
                backup_time = backup_time_from_name(item.name)
                if backup_time is not None and backup_time < minimum_time:
                    item.unlink(missing_ok=True)
        except OSError as e:
            raise SyncError(f"Не удалось удалить старые копии мастера: {e}") from e


def backup_time_from_name(name: str) -> datetime | None:
    if not (name.startswith(BACKUP_PREFIX) and name.endswith(".db")):
        return None
    try:
        return datetime.strptime(name[len(BACKUP_PREFIX):-len(".db")], BACKUP_TIME_FORMAT)
    except ValueError:
        return None


@dataclass
class SyncParams:
    author: str
    machine: str
    app_version: str
    backup_keep_days: int = 30


def master_token(master: MasterInfo | None) -> str | None:
    return None if master is None else master.sync_token


def push_master(dbh: "DBHandler", channel: SyncChannel, params: SyncParams, overwrite: bool = False) -> None:
    local = read_local_state(dbh)
    master = channel.read_master_info()
    action = decide_action(local, master)
    allowed = {SyncAction.PUSH, SyncAction.NO_MASTER} | ({SyncAction.CONFLICT} if overwrite else set())
    if action not in allowed:
        raise SyncError(f"Отправка невозможна в состоянии «{action.value}»")
    new_token = uuid4().hex
    with tempfile.TemporaryDirectory() as folder:
        snapshot = Path(folder) / MASTER_DB_NAME
        counter = dbh.create_sync_snapshot(str(snapshot), new_token)
        if counter is None or not dbh.check_file_integrity(str(snapshot)):
            raise SyncError("Не удалось подготовить снимок базы данных для отправки")
        if master_token(channel.read_master_info()) != master_token(master):
            raise MasterChangedError("Мастер изменился во время подготовки отправки")
        info = MasterInfo(local.db_uuid, new_token, local.db_version, params.author, params.machine,
                          datetime.now().isoformat(timespec="seconds"), params.app_version)
        channel.backup_master()
        channel.upload_master(snapshot, info)
    try:
        channel.remove_old_backups(params.backup_keep_days)
    except SyncError as e:
        log.w(f"Не удалось удалить старые копии мастера: {e}")
    if not dbh.finish_push(new_token, counter):
        raise SyncError("Мастер обновлён, но не удалось записать результат в локальную базу данных (подробности см. в логе)")
    log.i(f"Мастер обновлён локальной базой данных, токен {new_token}")


def pull_master(dbh: "DBHandler", channel: SyncChannel, allowed: tuple[SyncAction, ...] = (SyncAction.PULL,)) -> None:
    local = read_local_state(dbh)
    master = channel.read_master_info()
    action = decide_action(local, master)
    if action not in allowed:
        raise SyncError(f"Подтягивание невозможно в состоянии «{action.value}»")
    with tempfile.TemporaryDirectory() as folder:
        downloaded = Path(folder) / MASTER_DB_NAME
        channel.download_master(downloaded)
        downloaded_state = read_file_state(dbh, downloaded)
        if downloaded_state.sync_token != master.sync_token:
            raise MasterUpdatingError("Мастер обновляется: файл базы данных и master.json не совпадают, повторите позже")
        if downloaded_state.db_uuid != master.db_uuid or downloaded_state.db_version != master.db_version:
            raise SyncError("Скачанный мастер не соответствует master.json")
        if not dbh.check_file_integrity(str(downloaded)):
            raise SyncError("Скачанный мастер не прошёл проверку целостности")
        new_file = downloaded
        migrated_path: str | None = None
        if downloaded_state.db_version < dbh.DB_VERSION:
            migrated_path = dbh.make_migrated_copy(str(downloaded))
            if migrated_path is None:
                raise SyncError("Не удалось обновить структуру скачанного мастера (подробности см. в логе)")
            new_file = Path(migrated_path)
        local_copy = Path(backup_dir()) / f"before_sync_{datetime.now().strftime(BACKUP_TIME_FORMAT + '-%f')}.db"
        try:
            if not dbh.copy_db_file(str(local_copy)):
                raise SyncError("Не удалось сохранить копию локальной базы данных перед заменой")
            if not replace_db_file(dbh, str(new_file)):
                raise SyncError("Не удалось заменить локальную базу данных мастером (подробности см. в логе)")
        finally:
            if migrated_path is not None:
                Path(migrated_path).unlink(missing_ok=True)
    log.i(f"Локальная база данных заменена мастером, токен {master.sync_token}")


def save_conflict_copy(dbh: "DBHandler") -> None:
    copy_path = Path(backup_dir()) / f"conflict_{datetime.now().strftime(BACKUP_TIME_FORMAT + '-%f')}.db"
    if not dbh.copy_db_file(str(copy_path)):
        raise SyncError("Не удалось сохранить копию локальной базы данных перед разрешением конфликта")


def synchronize(dbh: "DBHandler", channel: SyncChannel, params: SyncParams) -> SyncAction:
    action = decide_action(read_local_state(dbh), channel.read_master_info())
    if action == SyncAction.PULL:
        pull_master(dbh, channel)
    elif action == SyncAction.PUSH:
        push_master(dbh, channel, params)
    return action
