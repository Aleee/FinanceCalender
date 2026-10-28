import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtNetwork import QNetworkReply

import base.updater as updmod
from base.updater import NetworkError, UpdateChecker, UpdateDownloader, UpdateError, UpdateInfo
from base.version import DB_VERSION
from tests.test_updater import FULL_ARCHIVE, build_archive, make_version

UPDATER_PATH = Path(__file__).resolve().parent.parent / "updater" / "updater.py"
NoError = QNetworkReply.NetworkError.NoError
HostNotFound = QNetworkReply.NetworkError.HostNotFoundError


@pytest.fixture
def raw_updater():
    spec = importlib.util.spec_from_file_location("updater_exe_raw", UPDATER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.started = []
    module.errors = []
    yield module
    for handler in list(module.log.handlers):
        module.log.removeHandler(handler)
        handler.close()
    module.set_app_exe("FinanceCalender.exe")


@pytest.fixture
def stand(tmp_path):
    app_dir = tmp_path / "app"
    new_dir = app_dir / "update" / "new"
    make_version(app_dir, "FinanceCalender.exe", "old")
    (app_dir / "data").mkdir()
    (app_dir / "data" / "db.db").write_text("user data")
    make_version(new_dir, "FinanceCalender.exe", "new")
    return app_dir, new_dir


@pytest.fixture
def stubbed(raw_updater, monkeypatch):
    monkeypatch.setattr(raw_updater, "start_app", lambda app_dir: raw_updater.started.append(app_dir))
    monkeypatch.setattr(raw_updater, "show_error", raw_updater.errors.append)
    monkeypatch.setattr(raw_updater.time, "sleep", lambda seconds: None)
    return raw_updater


def test_timeout_waiting_for_app_changes_nothing(stubbed, stand, monkeypatch):
    app_dir, new_dir = stand
    monkeypatch.setattr(stubbed, "wait_for_process", lambda pid, timeout: False)
    assert stubbed.run_update(1, app_dir, new_dir, 1) == 2
    assert (app_dir / "FinanceCalender.exe").read_text() == "old"
    assert (new_dir / "FinanceCalender.exe").read_text() == "new"
    assert not (new_dir.parent / "old").exists()
    assert stubbed.started == []
    assert len(stubbed.errors) == 1


def test_failed_rollback_keeps_old_files_and_reports_error(stubbed, stand, monkeypatch):
    app_dir, new_dir = stand
    monkeypatch.setattr(stubbed, "wait_for_process", lambda pid, timeout: True)
    calls = []

    def failing_rename(source, target):
        calls.append(source)
        if len(calls) == 4:
            raise OSError("locked")
        os.rename(source, target)

    def broken_rename(source, target):
        raise OSError("rollback impossible")

    monkeypatch.setattr(stubbed, "rename_with_retries", failing_rename)
    monkeypatch.setattr(stubbed, "os", SimpleNamespace(rename=broken_rename))
    assert stubbed.run_update(1, app_dir, new_dir, 1) == 1
    old_dir = new_dir.parent / "old"
    assert (old_dir / "FinanceCalender.exe").read_text() == "old"
    assert (old_dir / "_internal" / "lib.dll").read_text() == "old"
    assert (app_dir / "data" / "db.db").read_text() == "user data"
    assert len(stubbed.errors) == 1


def test_rollback_raises_update_error_when_rename_fails(stubbed, tmp_path, monkeypatch):
    def broken_rename(source, target):
        raise OSError("x")

    monkeypatch.setattr(stubbed, "os", SimpleNamespace(rename=broken_rename))
    with pytest.raises(stubbed.UpdateError):
        stubbed.rollback(tmp_path, tmp_path, tmp_path, ["FinanceCalender.exe"], [])


def test_rename_with_retries_succeeds_after_failures(stubbed, tmp_path, monkeypatch):
    attempts = []
    sleeps = []

    def flaky_rename(source, target):
        attempts.append(source)
        if len(attempts) < 3:
            raise PermissionError("busy")

    monkeypatch.setattr(stubbed.os, "rename", flaky_rename)
    monkeypatch.setattr(stubbed.time, "sleep", sleeps.append)
    stubbed.rename_with_retries(tmp_path / "a", tmp_path / "b")
    assert len(attempts) == 3 and len(sleeps) == 2


def test_rename_with_retries_gives_up(stubbed, tmp_path, monkeypatch):
    attempts = []

    def always_busy(source, target):
        attempts.append(source)
        raise PermissionError("busy")

    monkeypatch.setattr(stubbed.os, "rename", always_busy)
    with pytest.raises(PermissionError):
        stubbed.rename_with_retries(tmp_path / "a", tmp_path / "b")
    assert len(attempts) == stubbed.MOVE_ATTEMPTS


def test_clean_up_removes_work_folders_and_archives_only(stubbed, tmp_path):
    update_dir = tmp_path / "update"
    new_dir, old_dir = update_dir / "new", update_dir / "old"
    for folder in (new_dir, old_dir):
        folder.mkdir(parents=True)
        (folder / "file.txt").write_text("x")
    (update_dir / "app.zip").write_text("zip")
    (update_dir / "updater.exe").write_text("exe")
    stubbed.clean_up(new_dir, old_dir)
    assert not new_dir.exists() and not old_dir.exists()
    assert not (update_dir / "app.zip").exists()
    assert (update_dir / "updater.exe").exists()


def test_start_app_survives_launch_failure(raw_updater, tmp_path, monkeypatch):
    def failing_popen(*args, **kwargs):
        raise OSError("no exe")

    monkeypatch.setattr(raw_updater.subprocess, "Popen", failing_popen)
    raw_updater.start_app(tmp_path)


def test_setup_logging_writes_to_file(raw_updater, tmp_path):
    raw_updater.setup_logging(tmp_path)
    raw_updater.log.info("проверка")
    for handler in raw_updater.log.handlers:
        handler.flush()
    assert "проверка" in (tmp_path / "data" / "logs" / "updater.log").read_text(encoding="utf-8")


def test_setup_logging_falls_back_to_stream_when_folder_is_unwritable(raw_updater, tmp_path):
    (tmp_path / "data").write_text("файл вместо папки")
    raw_updater.setup_logging(tmp_path)
    assert [type(handler) for handler in raw_updater.log.handlers] == [logging.StreamHandler]


def test_main_passes_arguments_and_updates(stubbed, stand, monkeypatch):
    app_dir, new_dir = stand
    monkeypatch.setattr(stubbed, "wait_for_process", lambda pid, timeout: True)
    monkeypatch.setattr(stubbed, "setup_logging", lambda folder: None)
    monkeypatch.setattr(sys, "argv", ["updater", "--pid", "7", "--app-dir", str(app_dir), "--new-dir", str(new_dir),
                                      "--silent", "--app-exe", "FinanceCalender.exe"])
    assert stubbed.main() == 0
    assert stubbed.silent
    assert (app_dir / "FinanceCalender.exe").read_text() == "new"
    assert stubbed.started == [app_dir.resolve()]


class FakeReply:

    def __init__(self, data: bytes = b"", error=NoError, text: str = ""):
        self.data, self._error, self.text = data, error, text
        self.deleted = False
        self.aborted = False

    def error(self):
        return self._error

    def errorString(self):
        return self.text

    def readAll(self):
        return self.data

    def deleteLater(self):
        self.deleted = True

    def abort(self):
        self.aborted = True


def version_reply(version: str, db_version: int = DB_VERSION) -> FakeReply:
    raw = f'{{"version": "{version}", "db_version": {db_version}, "file": "app.zip", "sha256": "abc"}}'
    return FakeReply(raw.encode("utf-8"))


@pytest.fixture
def checker(qapp, monkeypatch):
    scheduled = []
    monkeypatch.setattr(updmod.QTimer, "singleShot", lambda delay, callback: scheduled.append(callback))
    result = UpdateChecker()
    result.scheduled = scheduled
    result.found = []
    result.update_available.connect(result.found.append)
    result.checking = True
    result.attempt = 1
    return result


def test_newer_version_is_offered(checker):
    reply = version_reply("2999.01.01")
    checker.on_version_received(reply)
    assert [info.version for info in checker.found] == ["2999.01.01"]
    assert not checker.checking and reply.deleted
    assert "2999.01.01" in checker.last_check_result


def test_same_or_older_version_is_not_offered(checker):
    checker.on_version_received(version_reply("2000.01.01"))
    assert checker.found == [] and not checker.checking
    assert checker.last_check_status.endswith("актуальная версия")


def test_update_for_older_database_is_not_offered(checker):
    checker.on_version_received(version_reply("2999.01.01", DB_VERSION - 1))
    assert checker.found == [] and not checker.checking
    assert "несовместима" in checker.last_check_result


def test_broken_version_file_ends_check_without_retry(checker):
    checker.on_version_received(FakeReply(b"not json"))
    assert checker.found == [] and not checker.checking and checker.scheduled == []
    assert checker.last_check_status.endswith("ошибка")


def test_network_error_is_retried_then_gives_up(checker):
    for attempt in range(1, updmod.CHECK_ATTEMPTS):
        checker.on_version_received(FakeReply(error=HostNotFound, text="down"))
        assert checker.checking and checker.attempt == attempt + 1
        assert len(checker.scheduled) == attempt
    checker.on_version_received(FakeReply(error=HostNotFound, text="down"))
    assert not checker.checking and checker.found == []
    assert len(checker.scheduled) == updmod.CHECK_ATTEMPTS - 1


def test_check_is_disabled_without_public_key(checker, monkeypatch):
    checker.checking = False
    monkeypatch.setattr(updmod, "PUBLIC_KEY", "")
    finished = []
    checker.check_finished.connect(lambda: finished.append(True))
    checker.check()
    assert finished == [True] and not checker.checking


def test_check_does_not_start_twice(checker, monkeypatch):
    monkeypatch.setattr(checker, "request_link", lambda: pytest.fail("second request"))
    checker.check()


def test_read_download_link():
    assert updmod.read_download_link(FakeReply(b'{"href": "https://x/y"}')) == "https://x/y"
    with pytest.raises(NetworkError):
        updmod.read_download_link(FakeReply(error=HostNotFound))
    for bad in (b"[]", b'{"no": 1}', b"\xff"):
        with pytest.raises(UpdateError) as caught:
            updmod.read_download_link(FakeReply(bad))
        assert not isinstance(caught.value, NetworkError)


@pytest.mark.skipif(sys.platform == "darwin", reason="на macOS другой запуск")
def test_launch_updater_copies_and_starts_with_arguments(tmp_path, monkeypatch):
    new = tmp_path / "update" / "new"
    new.mkdir(parents=True)
    (new / "updater.exe").write_text("updater")
    monkeypatch.setattr(updmod, "update_dir", lambda: str(tmp_path / "update"))
    monkeypatch.setattr(updmod, "new_dir", lambda: str(new))
    monkeypatch.setattr(updmod, "app_dir", lambda: str(tmp_path))
    started = []
    monkeypatch.setattr(updmod.subprocess, "Popen", lambda command, **kwargs: started.append(command))
    updmod.launch_updater()
    command = started[0]
    assert command[0] == str(tmp_path / "update" / "updater.exe")
    assert command[command.index("--new-dir") + 1] == str(new)
    assert command[command.index("--app-dir") + 1] == str(tmp_path)
    assert command[command.index("--app-exe") + 1] == updmod.APP_EXE
    assert (tmp_path / "update" / "updater.exe").read_text() == "updater"


@pytest.mark.skipif(sys.platform == "darwin", reason="на macOS другой запуск")
def test_launch_updater_reports_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(updmod, "update_dir", lambda: str(tmp_path / "update"))
    monkeypatch.setattr(updmod, "new_dir", lambda: str(tmp_path / "update" / "new"))
    with pytest.raises(UpdateError):
        updmod.launch_updater()


@pytest.fixture
def downloader(qapp, tmp_path, monkeypatch):
    (tmp_path / "update").mkdir()
    monkeypatch.setattr(updmod, "update_dir", lambda: str(tmp_path / "update"))
    monkeypatch.setattr(updmod, "new_dir", lambda: str(tmp_path / "update" / "new"))
    monkeypatch.setattr(updmod.QTimer, "singleShot", lambda delay, callback: None)
    result = UpdateDownloader()
    result.messages = []
    result.readied = []
    result.failed.connect(result.messages.append)
    result.ready.connect(result.readied.append)
    return result


def info_for(tmp_path, names=FULL_ARCHIVE, sha256=None) -> UpdateInfo:
    digest = build_archive(tmp_path / "update" / "app.zip", names)
    return UpdateInfo("2999.01.01", DB_VERSION, "app.zip", sha256 or digest, "")


class ClosableFile:

    def write(self, data):
        return len(data)

    def close(self):
        pass


def test_start_reports_unwritable_folder(downloader, monkeypatch):
    def refuse():
        raise OSError("read only")

    monkeypatch.setattr(downloader, "prepare_update_dir", refuse)
    monkeypatch.setattr(downloader, "request_link", lambda: pytest.fail("request after failure"))
    downloader.start(UpdateInfo("2999.01.01", DB_VERSION, "app.zip", "abc", ""))
    assert len(downloader.messages) == 1 and "папку программы" in downloader.messages[0]


def test_retry_is_limited(downloader):
    downloader.attempt = 1
    assert downloader.retry() and downloader.retry()
    assert downloader.attempt == updmod.NETWORK_ATTEMPTS
    assert not downloader.retry()


def test_cancel_aborts_reply_and_silences_failure(downloader, tmp_path):
    downloader.info = info_for(tmp_path)
    reply = FakeReply(error=HostNotFound)
    downloader.reply = reply
    downloader.file = ClosableFile()
    downloader.cancel()
    assert reply.aborted
    downloader.on_download_finished()
    assert downloader.messages == [] and downloader.readied == []


def test_network_error_during_download_is_retried_then_reported(downloader, tmp_path):
    downloader.info = info_for(tmp_path)
    downloader.attempt = 1
    for _ in range(updmod.NETWORK_ATTEMPTS - 1):
        downloader.reply = FakeReply(error=HostNotFound, text="reset")
        downloader.file = ClosableFile()
        downloader.on_download_finished()
        assert downloader.messages == []
    downloader.reply = FakeReply(error=HostNotFound, text="reset")
    downloader.file = ClosableFile()
    downloader.on_download_finished()
    assert len(downloader.messages) == 1 and "скачать" in downloader.messages[0]
    assert downloader.readied == []


def test_corrupted_download_is_not_installed(downloader, tmp_path):
    downloader.info = info_for(tmp_path, sha256="0" * 64)
    downloader.reply = FakeReply()
    downloader.file = ClosableFile()
    downloader.on_download_finished()
    assert len(downloader.messages) == 1 and "повреждён" in downloader.messages[0]
    assert downloader.readied == []
    assert not (tmp_path / "update" / "new").exists()


@pytest.mark.skipif(sys.platform == "darwin", reason="на macOS распаковка отличается")
def test_good_download_is_extracted_and_reported_ready(downloader, tmp_path):
    downloader.info = info_for(tmp_path)
    downloader.reply = FakeReply()
    downloader.file = ClosableFile()
    downloader.on_download_finished()
    assert downloader.messages == []
    assert downloader.readied == [str(tmp_path / "update" / "new")]
    assert (tmp_path / "update" / "new" / "updater.exe").exists()


def test_download_link_after_cancel_is_ignored(downloader, tmp_path):
    downloader.info = info_for(tmp_path)
    downloader.cancelled = True
    reply = FakeReply(error=HostNotFound)
    downloader.on_link_received(reply)
    assert reply.deleted and downloader.messages == []


def test_link_errors_are_retried_then_reported(downloader, tmp_path):
    downloader.info = info_for(tmp_path)
    downloader.attempt = updmod.NETWORK_ATTEMPTS
    downloader.on_link_received(FakeReply(error=HostNotFound))
    assert len(downloader.messages) == 1 and "Яндекс.Диском" in downloader.messages[0]
    downloader.messages.clear()
    downloader.attempt = 1
    downloader.on_link_received(FakeReply(error=HostNotFound))
    assert downloader.messages == [] and downloader.attempt == 2
