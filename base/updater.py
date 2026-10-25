import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from typing import Optional

import lovely_logger as log
from PySide6.QtCore import QObject, QUrl, QUrlQuery, QFile, QIODevice, QDateTime, QTimer, Signal
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply, QNetworkRequest, QNetworkProxy,
                               QSslSocket)

from base.edition import is_viewer
from base.httpclient import MAX_ATTEMPTS, RESPONSE_TIMEOUT_MS, RETRY_PAUSE_MS
from base.macupdate import APP_BUNDLE, install_location_problem, launch_mac_updater
from base.paths import app_dir, update_dir
from base.version import DB_VERSION, is_newer

API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
PUBLIC_KEY = "https://disk.yandex.by/d/-feulMjOLlZpoA"
if is_viewer():
    VERSION_FILE = "version-viewer.json"
elif sys.platform == "darwin":
    VERSION_FILE = f"version-mac-{platform.machine()}.json"
else:
    VERSION_FILE = "version.json"
CHECK_TIMEOUT_MS = RESPONSE_TIMEOUT_MS
DOWNLOAD_TIMEOUT_MS = 90000
NETWORK_ATTEMPTS = 3
RETRY_DELAY_MS = 3000
CHECK_ATTEMPTS = MAX_ATTEMPTS
CHECK_RETRY_DELAY_MS = RETRY_PAUSE_MS
APP_EXE = "FinanceCalenderViewer.exe" if is_viewer() else "FinanceCalender.exe"
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
DIAG_HOSTS = ("cloud-api.yandex.net", "downloader.disk.yandex.ru", "api.github.com")
INTERNET_SETTINGS_KEY = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
PROXY_SETTINGS_SCRIPT = (f"Get-ItemProperty '{INTERNET_SETTINGS_KEY}' | "
                         f"Select-Object ProxyEnable,ProxyServer,ProxyOverride,AutoConfigURL | Format-List; "
                         f"'DefaultConnectionSettings flags: ' + "
                         f"(Get-ItemProperty '{INTERNET_SETTINGS_KEY}\\Connections').DefaultConnectionSettings[8]")
ANTIVIRUS_SCRIPT = ("Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | "
                    "Select-Object displayName,productState | Format-List")


class UpdateError(Exception):
    pass


class NetworkError(UpdateError):
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
            raise UpdateError(f"Некорректный {VERSION_FILE}: {e!r}") from e
        if os.path.basename(info.file) != info.file or not info.file:
            raise UpdateError(f"Недопустимое имя файла обновления: {info.file!r}")
        return info


def new_dir() -> str:
    return os.path.join(update_dir(), "new")


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def check_install_location() -> None:
    if sys.platform != "darwin":
        return
    problem = install_location_problem()
    if problem:
        raise UpdateError(problem)


