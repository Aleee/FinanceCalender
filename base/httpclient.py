import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import lovely_logger as log
from PySide6.QtCore import QByteArray, QEventLoop, QFile, QIODevice, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from base.sync import NetworkError, SyncCancelledError, SyncError

QUIET_WAIT_MS = 350
CONNECT_TIMEOUT_MS = 1500
RESPONSE_TIMEOUT_MS = 8000
UPLOAD_EXTRA_MS_PER_MB = 2000
MAX_ATTEMPTS = 4
IDLE_RECONNECT_S = 5
RETRY_PAUSE_MS = 200
RETRY_METHODS = ("GET",)
OWN_CONNECT_TIMEOUT = "ConnectTimeout"


class ConnectStageError(NetworkError):
    pass


@dataclass
class HttpResponse:
    status: int
    body: bytes


@dataclass
class AttemptInfo:
    target: str
    attempt: int
    elapsed_ms: int
    status: int | None = None
    marks: dict[str, int] = field(default_factory=dict)
    error: str = ""
    qt_error: str = ""


def qt_network_error(text: str, error: QNetworkReply.NetworkError) -> NetworkError:
    network_error = NetworkError(text)
    network_error.qt_error = error.name
    return network_error


def trace_text(marks: dict[str, int], qt_error: str = "") -> str:
    parts = [f"{name}={value}" for name, value in marks.items()]
    if qt_error:
        parts.append(f"ошибка Qt: {qt_error}")
    return f" [{', '.join(parts)}]" if parts else ""


class HttpClient(ABC):
    cancel_requested: bool = False
    cancel_allowed: bool = True

    def request_cancel(self) -> None:
        if self.cancel_allowed:
            self.cancel_requested = True

    def check_cancel(self) -> None:
        if self.cancel_requested:
            self.cancel_requested = False
            raise SyncCancelledError("прервано пользователем")

    @contextmanager
    def uninterruptible(self) -> Iterator[None]:
        self.check_cancel()
        self.cancel_allowed = False
        try:
            yield
        finally:
            self.cancel_allowed = True

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
        self.marks: dict[str, int] = {}
        self.on_attempt: Callable[[AttemptInfo], None] | None = None
        self.on_retry: Callable[[int, int], None] | None = None
        self.on_long_wait: Callable[[bool], None] | None = None
        self.on_long_wait_end: Callable[[], None] | None = None
        self.active_reply: QNetworkReply | None = None
        self.active_loop: QEventLoop | None = None
        self.last_request_at: float = time.monotonic()

    def send(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
             upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        self.check_cancel()
        qurl = QUrl(url)
        target = f"{method} {qurl.host()}{qurl.path()}"
        failures: list[str] = []
        if time.monotonic() - self.last_request_at > IDLE_RECONNECT_S:
            self.manager.clearConnectionCache()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.monotonic()
            try:
                response = self.send_once(method, url, headers, data, upload_file, download_file)
            except NetworkError as e:
                self.check_cancel()
                qt_error = getattr(e, "qt_error", "")
                failures.append(f"{target}: попытка {attempt}/{MAX_ATTEMPTS} не удалась за {elapsed_ms(started)} мс: "
                                f"{e}{trace_text(self.marks, qt_error)}")
                self.report_attempt(AttemptInfo(target, attempt, elapsed_ms(started), None, self.marks, str(e), qt_error))
                if attempt == MAX_ATTEMPTS or not (isinstance(e, ConnectStageError) or method in RETRY_METHODS):
                    for failure in failures:
                        log.d(failure)
                    raise
                self.manager.clearConnectionCache()
                if self.on_retry is not None:
                    self.on_retry(attempt + 1, MAX_ATTEMPTS)
                self.pause(RETRY_PAUSE_MS)
                continue
            for failure in failures:
                log.d(failure)
            log.d(f"{target}: статус {response.status} за {elapsed_ms(started)} мс, попытка {attempt}/{MAX_ATTEMPTS}"
                  f"{trace_text(self.marks)}")
            self.report_attempt(AttemptInfo(target, attempt, elapsed_ms(started), response.status, self.marks))
            return response

    def report_attempt(self, info: AttemptInfo) -> None:
        if self.on_attempt is not None:
            self.on_attempt(info)

    def send_once(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
                  upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        self.marks = {}
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
            stage = self.wait_for_reply(reply, self.marks)
            try:
                response = self.read_response(reply)
            except NetworkError as e:
                if stage == "request":
                    raise
                text = "Нет связи с сервером: превышено время подключения" if stage == "timeout" else str(e)
                connect_error = ConnectStageError(text)
                connect_error.qt_error = OWN_CONNECT_TIMEOUT if stage == "timeout" else getattr(e, "qt_error", "")
                raise connect_error from e
        finally:
            self.last_request_at = time.monotonic()
            if upload is not None:
                upload.close()
        if download_file is not None and response.status == 200:
            try:
                download_file.write_bytes(response.body)
            except OSError as e:
                raise SyncError(f"Не удалось записать файл {download_file}: {e}") from e
            return HttpResponse(response.status, b"")
        return response

    def request_cancel(self) -> None:
        super().request_cancel()
        if not self.cancel_requested:
            return
        if self.active_reply is not None:
            self.active_reply.abort()
        if self.active_loop is not None:
            self.active_loop.quit()

    def run_loop(self, loop: QEventLoop, is_finished: Callable[[], bool]) -> None:
        quiet_timer = QTimer()
        quiet_timer.setSingleShot(True)
        quiet_timer.timeout.connect(loop.quit)
        quiet_timer.start(QUIET_WAIT_MS)
        self.active_loop = loop
        long_wait_started = False
        try:
            loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            quiet_timer.stop()
            if is_finished() or self.cancel_requested:
                return
            if self.on_long_wait is not None:
                self.on_long_wait(self.cancel_allowed)
                long_wait_started = True
            loop.exec(QEventLoop.ProcessEventsFlag.AllEvents if self.cancel_allowed
                      else QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        finally:
            self.active_loop = None
            if long_wait_started and self.on_long_wait_end is not None:
                self.on_long_wait_end()

    def wait_for_reply(self, reply: QNetworkReply, marks: dict[str, int] | None = None) -> str:
        stage = "request"
        marks = {} if marks is None else marks
        started = time.monotonic()

        def on_connecting():
            nonlocal stage
            stage = "connect"
            marks.setdefault("connecting", elapsed_ms(started))
            connect_timer.start(CONNECT_TIMEOUT_MS)

        def on_connected(name: str):
            nonlocal stage
            marks.setdefault(name, elapsed_ms(started))
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
        for name, signal in (("encrypted", reply.encrypted), ("sent", reply.requestSent),
                             ("headers", reply.metaDataChanged)):
            signal.connect(lambda name=name: on_connected(name))
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        self.active_reply = reply
        try:
            self.run_loop(loop, reply.isFinished)
        finally:
            self.active_reply = None
            connect_timer.stop()
        return stage

    @staticmethod
    def read_response(reply: QNetworkReply) -> HttpResponse:
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error, error_text = reply.error(), reply.errorString()
        body = bytes(reply.readAll()) if reply.isOpen() else b""
        reply.deleteLater()
        if status is None:
            raise qt_network_error(f"Нет связи с сервером: {error_text}", error)
        if status < 400 and error != QNetworkReply.NetworkError.NoError:
            raise qt_network_error(f"Передача данных прервана: {error_text}", error)
        return HttpResponse(int(status), body)

    def pause(self, milliseconds: int) -> None:
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(milliseconds)
        self.run_loop(loop, lambda: not timer.isActive())
        timer.stop()
        self.check_cancel()
