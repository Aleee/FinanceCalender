import hashlib
import ipaddress
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import lovely_logger as log
import PySide6
from PySide6.QtCore import QLocale, QThread, Signal, qVersion
from PySide6.QtNetwork import (QAbstractSocket, QHostAddress, QHostInfo, QNetworkInterface, QNetworkProxy,
                               QNetworkProxyFactory, QNetworkProxyQuery, QSslSocket)

from base.httpclient import AttemptInfo, QtHttpClient
from base.netdiagreport import (DiagReport, collect_log_text, drop_private_lines, drop_wifi_identity, read_tail,
                                save_report)
from base.paths import diag_dir, logs_dir
from base.sync import SyncError
from base.updater import (ANTIVIRUS_SCRIPT, API_URL, CREATE_NO_WINDOW, DIAG_HOSTS, PROXY_SETTINGS_SCRIPT,
                          PUBLIC_KEY, VERSION_FILE, describe_proxy)
from base.version import APP_VERSION, DB_VERSION
from base.yandexchannel import DEFAULT_DISK_FOLDER, YandexDiskApiChannel

YANDEX_HOSTS = DIAG_HOSTS[:2]
CONTROL_HOSTS = ("ya.ru", "www.google.com", "www.cloudflare.com")
PROBE_TIMEOUT_MS = 8000
LONG_PROBE_TIMEOUT_MS = 30000
PING_TIMEOUT_MS = 1000
GATEWAY_PING_COUNT = 20
PATHPING_QUERIES = 25
PATHPING_TIMEOUT_S = 400
WLAN_COMMAND = ["netsh", "wlan", "show", "interfaces"]
DNS_REPEATS = 3
API_REPEATS = 10
MASTER_INFO_REPEATS = 3
UPLOAD_TEST_SIZES = (64 * 1024, 1024 * 1024, 1024 * 1024)
UPLOAD_TEST_FOLDER = "app:/_netdiag"
SOAK_INTERVAL_S = 5
SOAK_API_EVERY = 6
SOAK_UPLOAD_EVERY = 60
SOAK_UPLOAD_SIZE = 1024 * 1024
SOAK_PAUSE_S = 300
COMMAND_TIMEOUT_S = 30
LONG_COMMAND_TIMEOUT_S = 120
MTU_PAYLOADS = (1472, 1400, 1280)
DNS_SERVERS = ("8.8.8.8", "1.1.1.1", "77.88.8.8")
CURL_FORMAT = ("dns %{time_namelookup} tcp %{time_connect} tls %{time_appconnect} ttfb %{time_starttransfer} "
               "total %{time_total} ip %{remote_ip} code %{http_code}\\n")
LOG_TAIL_BYTES = 400_000
MAX_ADDRESSES_PER_FAMILY = 3


@dataclass
class DiagConfig:
    token: str = ""
    disk_folder: str = DEFAULT_DISK_FOLDER
    send_test: bool = True
    soak_seconds: int = 0


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def resolve_host(host: str) -> tuple[list[str], list[str], int, str]:
    started = time.monotonic()
    info = QHostInfo.fromName(host)
    ipv4, ipv6 = [], []
    for address in info.addresses():
        target = ipv4 if address.protocol() == QAbstractSocket.NetworkLayerProtocol.IPv4Protocol else ipv6
        target.append(address.toString())
    error = "" if info.error() == QHostInfo.HostInfoError.NoError else info.errorString()
    return ipv4, ipv6, elapsed_ms(started), error


