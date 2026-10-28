import json
import os
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from platform import node
from typing import TYPE_CHECKING

import lovely_logger as log

from base.paths import sync_install_id_path, sync_journal_path, sync_journal_uploaded_path

if TYPE_CHECKING:
    from base.sync import SyncChannel

JOURNAL_KEEP_DAYS = 7
JOURNAL_DIR = "journal"
JOURNAL_START = "start"
JOURNAL_EXIT = "exit"
JOURNAL_MANUAL = "manual"
JOURNAL_AUTO = "auto"


def load_install(machine: str) -> tuple[str, str]:
    path = Path(sync_install_id_path())
    try:
        lines = path.read_text(encoding="utf-8").split()
    except OSError:
        lines = []
    value = lines[0] if lines else uuid.uuid4().hex[:6]
    label = lines[1] if len(lines) > 1 else re.sub(r"[^\w.-]", "_", machine)
    if len(lines) < 2:
        try:
            path.write_text(f"{value}\n{label}", encoding="utf-8")
        except OSError as e:
            log.w(f"Не удалось сохранить идентификатор установки: {e}")
    return value, label


def install_id() -> str:
    return load_install(node())[0]


def journal_remote_name(machine: str) -> str:
    value, label = load_install(machine)
    return f"{label}-{value}.jsonl"


def journal_upload_due() -> bool:
    try:
        uploaded = date.fromisoformat(Path(sync_journal_uploaded_path()).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return True
    return uploaded < date.today()


def upload_journal_if_due(channel: "SyncChannel", machine: str) -> None:
    path = Path(sync_journal_path())
    if not path.is_file() or not journal_upload_due():
        return
    try:
        channel.upload_journal(path, journal_remote_name(machine))
        Path(sync_journal_uploaded_path()).write_text(date.today().isoformat(), encoding="utf-8")
    except Exception as e:
        log.w(f"Не удалось выгрузить журнал обращений к общей базе: {e}")


def entry_time(line: str) -> datetime | None:
    try:
        return datetime.fromisoformat(json.loads(line)["time"]).astimezone()
    except (ValueError, KeyError, TypeError):
        return None


def is_fresh(line: str, cutoff: datetime) -> bool:
    time_value = entry_time(line)
    return time_value is None or time_value >= cutoff


def add_journal_entry(author: str, machine: str, event: str, result: str, path: Path | None = None) -> None:
    path = path or Path(sync_journal_path())
    entry = {"time": datetime.now().astimezone().isoformat(timespec="seconds"), "author": author, "machine": machine, "event": event, "result": result}
    cutoff = datetime.now().astimezone() - timedelta(days=JOURNAL_KEEP_DAYS)
    try:
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        lines = [line for line in lines if line.strip() and is_fresh(line, cutoff)]
        lines.append(json.dumps(entry, ensure_ascii=False))
        temp = path.with_name(path.name + ".tmp")
        temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(temp, path)
    except OSError as e:
        log.w(f"Не удалось записать журнал обращений к общей базе: {e}")
