from datetime import date, datetime
from pathlib import Path
from platform import node

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import QApplication

from base.dbhandler import DBHandler
from base.httpclient import QtHttpClient
from base.sync import (STAGE_COMPARE, STAGE_CONNECT, AuthError, FolderChannel, MasterInfo, MasterUpdatingError, NetworkError,
                       SyncAction, SyncCancelledError, SyncChannel, SyncError, SyncParams, SyncReport, collect_conflict_report,
                       pull_master, push_master, restore_master_info, save_conflict_copy)
from base.syncdiff import DbDiff, format_warnings
from base.version import APP_VERSION
from base.yandexchannel import YandexDiskApiChannel
from gui.settings import SettingsHandler

SYNC_STALE_DAYS = 7
SYNC_RETRY_DELAY_MS = 30000
SYNC_RETRY_ATTEMPTS = 2
TOKEN_WARNING_DAYS = 30
SYNC_PLANNED_STAGES = (STAGE_CONNECT, STAGE_COMPARE)
SYNC_STAGE_CHANGES_NOTICE = "Уведомление об изменениях"
SYNC_STAGE_CONFLICT_RESOLUTION = "Решение конфликта"

SYNC_STATUS_TEXT: dict[SyncAction, str] = {
    SyncAction.NOTHING: "данные актуальны",
    SyncAction.PULL: "данные актуальны",
    SyncAction.PUSH: "данные актуальны",
    SyncAction.MERGE: "данные актуальны",
    SyncAction.CONFLICT: "КОНФЛИКТ",
    SyncAction.NO_MASTER: "общей базы нет",
    SyncAction.FOREIGN_DB: "в общей базе другие данные",
    SyncAction.CLIENT_OUTDATED: "обновите программу",
}

SYNC_ACTION_MESSAGE: dict[SyncAction, str] = {
    SyncAction.CLIENT_OUTDATED: "Общая база создана более новой версией программы. Обновите программу. Ничего не изменено",
}

SYNC_PULL_MESSAGE = "Данные были изменены другим пользователем. Программа обновлена по актуальной версии"


class IdleSyncTimer(QTimer):
    USER_INPUT_EVENTS = (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseMove,
                         QEvent.Type.Wheel, QEvent.Type.KeyPress)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSingleShot(True)
        self.idle_enabled: bool = False
        QApplication.instance().installEventFilter(self)

    def set_idle_seconds(self, seconds: int) -> None:
        self.stop()
        self.setInterval(seconds * 1000)
        self.idle_enabled = seconds > 0
        if self.idle_enabled:
            self.start()

    def eventFilter(self, watched, event) -> bool:
        if self.idle_enabled and event.type() in self.USER_INPUT_EVENTS:
            self.start()
        return False


def create_yandex_channel(token: str, disk_folder: str) -> YandexDiskApiChannel:
    return YandexDiskApiChannel(token, QtHttpClient(), disk_folder)


def create_sync_channel(settings_handler: SettingsHandler) -> SyncChannel:
    if settings_handler.sync_channel_type() == "yandex":
        return create_yandex_channel(settings_handler.sync_token(), settings_handler.sync_disk_folder())
    return FolderChannel(Path(settings_handler.sync_folder()))


def create_sync_params(settings_handler: SettingsHandler) -> SyncParams:
    return SyncParams(settings_handler.sync_author(), node(), APP_VERSION, settings_handler.sync_long_backup_keep_days(),
                      settings_handler.sync_backup_interval_minutes())


def failure_status_text(error: SyncError) -> str:
    if isinstance(error, SyncCancelledError):
        return "прервана"
    if isinstance(error, NetworkError):
        return "нет связи"
    if isinstance(error, AuthError):
        return "токен недействителен"
    if isinstance(error, MasterUpdatingError):
        return "общая база обновляется"
    return "ошибка"


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
    pull_master(dbh, channel, (SyncAction.CONFLICT, SyncAction.PUSH))
    return SyncAction.PULL


def overwrite_master(dbh: DBHandler, channel: SyncChannel, params: SyncParams) -> SyncAction:
    save_conflict_copy(dbh)
    push_master(dbh, channel, params, overwrite=True)
    return SyncAction.PUSH


def restore_master(dbh: DBHandler, channel: SyncChannel, params: SyncParams) -> SyncAction:
    restore_master_info(dbh, channel, params)
    return SyncAction.NOTHING


def compare_with_master(dbh: DBHandler, channel: SyncChannel, report: SyncReport) -> SyncAction:
    collect_conflict_report(dbh, channel, report)
    return SyncAction.CONFLICT


def pull_message(info: MasterInfo | None) -> str:
    text: str = SYNC_PULL_MESSAGE
    if info is not None:
        text += f".\n\nОбщая база обновлена: {describe_master(info)}"
    return text


def pull_tabs(report: SyncReport) -> list[tuple[str, DbDiff | None]]:
    return [("Изменения другого пользователя", report.their_changes)]


def merge_tabs(report: SyncReport) -> list[tuple[str, DbDiff | None]]:
    return pull_tabs(report) + [("Ваши изменения", report.my_changes)]


def conflict_tabs(report: SyncReport) -> list[tuple[str, DbDiff | None]]:
    return [("Ваши изменения", report.my_changes), ("Изменения в общей базе", report.their_changes)]


def merge_warning_lines(report: SyncReport) -> list[str]:
    return [] if report.warnings is None else format_warnings(report.warnings)


def merge_message(report: SyncReport) -> str:
    text: str = "Пока вы работали, общая база была изменена другим пользователем"
    if report.master_info is not None:
        text += f" ({describe_master(report.master_info)})"
    text += ". Ваши изменения объединены с ними"
    text += " и отправлены в общую базу." if report.merge_pushed else ". Они будут отправлены при следующей синхронизации."
    return text


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
