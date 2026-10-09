from datetime import datetime
from pathlib import Path
from platform import node

from base.dbhandler import DBHandler
from base.sync import (FolderChannel, MasterInfo, SyncAction, SyncChannel, SyncParams, pull_master, push_master,
                       save_conflict_copy)
from base.version import APP_VERSION
from gui.settings import SettingsHandler

SYNC_STALE_DAYS = 7

SYNC_STATUS_TEXT: dict[SyncAction, str] = {
    SyncAction.NOTHING: "актуально",
    SyncAction.PULL: "получены изменения",
    SyncAction.PUSH: "изменения отправлены",
    SyncAction.CONFLICT: "КОНФЛИКТ",
    SyncAction.NO_MASTER: "мастера нет",
    SyncAction.FOREIGN_DB: "другая база данных",
    SyncAction.CLIENT_OUTDATED: "обновите программу",
}

SYNC_ACTION_MESSAGE: dict[SyncAction, str] = {
    SyncAction.CLIENT_OUTDATED: "Мастер создан более новой версией программы. Обновите программу. Ничего не изменено",
}


def create_sync_channel(settings_handler: SettingsHandler) -> FolderChannel:
    return FolderChannel(Path(settings_handler.sync_folder()))


def create_sync_params(settings_handler: SettingsHandler) -> SyncParams:
    return SyncParams(settings_handler.sync_author(), node(), APP_VERSION, settings_handler.sync_backup_keep_days())


def create_master(dbh: DBHandler, channel: SyncChannel, params: SyncParams) -> SyncAction:
    push_master(dbh, channel, params)
    return SyncAction.PUSH


def connect_to_master(dbh: DBHandler, channel: SyncChannel) -> SyncAction:
    pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
    return SyncAction.PULL


def take_master(dbh: DBHandler, channel: SyncChannel) -> SyncAction:
    save_conflict_copy(dbh)
    pull_master(dbh, channel, (SyncAction.CONFLICT,))
    return SyncAction.PULL


def overwrite_master(dbh: DBHandler, channel: SyncChannel, params: SyncParams) -> SyncAction:
    save_conflict_copy(dbh)
    push_master(dbh, channel, params, overwrite=True)
    return SyncAction.PUSH


def describe_master(info: MasterInfo) -> str:
    try:
        uploaded_at: str = datetime.fromisoformat(info.uploaded_at).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        uploaded_at = info.uploaded_at
    return f"{uploaded_at}, {info.author} ({info.machine})"


def master_age_days(info: MasterInfo) -> int | None:
    try:
        return (datetime.now() - datetime.fromisoformat(info.uploaded_at)).days
    except ValueError:
        return None
