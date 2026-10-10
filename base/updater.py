import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from dataclasses import dataclass
from typing import Optional

import lovely_logger as log
from PySide6.QtCore import QObject, QUrl, QUrlQuery, QFile, QIODevice, QDateTime, QTimer, Signal
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply, QNetworkRequest, QNetworkProxy,
                               QNetworkProxyFactory, QNetworkProxyQuery, QSslSocket)

from base.paths import app_dir, update_dir
from base.version import APP_VERSION, DB_VERSION, is_newer

API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
PUBLIC_KEY = "https://disk.yandex.by/d/-feulMjOLlZpoA"
VERSION_FILE = "version.json"
CHECK_TIMEOUT_MS = 60000
DOWNLOAD_TIMEOUT_MS = 90000
NETWORK_ATTEMPTS = 3
RETRY_DELAY_MS = 3000
APP_EXE = "FinanceCalender.exe"
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
DIAG_HOSTS = ("cloud-api.yandex.net", "downloader.disk.yandex.ru", "api.github.com")
DIAG_TIMEOUT_MS = 8000
DIAG_COMMAND_TIMEOUT = 30
INTERNET_SETTINGS_KEY = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"


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


def describe_proxy(proxy: QNetworkProxy) -> str:
    return f"{proxy.type().name} {proxy.hostName()}:{proxy.port()}"


def probe_host(host: str, proxy: QNetworkProxy, label: str) -> None:
    socket = QSslSocket()
    socket.setProxy(proxy)
    start = time.monotonic()
    socket.connectToHost(host, 443)
    if not socket.waitForConnected(DIAG_TIMEOUT_MS):
        log.w(f"Диагностика [{label}] {host}: TCP не установлен за {(time.monotonic() - start) * 1000:.0f} мс: "
              f"{socket.error().name}, {socket.errorString()}")
        return
    tcp_ms = (time.monotonic() - start) * 1000
    socket.startClientEncryption()
    if not socket.waitForEncrypted(DIAG_TIMEOUT_MS):
        errors = [e.errorString() for e in socket.sslHandshakeErrors()]
        log.w(f"Диагностика [{label}] {host}: TCP за {tcp_ms:.0f} мс, TLS не завершён: "
              f"{socket.errorString()} {errors}")
        return
    log.i(f"Диагностика [{label}] {host}: TCP за {tcp_ms:.0f} мс, TLS ок за {(time.monotonic() - start) * 1000:.0f} мс")
    socket.disconnectFromHost()


def run_command(label: str, args: list[str]) -> None:
    try:
        result = subprocess.run(args, capture_output=True, stdin=subprocess.DEVNULL, timeout=DIAG_COMMAND_TIMEOUT,
                                creationflags=CREATE_NO_WINDOW, encoding="oem", errors="replace")
    except subprocess.TimeoutExpired:
        log.w(f"Диагностика, команда [{label}]: нет ответа за {DIAG_COMMAND_TIMEOUT} с")
        return
    except OSError as e:
        log.w(f"Диагностика, команда [{label}]: не удалось запустить: {e}")
        return
    output = (result.stdout + result.stderr).strip()
    log.i(f"Диагностика, команда [{label}], код {result.returncode}:\n{output[:4000]}")


def run_command_diagnostics() -> None:
    api_link = f"{API_URL}?public_key={PUBLIC_KEY}&path=/{VERSION_FILE}"
    curl = ["curl.exe", "-v", "-sS", "-m", "20", "-o", "NUL"]
    settings = (f"Get-ItemProperty '{INTERNET_SETTINGS_KEY}' | "
                f"Select-Object ProxyEnable,ProxyServer,ProxyOverride,AutoConfigURL | Format-List; "
                f"'DefaultConnectionSettings flags: ' + "
                f"(Get-ItemProperty '{INTERNET_SETTINGS_KEY}\\Connections').DefaultConnectionSettings[8]")
    antivirus = ("Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | "
                 "Select-Object displayName,productState | Format-List")
    proxy_vars = {name: os.environ[name] for name in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY")
                  if name in os.environ}
    log.i(f"Диагностика, переменные прокси: {proxy_vars}")
    run_command("curl API", curl + [api_link])
    run_command("curl API без прокси", curl + ["--noproxy", "*", api_link])
    run_command("curl GitHub", curl + ["https://api.github.com"])
    run_command("nslookup", ["nslookup", DIAG_HOSTS[0]])
    run_command("netsh winhttp", ["netsh", "winhttp", "show", "proxy"])
    run_command("настройки прокси", ["powershell", "-NoProfile", "-NonInteractive", "-Command", settings])
    run_command("антивирус", ["powershell", "-NoProfile", "-NonInteractive", "-Command", antivirus])


def run_network_diagnostics() -> None:
    log.i(f"Диагностика сети: версия {APP_VERSION}, SSL {QSslSocket.supportsSsl()} ({QSslSocket.activeBackend()}), "
          f"системные настройки прокси {QNetworkProxyFactory.usesSystemConfiguration()}")
    for host in DIAG_HOSTS:
        system_proxy = QNetworkProxyFactory.systemProxyForQuery(QNetworkProxyQuery(host, 443, "https"))[0]
        probe_host(host, QNetworkProxy(QNetworkProxy.ProxyType.NoProxy), "без прокси")
        probe_host(host, system_proxy, f"системный прокси: {describe_proxy(system_proxy)}")
    run_command_diagnostics()
    log.i("Диагностика сети завершена")


def read_download_link(reply: QNetworkReply) -> str:
    if reply.error() != QNetworkReply.NetworkError.NoError:
        raise NetworkError(f"Не удалось получить ссылку на скачивание: {reply.error().name}, {reply.errorString()}")
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
        self.request_link()

    def request_link(self) -> None:
        reply = request_download_link(self.manager, VERSION_FILE, CHECK_TIMEOUT_MS)
        reply.finished.connect(lambda: self.on_link_received(reply))

    def on_failure(self, error: Exception) -> None:
        log.w(f"Проверка обновлений (попытка {self.attempt} из {NETWORK_ATTEMPTS}): {error}")
        if isinstance(error, NetworkError):
            if self.attempt < NETWORK_ATTEMPTS:
                self.attempt += 1
                QTimer.singleShot(RETRY_DELAY_MS, self.request_link)
                return
            threading.Thread(target=run_network_diagnostics, daemon=True).start()
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
        self.attempt: int = 0

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
