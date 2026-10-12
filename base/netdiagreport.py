import json
import math
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OAUTH_RE = re.compile(r"OAuth\s+\S+")
YANDEX_TOKEN_RE = re.compile(r"\by[0-9a-z]_[A-Za-z0-9_\-]{20,}")
SIGNED_URL_RE = re.compile(r"((?:downloader|uploader)[\w.\-]*\.disk\.yandex\.\w+)/\S+")
URL_CREDENTIALS_RE = re.compile(r"://[^/@\s]+@")
PRIVATE_LINE_RE = re.compile(r"physical address|физический адрес|duid|iaid|\bether\b", re.IGNORECASE)
WIFI_IDENTITY_RE = re.compile(r"^\s*(b?ssid|profile|профиль|идентификатор guid|guid|physical address|физический адрес)\b", re.IGNORECASE)
SLOW_PROBE_MS = (1000, 3000)
PROBLEM_PROBE_MS = SLOW_PROBE_MS[1]
GROUP_NAMES = {"gateway": "шлюз (роутер)", "yandex": "Яндекс", "control": "контрольные хосты"}


def sanitize_text(text: str, secrets: tuple[str, ...] | list[str] = ()) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    text = OAUTH_RE.sub("OAuth ***", text)
    text = YANDEX_TOKEN_RE.sub("***", text)
    text = SIGNED_URL_RE.sub(r"\1/…", text)
    return URL_CREDENTIALS_RE.sub("://***@", text)


def drop_private_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not PRIVATE_LINE_RE.search(line))


def drop_wifi_identity(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not WIFI_IDENTITY_RE.search(line))


def percentile(values: list[int], share: float) -> int:
    ordered = sorted(values)
    return ordered[max(math.ceil(share * len(ordered)) - 1, 0)]


def describe_timings(values: list[int]) -> str:
    if not values:
        return "нет данных"
    return (f"p50 {percentile(values, 0.5)}, p90 {percentile(values, 0.9)}, p99 {percentile(values, 0.99)}, "
            f"max {max(values)} мс")


def describe_errors(errors: Counter) -> str:
    return ", ".join(f"{name} ×{count}" for name, count in errors.most_common())


def summarize_probes(samples: list[dict]) -> list[str]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for sample in samples:
        if sample.get("kind") == "soak":
            groups[sample["host"]].append(sample)
    lines: list[str] = []
    for host, items in groups.items():
        failed = [item for item in items if not item["ok"]]
        slow = [sum(1 for item in items if item.get("total_ms", 0) > limit) for limit in SLOW_PROBE_MS]
        lines.append(f"{host}: проб {len(items)}, неудач {len(failed)}, дольше {SLOW_PROBE_MS[0] // 1000} с: {slow[0]}, "
                     f"дольше {SLOW_PROBE_MS[1] // 1000} с: {slow[1]}")
        lines.append(f"    весь запрос (успешные): {describe_timings([item['total_ms'] for item in items if item['ok']])}")
        tcp_timings = [item["tcp_ms"] for item in items if "tcp_ms" in item]
        if tcp_timings:
            lines.append(f"    TCP-подключение: {describe_timings(tcp_timings)}")
        if failed:
            lines.append("    ошибки: " + describe_errors(
                Counter(f"{item['stage']}/{item.get('qt_error') or 'без кода'}" for item in failed)))
    return lines


def summarize_correlation(samples: list[dict]) -> list[str]:
    cycles: dict[int, set[str]] = defaultdict(set)
    for sample in samples:
        if sample.get("kind") == "soak" and "cycle" in sample:
            bad = cycles[sample["cycle"]]
            if not sample["ok"] or sample.get("total_ms", 0) > PROBLEM_PROBE_MS:
                bad.add(sample["group"])
    if not cycles:
        return []
    combinations = Counter(tuple(group for group in GROUP_NAMES if group in bad) for bad in cycles.values() if bad)
    lines = [f"Циклов наблюдения {len(cycles)}, с проблемой (сбой или дольше {PROBLEM_PROBE_MS // 1000} с) "
             f"{sum(combinations.values())}:"]
    lines.extend(f"    {' + '.join(GROUP_NAMES[group] for group in combination)}: {count}"
                 for combination, count in combinations.most_common())
    return lines


