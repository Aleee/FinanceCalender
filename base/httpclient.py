from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QByteArray, QEventLoop, QFile, QIODevice, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from base.sync import NetworkError, SyncError

TRANSFER_TIMEOUT_MS = 60000


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


class QtHttpClient(HttpClient):
    def __init__(self, timeout_ms: int = TRANSFER_TIMEOUT_MS):
        self.timeout_ms: int = timeout_ms
        self.manager: QNetworkAccessManager = QNetworkAccessManager()
        self.manager.setRedirectPolicy(QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)

    def send(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
             upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(self.timeout_ms)
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
        body = bytes(reply.readAll())
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
