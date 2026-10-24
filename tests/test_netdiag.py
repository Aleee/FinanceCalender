import json
import zipfile
from pathlib import Path

import pytest

import base.netdiag as netdiagmod
from base.httpclient import AttemptInfo, QtHttpClient
from base.netdiag import DiagConfig, NetDiag, probe_https, resolve_host
from base.netdiagreport import (DiagReport, collect_log_text, describe_timings, drop_private_lines, drop_wifi_identity,
                                sanitize_text, save_report, summarize_attempts, summarize_correlation,
                                summarize_operations, summarize_probes)
from tests.yandexfake import FakeDisk

TOKEN = "y0_AgAAAAAtestsecrettokenvalue1234567890"


def test_sanitize_hides_token_and_signed_links():
    text = (f"Authorization: OAuth {TOKEN}\nGET https://downloader.disk.yandex.ru/disk/abcdef?x=1 "
            f"token={TOKEN} https://user:pass@host/path")
    result = sanitize_text(text, (TOKEN,))
    assert TOKEN not in result
    assert "abcdef" not in result
    assert "pass@" not in result


def test_drop_private_lines():
    text = "Описание: Ethernet\nФизический адрес: AA-BB\nIPv4-адрес: 10.0.0.2\nDUID: 1234"
    assert drop_private_lines(text) == "Описание: Ethernet\nIPv4-адрес: 10.0.0.2"


def test_describe_timings():
    assert describe_timings([]) == "нет данных"
    assert describe_timings(list(range(1, 101))) == "p50 50, p90 90, p99 99, max 100 мс"


def test_summaries_count_failures_and_slow_probes():
    samples = [{"kind": "soak", "host": "h", "ok": True, "stage": "ok", "total_ms": 500, "tcp_ms": 40},
               {"kind": "soak", "host": "h", "ok": True, "stage": "ok", "total_ms": 3500, "tcp_ms": 3000},
               {"kind": "soak", "host": "h", "ok": False, "stage": "tcp", "qt_error": "SocketTimeoutError",
                "total_ms": 8000},
               {"kind": "attempt", "label": "GET h/x", "attempt": 1, "ms": 1500, "status": None,
                "qt_error": "OwnConnectTimeout"},
               {"kind": "attempt", "label": "GET h/x", "attempt": 2, "ms": 300, "status": 200}]
    probes = "\n".join(summarize_probes(samples))
    assert "проб 3, неудач 1, дольше 1 с: 2, дольше 3 с: 2" in probes
    assert "tcp/SocketTimeoutError ×1" in probes
    attempts = "\n".join(summarize_attempts(samples))
    assert "попыток 2, неудачных 1, повторных 1" in attempts


def test_save_report_masks_token(tmp_path):
    report = DiagReport((TOKEN,))
    report.section("Проверка")
    report.line(f"токен {TOKEN}")
    report.sample("op", label="x", ok=False, ms=5, error=f"ошибка {TOKEN}")
    path = save_report(report, tmp_path / "diag", log_text=f"OAuth {TOKEN}", errors_text="")
    with zipfile.ZipFile(path) as archive:
        assert sorted(archive.namelist()) == ["app_log.txt", "report.txt", "samples.jsonl", "sys_errors.txt"]
        assert all(TOKEN not in archive.read(name).decode("utf-8") for name in archive.namelist())
        assert "=== СВОДКА ===" in archive.read("report.txt").decode("utf-8")


def test_collect_log_text_takes_tail_of_both_files(tmp_path):
    (tmp_path / "log.log.1").write_bytes("старый\n".encode())
    (tmp_path / "log.log").write_bytes("новый\n".encode())
    assert collect_log_text(tmp_path, 10_000) == "старый\nновый\n"
    assert collect_log_text(tmp_path / "missing", 10_000) == ""


def test_resolve_host_localhost(qapp):
    ipv4, ipv6, ms, error = resolve_host("localhost")
    assert not error
    assert ipv4 or ipv6


def test_probe_unresolvable_host_fails_at_tcp_stage(qapp):
    probe = probe_https("nonexistent.invalid")
    assert not probe["ok"]
    assert probe["stage"] == "tcp"
    assert probe["total_ms"] >= 0


class DiskClient(FakeDisk):
    def __init__(self):
        super().__init__()
        self.on_attempt = None


@pytest.fixture
def diag(qapp, monkeypatch) -> NetDiag:
    disk = DiskClient()
    monkeypatch.setattr(netdiagmod, "QtHttpClient", lambda: disk)
    monkeypatch.setattr(netdiagmod, "API_REPEATS", 2)
    monkeypatch.setattr(netdiagmod, "MASTER_INFO_REPEATS", 1)
    diag = NetDiag(DiagConfig("good-token"))
    diag.client = disk
    return diag