def launch_updater() -> None:
    updater_path = os.path.join(update_dir(), "update.sh" if sys.platform == "darwin" else "updater.exe")
    try:
        if sys.platform == "darwin":
            launch_mac_updater(new_dir())
            return
        shutil.copy2(os.path.join(new_dir(), "updater.exe"), updater_path)
        subprocess.Popen([updater_path, "--pid", str(os.getpid()), "--app-dir", app_dir(), "--new-dir", new_dir(),
                          "--app-exe", APP_EXE],
                         cwd=update_dir(), close_fds=True, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    except OSError as e:
        log.x(f"Не удалось запустить {updater_path}: {e}")
        raise UpdateError("Не удалось запустить установку обновления.") from e


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


def describe_proxy(proxy: QNetworkProxy) -> str:
    return f"{proxy.type().name} {proxy.hostName()}:{proxy.port()}"


def read_download_link(reply: QNetworkReply) -> str:
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise NetworkError(f"Не удалось получить ссылку на скачивание: {reply.error().name}, {reply.errorString()}")
    try:
        return str(json.loads(bytes(reply.readAll()).decode("utf-8"))["href"])
    except (ValueError, KeyError, TypeError) as e:
        raise UpdateError(f"Яндекс.Диск вернул неожиданный ответ: {e!r}") from e


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
        self.attempt: int = 0

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
        self.attempt = 1
        log.i(f"Проверка обновлений: TLS-библиотека {QSslSocket.activeBackend()}")
        self.manager.clearConnectionCache()
        self.request_link()

    def request_link(self) -> None:
        reply = request_download_link(self.manager, VERSION_FILE, CHECK_TIMEOUT_MS)
        reply.finished.connect(lambda: self.on_link_received(reply))

    def on_failure(self, error: Exception) -> None:
        log.w(f"Проверка обновлений (попытка {self.attempt} из {CHECK_ATTEMPTS}): {error}")
        if isinstance(error, NetworkError):
            if self.attempt < CHECK_ATTEMPTS:
                self.attempt += 1
                self.manager.clearConnectionCache()
                QTimer.singleShot(CHECK_RETRY_DELAY_MS, self.request_link)
                return
        self.finish("Не удалось проверить обновления (подробности в логе)", "Обновления: ошибка")

    def on_link_received(self, reply: QNetworkReply) -> None:
        try:
            href = read_download_link(reply)
        except UpdateError as e:
            self.on_failure(e)
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
                raise NetworkError(f"Не удалось скачать {VERSION_FILE}: {reply.error().name}, {reply.errorString()}")
            info = UpdateInfo.from_json(bytes(reply.readAll()))
            if not is_newer(info.version):
                self.finish("Установлена актуальная версия", "Обновления: актуальная версия")
            elif info.db_version < DB_VERSION:
                log.w(f"Версия {info.version} требует более старой версии БД ({info.db_version}, у нас {DB_VERSION}), "
                      f"обновление не предлагается")
                self.finish(f"Доступна версия {info.version}, но она несовместима с текущей базой данных",
                            "Обновления: ошибка")
            else:
                self.finish(f"Доступно обновление {info.version}", f"Обновления: доступна {info.version}")
                self.update_available.emit(info)
        except (UpdateError, ValueError) as e:
            self.on_failure(e)
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
        self.write_failed: bool = False
        self.attempt: int = 0

    def start(self, info: UpdateInfo) -> None:
        self.info = info
        self.cancelled = False
        try:
            check_install_location()
        except UpdateError as e:
            self.failed.emit(str(e))
            return
        try:
            self.prepare_update_dir()
        except OSError as e:
            log.x(f"Не удалось подготовить папку {update_dir()}: {e}")
            self.failed.emit("Не удалось записать файлы в папку программы. "
                             "Возможно, флешка защищена от записи или закончилось место.")
            return
        self.attempt = 1
        self.request_link()

    def request_link(self) -> None:
        if self.cancelled:
            return
        reply = request_download_link(self.manager, self.info.file, CHECK_TIMEOUT_MS)
        reply.finished.connect(lambda: self.on_link_received(reply))

    def retry(self) -> bool:
        if self.attempt >= NETWORK_ATTEMPTS:
            return False
        self.attempt += 1
        QTimer.singleShot(RETRY_DELAY_MS, self.request_link)
        return True

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
            log.w(f"Скачивание обновления (попытка {self.attempt} из {NETWORK_ATTEMPTS}): {e}")
            if not (isinstance(e, NetworkError) and self.retry()):
                self.failed.emit("Не удалось связаться с Яндекс.Диском. Проверьте подключение к интернету.")
            return
        finally:
            reply.deleteLater()

        self.file = QFile(self.zip_path())
        self.write_failed = False
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

    def write_chunk(self, data) -> bool:
        if self.file.write(data) == len(data):
            return True
        log.e(f"Не удалось записать {self.zip_path()}: {self.file.errorString()}")
        self.write_failed = True
        return False

    def on_ready_read(self) -> None:
        if self.write_failed:
            return
        if not self.write_chunk(self.reply.readAll()):
            self.reply.abort()

    def on_download_finished(self) -> None:
        reply, self.reply = self.reply, None
        if not self.write_failed:
            self.write_chunk(reply.readAll())
        self.file.close()
        error, error_text = reply.error(), reply.errorString()
        reply.deleteLater()
        if self.cancelled:
            return
        if self.write_failed:
            self.failed.emit("Не удалось записать файл обновления. Возможно, на диске не хватает места.")
            return
        if error != QNetworkReply.NetworkError.NoError:
            log.w(f"Ошибка скачивания обновления (попытка {self.attempt} из {NETWORK_ATTEMPTS}): "
                  f"{error.name}, {error_text}")
            if not self.retry():
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
        mac = sys.platform == "darwin"
        try:
            if mac:
                subprocess.run(["ditto", "-x", "-k", self.zip_path(), new_dir()], check=True, capture_output=True)
            else:
                with zipfile.ZipFile(self.zip_path()) as archive:
                    archive.extractall(new_dir())
        except (zipfile.BadZipFile, subprocess.CalledProcessError) as e:
            raise UpdateError("Архив с обновлением повреждён.") from e
        for name in (APP_BUNDLE,) if mac else (APP_EXE, "_internal", "updater.exe"):
            if not os.path.exists(os.path.join(new_dir(), name)):
                raise UpdateError(f"В архиве обновления нет {name}.")
        data_path = os.path.join(new_dir(), APP_BUNDLE, "Contents", "MacOS", "data") if mac \
            else os.path.join(new_dir(), "data")
        if os.path.exists(data_path):
            raise UpdateError("В архиве обновления есть папка data, установка отменена.")
