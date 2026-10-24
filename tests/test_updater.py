import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

import base.updater as updmod
from base.updater import UpdateDownloader, UpdateError, UpdateInfo

UPDATER_PATH = Path(__file__).resolve().parent.parent / "updater" / "updater.py"


@pytest.fixture
def updater(monkeypatch):
    spec = importlib.util.spec_from_file_location("updater_exe", UPDATER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.started = []
    module.errors = []
    monkeypatch.setattr(module, "wait_for_process", lambda pid, timeout: True)
    monkeypatch.setattr(module, "start_app", lambda app_dir: module.started.append(app_dir))
    monkeypatch.setattr(module, "show_error", module.errors.append)
    yield module
    module.set_app_exe("FinanceCalender.exe")


def make_version(folder: Path, exe: str, label: str, with_internal: bool = True) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / exe).write_text(label)
    if with_internal:
        (folder / "_internal").mkdir()
        (folder / "_internal" / "lib.dll").write_text(label)


@pytest.fixture
def stand(tmp_path):
    app_dir = tmp_path / "app"
    new_dir = app_dir / "update" / "new"
    make_version(app_dir, "FinanceCalender.exe", "old")
    (app_dir / "data").mkdir()
    (app_dir / "data" / "db.db").write_text("user data")
    make_version(new_dir, "FinanceCalender.exe", "new")
    return app_dir, new_dir


def test_update_replaces_files_and_keeps_data(updater, stand):
    app_dir, new_dir = stand
    assert updater.run_update(1, app_dir, new_dir, 1) == 0
    assert (app_dir / "FinanceCalender.exe").read_text() == "new"
    assert (app_dir / "_internal" / "lib.dll").read_text() == "new"
    assert (app_dir / "data" / "db.db").read_text() == "user data"
    assert not new_dir.exists()
    assert updater.started == [app_dir]
    assert updater.errors == []


def test_failed_replacement_rolls_back(updater, stand, monkeypatch):
    app_dir, new_dir = stand
    original = updater.rename_with_retries
    calls = []

    def failing_rename(*args, **kwargs):
        calls.append(args)
        if len(calls) == 4:
            raise OSError("locked")
        return original(*args, **kwargs)

    monkeypatch.setattr(updater, "rename_with_retries", failing_rename)
    assert updater.run_update(1, app_dir, new_dir, 1) == 1
    assert (app_dir / "FinanceCalender.exe").read_text() == "old"
    assert (app_dir / "_internal" / "lib.dll").read_text() == "old"
    assert (app_dir / "data" / "db.db").read_text() == "user data"
    assert updater.started == [app_dir]
    assert len(updater.errors) == 1


def test_update_refused_when_new_files_incomplete(updater, stand):
    app_dir, new_dir = stand
    (new_dir / "_internal" / "lib.dll").unlink()
    (new_dir / "_internal").rmdir()
    assert updater.run_update(1, app_dir, new_dir, 1) == 2
    assert (app_dir / "FinanceCalender.exe").read_text() == "old"
    assert updater.started == [app_dir]


def test_update_refused_when_new_files_contain_data(updater, stand):
    app_dir, new_dir = stand
    (new_dir / "data").mkdir()
    assert updater.run_update(1, app_dir, new_dir, 1) == 2
    assert (app_dir / "FinanceCalender.exe").read_text() == "old"
    assert (app_dir / "data" / "db.db").read_text() == "user data"


def test_viewer_executable_is_replaced(updater, tmp_path):
    app_dir = tmp_path / "app"
    new_dir = app_dir / "update" / "new"
    make_version(app_dir, "FinanceCalenderViewer.exe", "old")
    make_version(new_dir, "FinanceCalenderViewer.exe", "new")
    updater.set_app_exe("FinanceCalenderViewer.exe")
    assert updater.run_update(1, app_dir, new_dir, 1) == 0
    assert (app_dir / "FinanceCalenderViewer.exe").read_text() == "new"


def version_json(**changes) -> bytes:
    values = {"version": "2030.01.01", "db_version": 11, "file": "app.zip", "sha256": "ABC", "notes": "text"}
    values.update(changes)
    return json.dumps(values).encode("utf-8")


def test_update_info_parsed():
    info = UpdateInfo.from_json(version_json())
    assert (info.version, info.db_version, info.file, info.notes) == ("2030.01.01", 11, "app.zip", "text")
    assert info.sha256.lower() == "abc"


@pytest.mark.parametrize("file", ["../app.zip", "folder/app.zip", "C:\\app.zip", ""])
def test_update_info_rejects_unsafe_file_name(file):
    with pytest.raises(UpdateError):
        UpdateInfo.from_json(version_json(file=file))


@pytest.mark.parametrize("raw", [b"not json", b"{}"])
def test_update_info_rejects_broken_json(raw):
    with pytest.raises(UpdateError):
        UpdateInfo.from_json(raw)


def build_archive(path: Path, names: list[str]) -> str:
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, "x")
    return hashlib.sha256(path.read_bytes()).hexdigest()


FULL_ARCHIVE = ["FinanceCalender.exe", "_internal/lib.dll", "updater.exe"]


@pytest.fixture
def downloader(qapp, tmp_path, monkeypatch):
    (tmp_path / "update").mkdir()
    monkeypatch.setattr(updmod, "update_dir", lambda: str(tmp_path / "update"))
    monkeypatch.setattr(updmod, "new_dir", lambda: str(tmp_path / "update" / "new"))
    return UpdateDownloader()


def prepare(downloader, tmp_path, names, sha256=None) -> None:
    digest = build_archive(tmp_path / "update" / "app.zip", names)
    downloader.info = UpdateInfo("2030.01.01", 11, "app.zip", sha256 or digest, "")


@pytest.mark.skipif(sys.platform == "darwin", reason="на macOS распаковка отличается")
class TestVerifyAndExtract:

    def test_valid_archive_is_extracted(self, downloader, tmp_path):
        prepare(downloader, tmp_path, FULL_ARCHIVE)
        downloader.verify_and_extract()
        assert (tmp_path / "update" / "new" / "_internal" / "lib.dll").exists()

    def test_wrong_checksum(self, downloader, tmp_path):
        prepare(downloader, tmp_path, FULL_ARCHIVE, sha256="0" * 64)
        with pytest.raises(UpdateError):
            downloader.verify_and_extract()
        assert not (tmp_path / "update" / "new").exists()

    def test_broken_zip(self, downloader, tmp_path):
        (tmp_path / "update" / "app.zip").write_bytes(b"not a zip")
        downloader.info = UpdateInfo("2030.01.01", 11, "app.zip", hashlib.sha256(b"not a zip").hexdigest(), "")
        with pytest.raises(UpdateError):
            downloader.verify_and_extract()

    @pytest.mark.parametrize("missing", ["updater.exe", "FinanceCalender.exe", "_internal/lib.dll"])
    def test_archive_without_required_item(self, downloader, tmp_path, missing):
        prepare(downloader, tmp_path, [name for name in FULL_ARCHIVE if name != missing])
        with pytest.raises(UpdateError):
            downloader.verify_and_extract()

    def test_archive_with_data_folder(self, downloader, tmp_path):
        prepare(downloader, tmp_path, FULL_ARCHIVE + ["data/db/db.db"])
        with pytest.raises(UpdateError):
            downloader.verify_and_extract()
