import os
import sys

import pytest

import base.backup as backupmod
from base.lockinfo import lock_holders

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Restart Manager есть только в Windows")


@windows_only
def test_lock_holders_sees_own_process(tmp_path):
    busy = tmp_path / "busy.db"
    busy.write_bytes(b"data")
    assert lock_holders(busy) == "не найдены"
    with open(busy, "rb"):
        assert f"PID {os.getpid()}, наш процесс" in lock_holders(busy)
    assert lock_holders(busy) == "не найдены"


@windows_only
def test_rename_with_retry_logs_diagnostics_for_busy_file(tmp_path, monkeypatch):
    busy = tmp_path / "db.db"
    busy.write_bytes(b"data")
    messages: list[str] = []
    monkeypatch.setattr(backupmod, "RENAME_ATTEMPTS", 3)
    monkeypatch.setattr(backupmod, "RENAME_PAUSE_SECONDS", 0)
    monkeypatch.setattr(backupmod.log, "w", messages.append)
    with open(busy, "rb"):
        with pytest.raises(PermissionError):
            backupmod.rename_with_retry(busy, tmp_path / "db_temp.db")
    diagnostics = [text for text in messages if text.startswith("Диагностика занятого файла db.db")]
    assert len(diagnostics) == 2
    assert "попытка 1 из 3" in diagnostics[0] and "попытка 3 из 3" in diagnostics[1]
    assert "db.db (4 байт)" in diagnostics[0]
    assert "наш процесс" in diagnostics[0]


def test_lock_holders_never_raises(tmp_path):
    assert isinstance(lock_holders(tmp_path / "missing.db"), str)
