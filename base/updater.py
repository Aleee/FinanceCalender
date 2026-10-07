import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from typing import Optional

import lovely_logger as log
from PySide6.QtCore import QObject, QUrl, QUrlQuery, QFile, QIODevice, QDateTime, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from base.paths import app_dir, update_dir
from base.version import DB_VERSION, is_newer

API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
PUBLIC_KEY = "https://disk.yandex.by/d/-feulMjOLlZpoA"
VERSION_FILE = "version.json"
CHECK_TIMEOUT_MS = 10000
DOWNLOAD_TIMEOUT_MS = 30000
APP_EXE = "FinanceCalender.exe"
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


class UpdateError(Exception):
    pass


@dataclass
class UpdateInfo:
    version: str
    db_version: int
    file: str
    sha256: str
    notes: str

    @classmethod
    def from_json(cls, raw: bytes) -> "UpdateInfo":
        try:
            data = json.loads(raw.decode("utf-8-sig"))
            info = cls(version=str(data["version"]), db_version=int(data["db_version"]), file=str(data["file"]),
                       sha256=str(data["sha256"]).lower(), notes=str(data.get("notes", "")))
        except (ValueError, KeyError, TypeError) as e:
            raise UpdateError(f"Некорректный {VERSION_FILE}: {e!r}")
        if os.path.basename(info.file) != info.file or not info.file:
            raise UpdateError(f"Недопустимое имя файла обновления: {info.file!r}")
        return info