def test_upload_check_sends_and_removes_test_files(diag):
    diag.check_upload()
    operations = [sample for sample in diag.report.samples if sample["kind"] == "op"]
    assert len(operations) == len(netdiagmod.UPLOAD_TEST_SIZES)
    assert all(sample["ok"] for sample in operations)
    assert not diag.client.files


def test_api_check_records_operations(diag):
    diag.check_api()
    operations = [sample for sample in diag.report.samples if sample["kind"] == "op"]
    assert any(sample["label"] == "API: проверка папки" for sample in operations)


def test_failed_step_is_reported_not_raised(diag):
    def broken():
        raise RuntimeError("сломалось")

    diag.run_step("Сломанный шаг", broken)
    assert "RuntimeError" in diag.errors[0]
    assert "Сломанный шаг" in diag.report.text()


def test_cancelled_run_skips_steps(diag):
    diag.cancelled = lambda: True
    visited: list[str] = []
    diag.run_step("Шаг", lambda: visited.append("x"))
    assert not visited


def test_step_journal_and_outcome_explain_why_run_ended(diag):
    diag.run_step("Первый", lambda: None)
    state = {"stop": False}
    diag.cancelled = lambda: state["stop"]
    diag.stop_reason = lambda: "нажата кнопка «Остановить»"
    diag.run_step("Второй", lambda: state.update(stop=True))
    diag.run_step("Третий", lambda: None)
    assert [(title, status) for title, status, _ in diag.report.steps] == [
        ("Первый", "выполнен"), ("Второй", "прерван остановкой"), ("Третий", "пропущен")]
    diag.report.outcome = diag.describe_outcome()
    text = diag.report.text()
    assert "Завершение: остановлено на" in text and "нажата кнопка «Остановить»" in text
    assert "Третий: пропущен" in text


def test_outcome_of_complete_run_lists_failed_steps(diag):
    diag.run_step("Хороший", lambda: None)
    assert diag.describe_outcome() == "все запланированные шаги выполнены"
    diag.run_step("Сломанный", lambda: 1 / 0)
    assert diag.describe_outcome().endswith("с ошибками: Сломанный")


def test_thread_keeps_first_stop_reason(qapp):
    thread = netdiagmod.DiagThread(DiagConfig())
    thread.request_stop("первая")
    thread.request_stop("вторая")
    assert thread.stop_reason == "первая"


def test_operations_summary_groups_repeated_labels():
    samples = [{"kind": "op", "label": "A", "ok": True, "ms": 100, "error": ""},
               {"kind": "op", "label": "A", "ok": False, "ms": 5000, "error": "таймаут"},
               {"kind": "op", "label": "B", "ok": True, "ms": 10, "error": ""}]
    lines = "\n".join(summarize_operations(samples))
    assert "A: 2 раз, с ошибкой 1; успешные: p50 100" in lines
    assert "B:" not in lines


def test_soak_pause_and_new_connection_check_are_recorded(diag, monkeypatch):
    monkeypatch.setattr(netdiagmod, "probe_https", lambda host, *args, **kwargs: {"ok": True, "stage": "ok", "total_ms": 1})
    monkeypatch.setattr(netdiagmod, "SOAK_INTERVAL_S", 0)
    monkeypatch.setattr(netdiagmod, "SOAK_PAUSE_S", -1)
    monkeypatch.setattr(diag, "sample_wifi", lambda: None)
    diag.gateway = ""
    diag.config.soak_seconds = 1
    diag.config.send_test = False
    monkeypatch.setattr(diag, "cancelled", iter([False, True, True]).__next__)
    diag.soak()
    assert any(sample["kind"] == "pause" for sample in diag.report.samples)
    labels = {sample["label"] for sample in diag.report.samples if sample["kind"] == "op"}
    assert any("новое соединение" in label for label in labels)
    assert any("соединение уже открыто" in label for label in labels)


