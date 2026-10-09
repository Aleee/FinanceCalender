import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import lovely_logger as log
from PySide6.QtCore import QByteArray, QEventLoop, QFile, QIODevice, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from base.sync import NetworkError, SyncError

CONNECT_TIMEOUT_MS = 1500
RESPONSE_TIMEOUT_MS = 4000
UPLOAD_EXTRA_MS_PER_MB = 10000
MAX_ATTEMPTS = 4
RETRY_PAUSE_MS = 200
RETRY_METHODS = ("GET", "PUT")


class ConnectStageError(NetworkError):
    pass


@dataclass
class HttpResponse:
    status: int
    body: bytes


class HttpClient(ABC):
    @abstractmethod
    def send(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
             upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        ...

    @abstractmethod
    def pause(self, milliseconds: int) -> None:
        ...


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


class QtHttpClient(HttpClient):
    def __init__(self):
        self.manager: QNetworkAccessManager = QNetworkAccessManager()
        self.manager.setRedirectPolicy(QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)

    def send(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
             upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        qurl = QUrl(url)
        target = f"{method} {qurl.host()}{qurl.path()}"
        failures: list[str] = []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.monotonic()
            try:
                response = self.send_once(method, url, headers, data, upload_file, download_file)
            except NetworkError as e:
                failures.append(f"{target}: попытка {attempt}/{MAX_ATTEMPTS} не удалась за {elapsed_ms(started)} мс: {e}")
                if attempt == MAX_ATTEMPTS or not (isinstance(e, ConnectStageError) or method in RETRY_METHODS):
                    for failure in failures:
                        log.d(failure)
                    raise
                self.manager.clearConnectionCache()
                self.pause(RETRY_PAUSE_MS)
                continue
            log.d(f"{target}: статус {response.status} за {elapsed_ms(started)} мс, попытка {attempt}/{MAX_ATTEMPTS}")
            return response

    def send_once(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
                  upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        request = QNetworkRequest(QUrl(url))
        for name, value in (headers or {}).items():
            request.setRawHeader(QByteArray(name.encode("ascii")), QByteArray(value.encode("utf-8")))
        verb = QByteArray(method.encode("ascii"))

        upload: QFile | None = None
        try:
            if upload_file is not None:
                upload = QFile(str(upload_file))
                if not upload.open(QIODevice.OpenModeFlag.ReadOnly):
                    raise SyncError(f"Не удалось открыть файл {upload_file}: {upload.errorString()}")
                body, size = upload, upload.size()
            else:
                body, size = QByteArray(data), len(data)
            request.setTransferTimeout(RESPONSE_TIMEOUT_MS + size * UPLOAD_EXTRA_MS_PER_MB // 1_000_000)
            reply = self.manager.sendCustomRequest(request, verb, body)
            stage = self.wait_for_reply(reply)
            try:
                response = self.read_response(reply)
            except NetworkError as e:
                if stage == "request":
                    raise
                text = "Нет связи с сервером: превышено время подключения" if stage == "timeout" else str(e)
                raise ConnectStageError(text) from e
        finally:
            if upload is not None:
                upload.close()
        if download_file is not None and response.status == 200:
            try:
                download_file.write_bytes(response.body)
            except OSError as e:
                raise SyncError(f"Не удалось записать файл {download_file}: {e}") from e
            return HttpResponse(response.status, b"")
        return response

    @staticmethod
    def wait_for_reply(reply: QNetworkReply) -> str:
        stage = "request"

        def on_connecting():
            nonlocal stage
            stage = "connect"
            connect_timer.start(CONNECT_TIMEOUT_MS)

        def on_connected():
            nonlocal stage
            if stage == "connect":
                stage = "request"
                connect_timer.stop()

        def on_connect_timeout():
            nonlocal stage
            stage = "timeout"
            reply.abort()

        connect_timer = QTimer()
        connect_timer.setSingleShot(True)
        connect_timer.timeout.connect(on_connect_timeout)
        reply.socketStartedConnecting.connect(on_connecting)
        for signal in (reply.encrypted, reply.requestSent, reply.metaDataChanged):
            signal.connect(on_connected)
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        connect_timer.stop()
        return stage

    @staticmethod
    def read_response(reply: QNetworkReply) -> HttpResponse:
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error, error_text = reply.error(), reply.errorString()
        body = bytes(reply.readAll()) if reply.isOpen() else b""
        reply.deleteLater()
        if status is None:
            raise NetworkError(f"Нет связи с сервером: {error_text}")
        if status < 400 and error != QNetworkReply.NetworkError.NoError:
            raise NetworkError(f"Передача данных прервана: {error_text}")
        return HttpResponse(int(status), body)

    def pause(self, milliseconds: int) -> None:
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