def new_dir() -> str:
    return os.path.join(update_dir(), "new")


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def launch_updater() -> None:
    updater_path = os.path.join(update_dir(), "updater.exe")
    try:
        shutil.copy2(os.path.join(new_dir(), "updater.exe"), updater_path)
        subprocess.Popen([updater_path, "--pid", str(os.getpid()), "--app-dir", app_dir(), "--new-dir", new_dir()],
                         cwd=update_dir(), close_fds=True, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    except OSError as e:
        log.x(f"Не удалось запустить {updater_path}: {e}")
        raise UpdateError("Не удалось запустить установку обновления.")


def create_manager(parent: QObject) -> QNetworkAccessManager:
    manager = QNetworkAccessManager(parent)
    manager.setRedirectPolicy(QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
    return manager


def request_download_link(manager: QNetworkAccessManager, file_name: str, timeout_ms: int) -> QNetworkReply:
    query = QUrlQuery()
    query.addQueryItem("public_key", PUBLIC_KEY)
    query.addQueryItem("path", "/" + file_name)
    url = QUrl(API_URL)
    url.setQuery(query)
    request = QNetworkRequest(url)
    request.setTransferTimeout(timeout_ms)
    return manager.get(request)


def read_download_link(reply: QNetworkReply) -> str:
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise UpdateError(f"Не удалось получить ссылку на скачивание: {reply.errorString()}")
    try:
        return str(json.loads(bytes(reply.readAll()).decode("utf-8"))["href"])
    except (ValueError, KeyError, TypeError) as e:
        raise UpdateError(f"Яндекс.Диск вернул неожиданный ответ: {e!r}")


class UpdateChecker(QObject):
    update_available = Signal(object)
    check_finished = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.manager: QNetworkAccessManager = create_manager(self)
        self.checking: bool = False
        self.last_check_time: Optional[QDateTime] = None
        self.last_check_result: str = ""
        self.last_check_status: str = ""

    def finish(self, result: str, status: str) -> None:
        self.checking = False
        self.last_check_time = QDateTime.currentDateTime()
        self.last_check_result = result
        self.last_check_status = status
        self.check_finished.emit()

    def check(self) -> None:
        if self.checking:
            return
        if not PUBLIC_KEY:
            self.finish("Проверка обновлений отключена", "Обновления: отключены")
            return
        self.checking = True
        reply = request_download_link(self.manager, VERSION_FILE, CHECK_TIMEOUT_MS)
        reply.finished.connect(lambda: self.on_link_received(reply))

    def on_link_received(self, reply: QNetworkReply) -> None:
        try:
            href = read_download_link(reply)
        except UpdateError as e:
            log.w(f"Проверка обновлений: {e}")
            self.finish("Не удалось проверить обновления (подробности в логе)", "Обновления: ошибка")
            return
        finally:
            reply.deleteLater()
        request = QNetworkRequest(QUrl(href))
        request.setTransferTimeout(CHECK_TIMEOUT_MS)
        file_reply = self.manager.get(request)
        file_reply.finished.connect(lambda: self.on_version_received(file_reply))

    def on_version_received(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise UpdateError(f"Не удалось скачать {VERSION_FILE}: {reply.errorString()}")
            info = UpdateInfo.from_json(bytes(reply.readAll()))
            if not is_newer(info.version):
                self.finish("Установлена актуальная версия", "Обновления: нет")
            elif info.db_version < DB_VERSION:
                log.w(f"Версия {info.version} требует более старой версии БД ({info.db_version}, у нас {DB_VERSION}), "
                      f"обновление не предлагается")
                self.finish(f"Доступна версия {info.version}, но она несовместима с текущей базой данных",
                            "Обновления: ошибка")
            else:
                self.finish(f"Доступно обновление {info.version}", f"Обновления: доступна {info.version}")
                self.update_available.emit(info)
        except (UpdateError, ValueError) as e:
            log.w(f"Проверка обновлений: {e}")
            self.finish("Не удалось проверить обновления (подробности в логе)", "Обновления: ошибка")
        finally:
            reply.deleteLater()


class UpdateDownloader(QObject):
    progress = Signal(int, int)
    ready = Signal(str)
    failed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.manager: QNetworkAccessManager = create_manager(self)
        self.reply: Optional[QNetworkReply] = None
        self.file: Optional[QFile] = None
        self.info: Optional[UpdateInfo] = None
        self.cancelled: bool = False

    def start(self, info: UpdateInfo) -> None:
        self.info = info
        self.cancelled = False
        try:
            self.prepare_update_dir()
        except OSError as e:
            log.x(f"Не удалось подготовить папку {update_dir()}: {e}")
            self.failed.emit("Не удалось записать файлы в папку программы. "
                             "Возможно, флешка защищена от записи или закончилось место.")
            return
        reply = request_download_link(self.manager, info.file, CHECK_TIMEOUT_MS)
        reply.finished.connect(lambda: self.on_link_received(reply))

    def cancel(self) -> None:
        self.cancelled = True
        if self.reply is not None:
            self.reply.abort()

    @staticmethod
    def prepare_update_dir() -> None:
        shutil.rmtree(update_dir(), ignore_errors=True)
        os.makedirs(update_dir(), exist_ok=True)
        test_path = os.path.join(update_dir(), "write_test.tmp")
        with open(test_path, "w") as test_file:
            test_file.write("test")
        os.remove(test_path)

    def zip_path(self) -> str:
        return os.path.join(update_dir(), self.info.file)

    def on_link_received(self, reply: QNetworkReply) -> None:
        if self.cancelled:
            reply.deleteLater()
            return
        try:
            href = read_download_link(reply)
        except UpdateError as e:
            log.w(f"Скачивание обновления: {e}")
            self.failed.emit("Не удалось связаться с Яндекс.Диском. Проверьте подключение к интернету.")
            return
        finally:
            reply.deleteLater()

        self.file = QFile(self.zip_path())
        if not self.file.open(QIODevice.OpenModeFlag.WriteOnly):
            log.e(f"Не удалось открыть {self.zip_path()} для записи: {self.file.errorString()}")
            self.failed.emit("Не удалось записать файл обновления в папку программы.")
            return
        request = QNetworkRequest(QUrl(href))
        request.setTransferTimeout(DOWNLOAD_TIMEOUT_MS)
        self.reply = self.manager.get(request)
        self.reply.readyRead.connect(self.on_ready_read)
        self.reply.downloadProgress.connect(lambda received, total: self.progress.emit(received, total))
        self.reply.finished.connect(self.on_download_finished)

    def on_ready_read(self) -> None:
        self.file.write(self.reply.readAll())

    def on_download_finished(self) -> None:
        reply, self.reply = self.reply, None
        self.file.write(reply.readAll())
        self.file.close()
        error, error_text = reply.error(), reply.errorString()
        reply.deleteLater()
        if self.cancelled:
            return
        if error != QNetworkReply.NetworkError.NoError:
            log.w(f"Ошибка скачивания обновления: {error_text}")
            self.failed.emit("Не удалось скачать обновление. Проверьте подключение к интернету.")
            return
        try:
            self.verify_and_extract()
        except UpdateError as e:
            log.x(f"Обновление не подготовлено: {e}")
            self.failed.emit(str(e))
            return
        except OSError as e:
            log.x(f"Ошибка при распаковке обновления: {e}")
            self.failed.emit("Не удалось распаковать обновление. Возможно, на диске не хватает места.")
            return
        log.i(f"Обновление {self.info.version} скачано и распаковано в {new_dir()}")
        self.ready.emit(new_dir())

    def verify_and_extract(self) -> None:
        digest = hashlib.sha256()
        with open(self.zip_path(), "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != self.info.sha256:
            raise UpdateError("Скачанный файл повреждён (не совпала контрольная сумма). Попробуйте ещё раз.")
        try:
            with zipfile.ZipFile(self.zip_path()) as archive:
                archive.extractall(new_dir())
        except zipfile.BadZipFile:
            raise UpdateError("Архив с обновлением повреждён.")
        for name in (APP_EXE, "_internal", "updater.exe"):
            if not os.path.exists(os.path.join(new_dir(), name)):
                raise UpdateError(f"В архиве обновления нет {name}.")
        if os.path.exists(os.path.join(new_dir(), "data")):
            raise UpdateError("В архиве обновления есть папка data, установка отменена.")
