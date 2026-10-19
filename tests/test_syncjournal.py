import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from base.sync import FolderChannel, SyncAction, SyncError, SyncParams, push_master, synchronize
from base.syncjournal import add_journal_entry
from tests.test_sync_flow import make_machine, patch_backup_dir  # noqa: F401

PARAMS = SyncParams("Автор", "PC-1", "2026.10.04")


def read_journal(tmp_path: Path) -> list[dict]:
    lines = (tmp_path / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def test_entry_is_appended(tmp_path):
    add_journal_entry("Автор", "PC-1", "start", "push")
    add_journal_entry("Автор", "PC-1", "exit", "no_changes")
    entries = read_journal(tmp_path)
    assert [entry["result"] for entry in entries] == ["push", "no_changes"]
    assert entries[0]["author"] == "Автор"
    assert entries[0]["machine"] == "PC-1"


def test_old_entries_are_removed(tmp_path):
    old = (datetime.now() - timedelta(days=8)).isoformat(timespec="seconds")
    recent = (datetime.now() - timedelta(days=6)).isoformat(timespec="seconds")
    lines = [json.dumps({"time": time, "author": "A", "machine": "M", "result": "pull"}) for time in (old, recent)]
    (tmp_path / "journal.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    add_journal_entry("A", "M", "start", "push")
    entries = read_journal(tmp_path)
    assert [entry["time"] for entry in entries[:1]] == [recent]
    assert [entry["result"] for entry in entries] == ["pull", "push"]


def test_synchronize_writes_result(tmp_path, dbh):
    channel = FolderChannel(tmp_path / "cloud")
    with pytest.raises(SyncError):
        synchronize(dbh, channel, PARAMS, journal_tag="start")
    entries = read_journal(tmp_path)
    assert [(entry["event"], entry["result"]) for entry in entries] == [("start", "SyncError")]


def test_journal_uploaded_once_a_day(tmp_path, make_machine):
    channel = FolderChannel(tmp_path / "cloud")
    uploaded = tmp_path / "cloud" / "journal" / "PC-1.jsonl"
    with make_machine("a") as dbh:
        synchronize(dbh, channel, PARAMS, journal_tag="start")
        assert uploaded.is_file()
        synchronize(dbh, channel, PARAMS, journal_tag="start")
        assert len(uploaded.read_text(encoding="utf-8").splitlines()) == 1
        (tmp_path / "journal_uploaded.txt").write_text("2000-01-01", encoding="utf-8")
        synchronize(dbh, channel, PARAMS, journal_tag="start")
        assert len(uploaded.read_text(encoding="utf-8").splitlines()) == 3


def test_failed_journal_upload_is_repeated_and_does_not_break_sync(tmp_path, make_machine):
    channel = FolderChannel(tmp_path / "cloud")

    def broken_upload(source, name):
        raise SyncError("нет связи")

    with make_machine("a") as dbh:
        channel.upload_journal = broken_upload
        synchronize(dbh, channel, PARAMS, journal_tag="start")
        assert not (tmp_path / "journal_uploaded.txt").exists()
        del channel.upload_journal
        synchronize(dbh, channel, PARAMS, journal_tag="start")
        assert (tmp_path / "journal_uploaded.txt").exists()


def test_automatic_nothing_is_not_journaled(tmp_path, make_machine):
    channel = FolderChannel(tmp_path / "cloud")
    with make_machine("a") as dbh:
        push_master(dbh, channel, PARAMS)
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    assert not (tmp_path / "journal.jsonl").exists()


def test_tagged_nothing_is_journaled(tmp_path, make_machine):
    channel = FolderChannel(tmp_path / "cloud")
    with make_machine("a") as dbh:
        push_master(dbh, channel, PARAMS)
        synchronize(dbh, channel, PARAMS, journal_tag="exit")
    assert [(entry["event"], entry["result"]) for entry in read_journal(tmp_path)] == [("exit", "nothing")]


def test_automatic_other_results_are_journaled(tmp_path, make_machine):
    channel = FolderChannel(tmp_path / "cloud")
    with make_machine("a") as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NO_MASTER
    assert [(entry["event"], entry["result"]) for entry in read_journal(tmp_path)] == [("auto", "no_master")]