def read_http_head(socket: QSslSocket, host: str, result: dict, timeout_ms: int = PROBE_TIMEOUT_MS) -> None:
    request = f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\nUser-Agent: netdiag\r\n\r\n"
    sent = time.monotonic()
    socket.write(request.encode("ascii"))
    if not socket.waitForReadyRead(timeout_ms):
        result["stage"] = "response"
        result["qt_error"] = socket.error().name
        result["detail"] = socket.errorString()
        return
    result["ttfb_ms"] = elapsed_ms(sent)
    head = bytes(socket.readAll()).decode("latin-1")
    lines = head.split("\r\n")
    result["http"] = lines[0]
    for line in lines[1:]:
        name, _, value = line.partition(":")
        if name.lower() == "date":
            try:
                server_time = parsedate_to_datetime(value.strip())
                result["skew_s"] = round((server_time - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError):
                pass
    result["ok"] = True
    result["stage"] = "ok"


def probe_https(host: str, address: str = "", proxy: QNetworkProxy | None = None,
                timeout_ms: int = PROBE_TIMEOUT_MS) -> dict:
    result = {"kind": "probe", "host": host, "address": address or "auto", "ok": False, "stage": "tcp"}
    socket = QSslSocket()
    socket.setProxy(proxy if proxy is not None else QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
    started = time.monotonic()
    if address:
        socket.setPeerVerifyName(host)
        socket.connectToHost(QHostAddress(address), 443)
    else:
        socket.connectToHost(host, 443)
    if not socket.waitForConnected(timeout_ms):
        result.update(qt_error=socket.error().name, detail=socket.errorString(), total_ms=elapsed_ms(started))
        socket.abort()
        return result
    result["tcp_ms"] = elapsed_ms(started)
    result["stage"] = "tls"
    socket.startClientEncryption()
    if not socket.waitForEncrypted(timeout_ms):
        result.update(qt_error=socket.error().name, detail=socket.errorString(), total_ms=elapsed_ms(started),
                      ssl_errors=[error.errorString() for error in socket.sslHandshakeErrors()])
        socket.abort()
        return result
    result["tls_ms"] = elapsed_ms(started)
    certificate = socket.peerCertificate()
    result["cert"] = (f"{certificate.subjectDisplayName()}; выдан: {certificate.issuerDisplayName()}; "
                      f"до {certificate.expiryDate().toString('yyyy-MM-dd')}")
    read_http_head(socket, host, result, timeout_ms)
    result["total_ms"] = elapsed_ms(started)
    socket.abort()
    return result


def describe_probe(probe: dict) -> str:
    where = f"{probe['host']} [{probe['address']}]"
    if probe["ok"]:
        text = (f"{where}: TCP {probe['tcp_ms']} мс, TLS {probe['tls_ms']} мс, ответ через {probe['ttfb_ms']} мс, "
                f"всего {probe['total_ms']} мс, {probe.get('http', '')}")
        if "skew_s" in probe:
            text += f", часы расходятся с сервером на {probe['skew_s']} с"
        return text + f"\n    сертификат: {probe['cert']}"
    text = f"{where}: сбой на этапе «{probe['stage']}» за {probe['total_ms']} мс: {probe.get('qt_error')}, {probe.get('detail')}"
    if probe.get("ssl_errors"):
        text += f"\n    ошибки сертификата: {probe['ssl_errors']}"
    return text


def command_output(args: list[str], timeout: int = COMMAND_TIMEOUT_S) -> tuple[int | None, str]:
    windows = sys.platform == "win32"
    try:
        result = subprocess.run(args, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout,
                                creationflags=CREATE_NO_WINDOW if windows else 0,
                                encoding="oem" if windows else "utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return None, f"нет ответа за {timeout} с"
    except OSError as e:
        return None, f"не удалось запустить: {e}"
    return result.returncode, (result.stdout + result.stderr).strip()


def ping_command(host: str, count: int, payload: int | None = None) -> list[str]:
    if sys.platform == "win32":
        return ["ping", "-n", str(count)] + (["-f", "-l", str(payload)] if payload else []) + [host]
    dont_fragment = ["-D"] if sys.platform == "darwin" else ["-M", "do"]
    return ["ping", "-c", str(count)] + (dont_fragment + ["-s", str(payload)] if payload else []) + [host]


def parse_gateway(output: str) -> str:
    routes = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[:2] == ["0.0.0.0", "0.0.0.0"] and parts[4].isdigit() and is_ip_address(parts[2]):
            routes.append((int(parts[4]), parts[2]))
    if routes:
        return min(routes)[1]
    match = re.search(r"(?:via|gateway:)\s+(\S+)", output)
    return match.group(1) if match else ""


def is_ip_address(text: str) -> bool:
    try:
        ipaddress.ip_address(text)
    except ValueError:
        return False
    return True


def default_gateway() -> str:
    if sys.platform == "win32":
        args = ["route", "print", "-4", "0.0.0.0"]
    elif sys.platform == "darwin":
        args = ["route", "-n", "get", "default"]
    else:
        args = ["ip", "route", "show", "default"]
    return parse_gateway(command_output(args)[1])


def ping_once(host: str) -> tuple[bool, int]:
    if sys.platform == "win32":
        args = ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), host]
    else:
        wait = PING_TIMEOUT_MS if sys.platform == "darwin" else max(PING_TIMEOUT_MS // 1000, 1)
        args = ["ping", "-c", "1", "-W", str(wait), host]
    started = time.monotonic()
    _, output = command_output(args, PING_TIMEOUT_MS // 1000 + 5)
    match = re.search(r"[=<]\s*([\d.]+)\s*(?:ms|мс)", output, re.IGNORECASE)
    return "ttl=" in output.lower(), math.ceil(float(match.group(1))) if match else elapsed_ms(started)


def wifi_signal(output: str) -> int | None:
    match = re.search(r"(\d+)\s*%", output)
    return int(match.group(1)) if match else None


def trace_command(host: str) -> list[str]:
    if sys.platform == "win32":
        return ["tracert", "-d", "-h", "15", "-w", "800", host]
    return ["traceroute", "-n", "-m", "15", "-w", "1", host]


class NetDiag:
    def __init__(self, config: DiagConfig, progress: Callable[[str], None] = lambda text: None,
                 cancelled: Callable[[], bool] = lambda: False, stop_reason: Callable[[], str] = lambda: ""):
        self.config: DiagConfig = config
        self.progress: Callable[[str], None] = progress
        self.cancelled: Callable[[], bool] = cancelled
        self.stop_reason: Callable[[], str] = stop_reason
        self.report: DiagReport = DiagReport((config.token,))
        self.errors: list[str] = []
        self.client: QtHttpClient | None = None
        self.gateway: str | None = None

    def run(self) -> DiagReport:
        log.i(f"Диагностика сети: запуск, токен {'есть' if self.config.token else 'не указан'}, "
              f"тест отправки {self.config.send_test}, наблюдение {self.config.soak_seconds} с")
        self.client = QtHttpClient()
        self.client.on_attempt = self.record_attempt
        steps = [("Окружение", self.check_environment), ("DNS", self.check_dns),
                 ("Подключение к серверам", self.check_connections),
                 ("Запросы к Яндекс.Диску", self.check_api)]
        if self.config.token and self.config.send_test:
            steps.append(("Отправка тестовых файлов", self.check_upload))
        steps.append(("Системные команды", self.run_commands))
        if self.config.soak_seconds > 0:
            steps.append(("Наблюдение во времени", self.soak))
        for title, step in steps:
            self.run_step(title, step)
        self.report.outcome = self.describe_outcome()
        log.i(f"Диагностика сети: завершена, {self.report.outcome}")
        return self.report

    def describe_outcome(self) -> str:
        if self.cancelled():
            seconds = int(time.monotonic() - self.report.started)
            return f"остановлено на {seconds}-й секунде: {self.stop_reason() or 'причина не указана'}"
        failed = [title for title, status, _ in self.report.steps if status == "ошибка"]
        text = "все запланированные шаги выполнены"
        return text + (f", но с ошибками: {', '.join(failed)}" if failed else "")

    def run_step(self, title: str, step: Callable[[], None]) -> None:
        if self.cancelled():
            self.report.steps.append((title, "пропущен", 0))
            return
        self.progress(f"{title}…")
        self.report.section(title)
        started = time.monotonic()
        status = "выполнен"
        try:
            step()
        except Exception:
            status = "ошибка"
            self.errors.append(f"[{title}]\n{traceback.format_exc()}")
            self.report.line("Шаг завершился ошибкой, подробности в sys_errors.txt")
            log.w(f"Диагностика сети: шаг «{title}» завершился ошибкой")
        if status == "выполнен" and self.cancelled():
            status = "прерван остановкой"
        seconds = int(time.monotonic() - started)
        self.report.steps.append((title, status, seconds))
        log.i(f"Диагностика сети: шаг «{title}»: {status}, {seconds} с")

    def record_attempt(self, info: AttemptInfo) -> None:
        self.report.sample("attempt", label=info.target, attempt=info.attempt, ms=info.elapsed_ms, status=info.status,
                           marks=dict(info.marks), error=info.error, qt_error=info.qt_error)

    def timed_op(self, label: str, operation: Callable[[], object]) -> bool:
        started = time.monotonic()
        error = ""
        try:
            operation()
        except (SyncError, ValueError) as e:
            error = str(e)
        self.report.sample("op", label=label, ok=not error, ms=elapsed_ms(started), error=error)
        self.report.line(f"{label}: {'ок' if not error else 'ошибка: ' + error} за {elapsed_ms(started)} мс")
        return not error

    def check_environment(self) -> None:
        report = self.report
        report.line(f"Программа {APP_VERSION}, версия БД {DB_VERSION}")
        report.line(f"ОС: {platform.platform()}, Python {platform.python_version()}, PySide6 {PySide6.__version__}, "
                    f"Qt {qVersion()}")
        report.line(f"SSL: {QSslSocket.supportsSsl()} ({QSslSocket.activeBackend()}), {QSslSocket.sslLibraryVersionString()}")
        report.line(f"Время: {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %z %Z}, язык системы {QLocale.system().name()}")
        report.line(f"Qt использует системные настройки прокси: {QNetworkProxyFactory.usesSystemConfiguration()}")
        for host in YANDEX_HOSTS:
            proxy = self.system_proxy(host)
            report.line(f"Прокси для {host}: {describe_proxy(proxy)}")
        proxy_vars = {name: os.environ[name] for name in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY")
                      if name in os.environ}
        report.line(f"Переменные прокси: {proxy_vars}")
        for interface in QNetworkInterface.allInterfaces():
            flags = interface.flags()
            if not (flags & QNetworkInterface.InterfaceFlag.IsUp) or flags & QNetworkInterface.InterfaceFlag.IsLoopBack:
                continue
            addresses = ", ".join(entry.ip().toString() for entry in interface.addressEntries())
            report.line(f"Интерфейс {interface.humanReadableName()} ({interface.type().name}), "
                        f"MTU {interface.maximumTransmissionUnit()}: {addresses}")
        report.line(f"Шлюз по умолчанию (роутер): {self.get_gateway() or 'не определён'}")
        self.timed_op("Внешний адрес (ipinfo.io)", self.read_public_address)

    def get_gateway(self) -> str:
        if self.gateway is None:
            self.gateway = default_gateway()
        return self.gateway

    @staticmethod
    def system_proxy(host: str) -> QNetworkProxy:
        return QNetworkProxyFactory.systemProxyForQuery(QNetworkProxyQuery(host, 443, "https"))[0]

    def read_public_address(self) -> None:
        response = self.client.send("GET", "https://ipinfo.io/json")
        data = json.loads(response.body.decode("utf-8"))
        self.report.line(f"Внешний адрес: {data.get('ip')}, {data.get('country')}, {data.get('region')}, "
                         f"провайдер: {data.get('org')}")

    def check_dns(self) -> None:
        for host in YANDEX_HOSTS + CONTROL_HOSTS:
            for number in range(1, DNS_REPEATS + 1):
                ipv4, ipv6, ms, error = resolve_host(host)
                self.report.sample("dns", host=host, ms=ms, ok=not error, error=error)
                self.report.line(f"{host} (попытка {number}): {ms} мс, IPv4 {ipv4}, IPv6 {ipv6}"
                                 f"{', ошибка: ' + error if error else ''}")

    def check_connections(self) -> None:
        for host in YANDEX_HOSTS + CONTROL_HOSTS:
            if self.cancelled():
                return
            self.report_probe(probe_https(host))
            system_proxy = self.system_proxy(host)
            if system_proxy.type() != QNetworkProxy.ProxyType.NoProxy:
                self.report.line(f"  через системный прокси {describe_proxy(system_proxy)}:")
                self.report_probe(probe_https(host, proxy=system_proxy))
        for host in YANDEX_HOSTS:
            ipv4, ipv6, _, _ = resolve_host(host)
            for address in ipv4[:MAX_ADDRESSES_PER_FAMILY] + ipv6[:MAX_ADDRESSES_PER_FAMILY]:
                self.report_probe(probe_https(host, address, timeout_ms=LONG_PROBE_TIMEOUT_MS))

    def report_probe(self, probe: dict) -> None:
        self.report.samples.append({"t": round(time.monotonic() - self.report.started, 1), **probe})
        self.report.line(describe_probe(probe))

    def create_channel(self, folder: str) -> YandexDiskApiChannel:
        return YandexDiskApiChannel(self.config.token, self.client, folder)

    def create_new_connection_channel(self) -> YandexDiskApiChannel:
        client = QtHttpClient()
        client.on_attempt = self.record_attempt
        return YandexDiskApiChannel(self.config.token, client, self.config.disk_folder)

    def check_api(self) -> None:
        public_link = f"{API_URL}?public_key={PUBLIC_KEY}&path=/{VERSION_FILE}"
        for _ in range(API_REPEATS):
            self.timed_op("Публичная ссылка на version.json (без токена)",
                          lambda: self.client.send("GET", public_link))
        if not self.config.token:
            self.report.line("Токен не указан, проверки с авторизацией пропущены")
            return
        channel = self.create_channel(self.config.disk_folder)
        for _ in range(API_REPEATS):
            if self.cancelled():
                return
            self.timed_op("API: проверка папки", channel.check_connection)
        for _ in range(MASTER_INFO_REPEATS):
            fresh = self.create_channel(self.config.disk_folder)
            self.timed_op("API + скачивание: информация о мастере", fresh.read_master_info)

    def check_upload(self) -> None:
        channel = self.create_channel(UPLOAD_TEST_FOLDER)
        for number, size in enumerate(UPLOAD_TEST_SIZES, start=1):
            if self.cancelled():
                break
            self.upload_test_file(channel, f"test_{number}.bin", size)
        channel.delete_quietly(UPLOAD_TEST_FOLDER)

    def upload_test_file(self, channel: YandexDiskApiChannel, name: str, size: int) -> None:
        data = os.urandom(size)
        remote = channel.remote_path(name)
        self.timed_op(f"Отправка {size // 1024} КБ",
                      lambda: channel.put_file(remote, hashlib.md5(data).hexdigest(), size, data=data))
        channel.delete_quietly(remote)

    def run_commands(self) -> None:
        windows = sys.platform == "win32"
        curl = "curl.exe" if windows else "curl"
        curl_base = [curl, "-sS", "-m", "20", "-o", "NUL" if windows else "/dev/null", "-w", CURL_FORMAT]
        api_link = f"{API_URL}?public_key={PUBLIC_KEY}&path=/{VERSION_FILE}"
        api_host = YANDEX_HOSTS[0]
        commands: list[tuple[str, list[str], int]] = []
        gateway = self.get_gateway()
        if gateway:
            commands.append((f"ping шлюза {gateway}, {GATEWAY_PING_COUNT} пакетов",
                             ping_command(gateway, GATEWAY_PING_COUNT), LONG_COMMAND_TIMEOUT_S))
        if windows:
            commands.append(("Wi-Fi: состояние адаптера", WLAN_COMMAND, COMMAND_TIMEOUT_S))
        commands += [(f"curl API, попытка {n}", curl_base + [api_link], COMMAND_TIMEOUT_S) for n in (1, 2, 3)]
        commands += [("curl API без прокси", curl_base + ["--noproxy", "*", api_link], COMMAND_TIMEOUT_S),
                     ("curl API по IPv4", curl_base + ["--ipv4", api_link], COMMAND_TIMEOUT_S),
                     ("curl API по IPv6", curl_base + ["--ipv6", api_link], COMMAND_TIMEOUT_S)]
        commands += [(f"curl {host}, попытка {n}", curl_base + [f"https://{host}"], COMMAND_TIMEOUT_S)
                     for host in CONTROL_HOSTS[:2] for n in (1, 2)]
        commands.append(("nslookup (DNS по умолчанию)", ["nslookup", api_host], COMMAND_TIMEOUT_S))
        commands += [(f"nslookup через {server}", ["nslookup", api_host, server], COMMAND_TIMEOUT_S)
                     for server in DNS_SERVERS]
        commands += [(f"ping {host}", ping_command(host, 10), COMMAND_TIMEOUT_S) for host in (api_host, CONTROL_HOSTS[1])]
        commands += [(f"ping {api_host}, запрет фрагментации, данные {payload} байт",
                      ping_command(api_host, 2, payload), COMMAND_TIMEOUT_S) for payload in MTU_PAYLOADS]
        commands += [(f"трассировка до {host}", trace_command(host), LONG_COMMAND_TIMEOUT_S)
                     for host in (api_host, CONTROL_HOSTS[1])]
        if windows:
            commands += [("ipconfig /all", ["ipconfig", "/all"], COMMAND_TIMEOUT_S),
                         ("netsh winhttp", ["netsh", "winhttp", "show", "proxy"], COMMAND_TIMEOUT_S),
                         ("настройки прокси в реестре",
                          ["powershell", "-NoProfile", "-NonInteractive", "-Command", PROXY_SETTINGS_SCRIPT],
                          COMMAND_TIMEOUT_S),
                         ("антивирус", ["powershell", "-NoProfile", "-NonInteractive", "-Command", ANTIVIRUS_SCRIPT],
                          COMMAND_TIMEOUT_S)]
            if self.config.soak_seconds > 0:
                commands += [(f"pathping до {host}", ["pathping", "-n", "-q", str(PATHPING_QUERIES), "-h", "15", host],
                              PATHPING_TIMEOUT_S) for host in (api_host, CONTROL_HOSTS[1])]
        for label, args, timeout in commands:
            if self.cancelled():
                return
            self.progress(f"Команда: {label}…")
            code, output = command_output(args, timeout)
            if label == "ipconfig /all":
                output = drop_private_lines(output)
            elif label.startswith("Wi-Fi"):
                output = drop_wifi_identity(output)
            self.report.line(f"\n--- {label} (код {code}) ---\n{output[:6000]}")

    def sample_wifi(self) -> None:
        if sys.platform != "win32":
            return
        signal = wifi_signal(command_output(WLAN_COMMAND)[1])
        if signal is not None:
            self.report.sample("wifi", signal=signal)

    def soak(self) -> None:
        hosts = YANDEX_HOSTS + CONTROL_HOSTS
        gateway = self.get_gateway()
        channel = self.create_channel(self.config.disk_folder) if self.config.token else None
        upload_channel = self.create_channel(UPLOAD_TEST_FOLDER) if channel and self.config.send_test else None
        soak_started = time.monotonic()
        deadline = soak_started + self.config.soak_seconds
        cycle = 0
        previous_start = time.time()
        while time.monotonic() < deadline and not self.cancelled():
            cycle_started = time.monotonic()
            pause = int(time.time() - previous_start)
            previous_start = time.time()
            if pause > SOAK_PAUSE_S:
                self.report.sample("pause", seconds=pause)
                self.report.line(f"Между циклами наблюдения прошло {pause} с (сон компьютера или зависание)")
            if gateway:
                reachable, ping_ms = ping_once(gateway)
                self.report.sample("soak", host=f"шлюз {gateway}", group="gateway", cycle=cycle, ok=reachable,
                                   stage="ok" if reachable else "ping", qt_error="" if reachable else "NoReply",
                                   total_ms=ping_ms)
            for host in hosts:
                probe = probe_https(host)
                self.report.sample("soak", host=host, group="yandex" if host in YANDEX_HOSTS else "control",
                                   cycle=cycle, ok=probe["ok"], stage=probe["stage"],
                                   qt_error=probe.get("qt_error", ""), total_ms=probe["total_ms"],
                                   **({"tcp_ms": probe["tcp_ms"]} if "tcp_ms" in probe else {}))
            if cycle % SOAK_API_EVERY == 0:
                self.sample_wifi()
            if channel is not None and cycle % SOAK_API_EVERY == 0:
                self.timed_op("Наблюдение: API, проверка папки (соединение уже открыто)", channel.check_connection)
                self.timed_op("Наблюдение: API, проверка папки (новое соединение, как при синхронизации)",
                              self.create_new_connection_channel().check_connection)
            if upload_channel is not None and cycle % SOAK_UPLOAD_EVERY == SOAK_UPLOAD_EVERY - 1:
                self.upload_test_file(upload_channel, "soak.bin", SOAK_UPLOAD_SIZE)
            cycle += 1
            if cycle % SOAK_API_EVERY == 0:
                self.progress(f"Наблюдение: цикл {cycle}, осталось {max(int(deadline - time.monotonic()), 0)} с")
            while time.monotonic() - cycle_started < SOAK_INTERVAL_S and not self.cancelled():
                time.sleep(0.1)
        if upload_channel is not None:
            upload_channel.delete_quietly(UPLOAD_TEST_FOLDER)
        self.report.line(f"Наблюдение длилось {int(time.monotonic() - soak_started)} с из запланированных "
                         f"{self.config.soak_seconds} с, циклов {cycle}, подробности в samples.jsonl")


class DiagThread(QThread):
    progress = Signal(str)
    report_ready = Signal(str)

    def __init__(self, config: DiagConfig, parent=None):
        super().__init__(parent)
        self.config: DiagConfig = config
        self.stop_reason: str = ""
        self.outcome: str = ""

    def request_stop(self, reason: str) -> None:
        if not self.stop_reason:
            self.stop_reason = reason
            log.i(f"Диагностика сети: запрошена остановка: {reason}")
        self.requestInterruption()

    def run(self) -> None:
        diag = NetDiag(self.config, self.progress.emit, self.isInterruptionRequested, lambda: self.stop_reason)
        try:
            report = diag.run()
            self.outcome = report.outcome
            logs_folder = Path(logs_dir())
            errors_text = "\n".join(diag.errors) + "\n" + read_tail(logs_folder / "sys_errors.log", LOG_TAIL_BYTES)
            path = save_report(report, Path(diag_dir()), collect_log_text(logs_folder, LOG_TAIL_BYTES), errors_text)
        except Exception:
            log.exception("Диагностика сети: аварийное завершение")
            self.outcome = "аварийное завершение из-за внутренней ошибки, подробности в журнале программы"
            return
        self.report_ready.emit(str(path))
