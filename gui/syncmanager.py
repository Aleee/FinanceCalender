from datetime import datetime
from pathlib import Path
from platform import node

from base.sync import FolderChannel, MasterInfo, SyncAction, SyncParams
from base.version import APP_VERSION
from gui.settings import SettingsHandler

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
    SyncAction.CONFLICT: "Изменения есть и в вашей базе данных, и в мастере. Автоматически объединить их нельзя, "
                         "поэтому ничего не изменено",
    SyncAction.NO_MASTER: "В папке обмена нет мастера. Ничего не изменено",
    SyncAction.FOREIGN_DB: "Мастер в папке обмена относится к другой базе данных. Ничего не изменено",
    SyncAction.CLIENT_OUTDATED: "Мастер создан более новой версией программы. Обновите программу. Ничего не изменено",
}


def create_sync_channel(settings_handler: SettingsHandler) -> FolderChannel:
    return FolderChannel(Path(settings_handler.sync_folder()))


def create_sync_params(settings_handler: SettingsHandler) -> SyncParams:
    return SyncParams(settings_handler.sync_author(), node(), APP_VERSION, settings_handler.sync_backup_keep_days())


def describe_master(info: MasterInfo) -> str:
    try:
        uploaded_at: str = datetime.fromisoformat(info.uploaded_at).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        uploaded_at = info.uploaded_at
    return f"{uploaded_at}, {info.author} ({info.machine})"
