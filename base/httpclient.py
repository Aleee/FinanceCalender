import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import lovely_logger as log
from PySide6.QtCore import QByteArray, QEventLoop, QFile, QIODevice, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from base.sync import NetworkError, SyncError

TIMEOUT_STEPS_MS = (1000, 1500, 2000, 2500, 3000)
RETRY_PAUSES_MS = (200, 300, 400, 500)
SINGLE_ATTEMPT_TIMEOUT_MS = 5000
RETRY_METHODS = ("GET", "PUT")


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
        steps = TIMEOUT_STEPS_MS if method in RETRY_METHODS else (SINGLE_ATTEMPT_TIMEOUT_MS,)
        qurl = QUrl(url)
        target = f"{method} {qurl.host()}{qurl.path()}"
        failures: list[str] = []
        for attempt, timeout_ms in enumerate(steps, 1):
            started = time.monotonic()
            try:
                response = self.send_once(method, url, timeout_ms, headers, data, upload_file, download_file)
            except NetworkError as e:
                failures.append(f"{target}: попытка {attempt}/{len(steps)} не удалась за {elapsed_ms(started)} мс "
                                f"(таймаут {timeout_ms} мс): {e}")
                if attempt == len(steps):
                    for failure in failures:
                        log.d(failure)
                    raise
                self.pause(RETRY_PAUSES_MS[attempt - 1])
                continue
            log.d(f"{target}: статус {response.status} за {elapsed_ms(started)} мс, попытка {attempt}/{len(steps)}")
            return response

    def send_once(self, method: str, url: str, timeout_ms: int, headers: dict[str, str] | None = None,
                  data: bytes = b"", upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(timeout_ms)
        for name, value in (headers or {}).items():
            request.setRawHeader(QByteArray(name.encode("ascii")), QByteArray(value.encode("utf-8")))
        verb = QByteArray(method.encode("ascii"))

        upload: QFile | None = None
        try:
            if upload_file is not None:
                upload = QFile(str(upload_file))
                if not upload.open(QIODevice.OpenModeFlag.ReadOnly):
                    raise SyncError(f"Не удалось открыть файл {upload_file}: {upload.errorString()}")
                reply = self.manager.sendCustomRequest(request, verb, upload)
            else:
                reply = self.manager.sendCustomRequest(request, verb, QByteArray(data))
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            response = self.read_response(reply)
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