def test_soak_probes_hosts_and_uploads_periodically(diag, monkeypatch):
    monkeypatch.setattr(netdiagmod, "probe_https",
                        lambda host, *args, **kwargs: {"ok": True, "stage": "ok", "total_ms": 10, "tcp_ms": 5})
    monkeypatch.setattr(netdiagmod, "SOAK_INTERVAL_S", 0)
    monkeypatch.setattr(netdiagmod, "SOAK_UPLOAD_EVERY", 2)
    monkeypatch.setattr(netdiagmod, "SOAK_UPLOAD_SIZE", 1024)
    diag.config.soak_seconds = 1
    diag.config.send_test = True
    diag.gateway = ""
    monkeypatch.setattr(diag, "sample_wifi", lambda: None)
    monkeypatch.setattr(diag, "cancelled", iter([False, False, False, True, True, True, True]).__next__)
    diag.soak()
    kinds = [sample["kind"] for sample in diag.report.samples]
    assert kinds.count("soak") >= len(netdiagmod.YANDEX_HOSTS + netdiagmod.CONTROL_HOSTS)
    uploads = [sample for sample in diag.report.samples if sample["kind"] == "op" and sample["label"].startswith("Отправка")]
    assert uploads and all(sample["ok"] for sample in uploads)
    assert not diag.client.files


ROUTE_PRINT = """
IPv4 таблица маршрута
Сетевой адрес           Маска сети      Адрес шлюза       Интерфейс  Метрика
          0.0.0.0          0.0.0.0       10.10.2.1      10.10.2.140     45
          0.0.0.0          0.0.0.0     192.168.1.1      192.168.1.5    300
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
"""


def test_parse_gateway_takes_route_with_lowest_metric():
    assert netdiagmod.parse_gateway(ROUTE_PRINT) == "10.10.2.1"
    assert netdiagmod.parse_gateway("default via 192.168.0.1 dev wlan0 proto dhcp") == "192.168.0.1"
    assert netdiagmod.parse_gateway("   gateway: 172.20.10.1\n  interface: en0") == "172.20.10.1"
    assert netdiagmod.parse_gateway("нет маршрутов") == ""


def test_wifi_signal_and_identity_filter():
    output = ("    Имя                    : Беспроводная сеть\n    SSID                   : MyHome\n"
              "    BSSID                  : aa:bb:cc:dd:ee:ff\n    Физический адрес       : aa-bb\n"
              "    Канал                  : 6\n    Сигнал                 : 72%\n    Профиль                : MyHome")
    assert netdiagmod.wifi_signal(output) == 72
    assert netdiagmod.wifi_signal("интерфейс не найден") is None
    filtered = drop_wifi_identity(output)
    assert "MyHome" not in filtered and "aa:bb" not in filtered and "44ba802e" not in filtered
    assert "Сигнал" in filtered and "Канал" in filtered


def test_correlation_summary_separates_wifi_from_route_problems():
    def sample(cycle, group, ok=True, total_ms=50):
        return {"kind": "soak", "cycle": cycle, "group": group, "host": group, "ok": ok, "stage": "ok",
                "total_ms": total_ms}

    samples = [sample(0, "gateway"), sample(0, "yandex"), sample(0, "control"),
               sample(1, "gateway"), sample(1, "yandex", total_ms=5000), sample(1, "control"),
               sample(2, "gateway", ok=False), sample(2, "yandex", ok=False), sample(2, "control", total_ms=4000)]
    lines = "\n".join(summarize_correlation(samples))
    assert "Циклов наблюдения 3, с проблемой (сбой или дольше 3 с) 2" in lines
    assert "Яндекс: 1" in lines
    assert "шлюз (роутер) + Яндекс + контрольные хосты: 1" in lines


def test_soak_pings_gateway_and_groups_samples(diag, monkeypatch):
    monkeypatch.setattr(netdiagmod, "probe_https",
                        lambda host, *args, **kwargs: {"ok": True, "stage": "ok", "total_ms": 10})
    monkeypatch.setattr(netdiagmod, "ping_once", lambda host: (False, 1000))
    monkeypatch.setattr(netdiagmod, "SOAK_INTERVAL_S", 0)
    monkeypatch.setattr(diag, "sample_wifi", lambda: None)
    diag.gateway = "10.0.0.1"
    diag.config.soak_seconds = 1
    diag.config.send_test = False
    monkeypatch.setattr(diag, "cancelled", iter([False, True, True]).__next__)
    diag.soak()
    gateway_samples = [sample for sample in diag.report.samples if sample.get("group") == "gateway"]
    assert gateway_samples and not gateway_samples[0]["ok"]
    assert {sample["group"] for sample in diag.report.samples if sample["kind"] == "soak"} == {
        "gateway", "yandex", "control"}


def test_sanitize_hides_signed_link_with_port():
    result = sanitize_text("GET https://downloader.disk.yandex.ru:443/disk/abcdef/file.zip ok")
    assert "abcdef" not in result
    assert "downloader.disk.yandex.ru:443/…" in result
