from datetime import date, datetime
from pathlib import Path
from platform import node

from base.dbhandler import DBHandler
from base.httpclient import QtHttpClient
from base.sync import (AuthError, FolderChannel, MasterInfo, MasterUpdatingError, NetworkError, SyncAction, SyncChannel,
                       SyncError, SyncParams, pull_master, push_master, save_conflict_copy)
from base.version import APP_VERSION
from base.yandexchannel import YandexDiskApiChannel
from gui.settings import SettingsHandler

SYNC_STALE_DAYS = 7
SYNC_RETRY_DELAY_MS = 30000
SYNC_RETRY_ATTEMPTS = 2
TOKEN_WARNING_DAYS = 30

SYNC_STATUS_TEXT: dict[SyncAction, str] = {
    SyncAction.NOTHING: "данные актуальны",
    SyncAction.PULL: "данные актуальны",
    SyncAction.PUSH: "данные актуальны",
    SyncAction.CONFLICT: "КОНФЛИКТ",
    SyncAction.NO_MASTER: "общей базы нет",
    SyncAction.FOREIGN_DB: "в общей базе другие данные",
    SyncAction.CLIENT_OUTDATED: "обновите программу",
}

SYNC_ACTION_MESSAGE: dict[SyncAction, str] = {
    SyncAction.CLIENT_OUTDATED: "Общая база создана более новой версией программы. Обновите программу. Ничего не изменено",
}

SYNC_PULL_MESSAGE = "Данные были изменены другим пользователем. Программа обновлена по актуальной версии"


def create_yandex_channel(token: str, disk_folder: str) -> YandexDiskApiChannel:
    return YandexDiskApiChannel(token, QtHttpClient(), disk_folder)


def create_sync_channel(settings_handler: SettingsHandler) -> SyncChannel:
    if settings_handler.sync_channel_type() == "yandex":
        return create_yandex_channel(settings_handler.sync_token(), settings_handler.sync_disk_folder())
    return FolderChannel(Path(settings_handler.sync_folder()))


def create_sync_params(settings_handler: SettingsHandler) -> SyncParams:
    return SyncParams(settings_handler.sync_author(), node(), APP_VERSION, settings_handler.sync_backup_keep_days())


def failure_status_text(error: SyncError) -> str:
    if isinstance(error, NetworkError):
        return "нет связи"
    if isinstance(error, AuthError):
        return "токен недействителен"
    if isinstance(error, MasterUpdatingError):
        return "общая база обновляется"
    return "ОШИБКА"


def token_days_left(settings_handler: SettingsHandler) -> int | None:
    if settings_handler.sync_channel_type() != "yandex":
        return None
    try:
        return (date.fromisoformat(settings_handler.sync_token_expires()) - date.today()).days
    except ValueError:
        return None


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