def summarize_wifi(samples: list[dict]) -> list[str]:
    signals = [sample["signal"] for sample in samples if sample.get("kind") == "wifi"]
    if not signals:
        return []
    return [f"Сигнал Wi-Fi: замеров {len(signals)}, минимум {min(signals)} %, медиана {percentile(signals, 0.5)} %"]


def summarize_attempts(samples: list[dict]) -> list[str]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for sample in samples:
        if sample.get("kind") == "attempt":
            groups[sample["label"]].append(sample)
    lines: list[str] = []
    for label, items in groups.items():
        failed = [item for item in items if item.get("status") is None]
        retried = sum(1 for item in items if item["attempt"] > 1)
        lines.append(f"{label}: попыток {len(items)}, неудачных {len(failed)}, повторных {retried}; "
                     f"успешные: {describe_timings([item['ms'] for item in items if item.get('status') is not None])}")
        if failed:
            lines.append("    ошибки: " + describe_errors(Counter(item.get("qt_error") or "без кода" for item in failed)))
    return lines


def summarize_operations(samples: list[dict]) -> list[str]:
    operations = [sample for sample in samples if sample.get("kind") == "op"]
    if not operations:
        return []
    failed = [sample for sample in operations if not sample["ok"]]
    lines = [f"Операции целиком: {len(operations)}, с ошибкой {len(failed)}"]
    lines.extend(f"    {sample['label']}: {sample['error']}" for sample in failed)
    return lines


class DiagReport:
    def __init__(self, secrets: tuple[str, ...] = ()):
        self.started: float = time.monotonic()
        self.started_at: datetime = datetime.now()
        self.lines: list[str] = []
        self.samples: list[dict] = []
        self.secrets: tuple[str, ...] = tuple(secret for secret in secrets if secret)

    def section(self, title: str) -> None:
        self.lines.extend(["", f"=== {title} ==="])

    def line(self, text: str = "") -> None:
        self.lines.append(text)

    def sample(self, kind: str, **data) -> None:
        self.samples.append({"t": round(time.monotonic() - self.started, 1), "kind": kind, **data})

    def summary_lines(self) -> list[str]:
        return (summarize_operations(self.samples) + summarize_attempts(self.samples)
                + summarize_correlation(self.samples) + summarize_wifi(self.samples) + summarize_probes(self.samples))

    def text(self) -> str:
        duration = int(time.monotonic() - self.started)
        header = ["Диагностика сети «Платежного календаря»",
                  f"Начало: {self.started_at:%Y-%m-%d %H:%M:%S}, длительность {duration} с",
                  "", "=== СВОДКА ==="]
        summary = self.summary_lines() or ["нет данных для сводки"]
        return sanitize_text("\n".join(header + summary + self.lines), self.secrets)

    def samples_text(self) -> str:
        return sanitize_text("\n".join(json.dumps(sample, ensure_ascii=False) for sample in self.samples), self.secrets)


def read_tail(path: Path, max_bytes: int) -> str:
    try:
        with open(path, "rb") as file:
            file.seek(max(path.stat().st_size - max_bytes, 0))
            return file.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def collect_log_text(logs_folder: Path, max_bytes: int) -> str:
    parts: list[str] = []
    remaining = max_bytes
    for name in ("log.log", "log.log.1"):
        chunk = read_tail(logs_folder / name, remaining)
        parts.insert(0, chunk)
        remaining -= len(chunk.encode("utf-8"))
        if remaining <= 0:
            break
    return "".join(parts)


def save_report(report: DiagReport, folder: Path, log_text: str = "", errors_text: str = "") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"netdiag_{report.started_at:%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("report.txt", report.text())
        archive.writestr("samples.jsonl", report.samples_text())
        archive.writestr("app_log.txt", sanitize_text(log_text, report.secrets))
        archive.writestr("sys_errors.txt", sanitize_text(errors_text, report.secrets))
    return path
