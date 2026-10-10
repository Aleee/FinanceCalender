from datetime import datetime, timedelta
from pathlib import Path

import pytest

from base.sync import (BACKUP_TIME_FORMAT, PRECISE_BACKUP_TIME_FORMAT, FolderChannel, LocalState, MasterInfo, SyncAction,
                       SyncError, backup_time_from_name, backups_cleanup_due, decide_action, read_local_state)
from tests.dbtools import create_db

UUID = "uuid-1"


def local_state(token: str = "t1", changes: int = 0, uuid: str = UUID, version: int = 5) -> LocalState:
    return LocalState(uuid, token, version, changes)


def master_info(token: str = "t1", uuid: str = UUID, version: int = 5, uploaded_at: str = "2026-10-09T10:00:00") -> MasterInfo:
    return MasterInfo(uuid, token, version, "Автор", "PC-1", uploaded_at, "2026.10.04")


@pytest.mark.parametrize("master_token, changes, expected", [
    ("t1", 0, SyncAction.NOTHING),
    ("t2", 0, SyncAction.PULL),
    ("t1", 3, SyncAction.PUSH),
    ("t2", 3, SyncAction.CONFLICT),
])
def test_decide_action_state_table(master_token, changes, expected):
    assert decide_action(local_state("t1", changes), master_info(master_token)) == expected


def test_decide_action_without_master():
    assert decide_action(local_state(), None) == SyncAction.NO_MASTER


def test_decide_action_foreign_db_has_priority():
    assert decide_action(local_state("t1", 3), master_info("t2", uuid="other")) == SyncAction.FOREIGN_DB


def test_decide_action_outdated_client_has_priority_over_conflict():
    assert decide_action(local_state("t1", 3, version=5), master_info("t2", version=6)) == SyncAction.CLIENT_OUTDATED


def test_decide_action_newer_client_can_push_and_pull():
    assert decide_action(local_state("t1", 1, version=6), master_info("t1", version=5)) == SyncAction.PUSH
    assert decide_action(local_state("t1", 0, version=6), master_info("t2", version=5)) == SyncAction.PULL


def test_master_info_json_roundtrip():
    info = master_info()
    assert MasterInfo.from_json(info.to_json()) == info


@pytest.mark.parametrize("text", ["not json", "[]", '{"db_uuid": "x"}', '{"extra": 1}'])
def test_master_info_rejects_broken_json(text):
    with pytest.raises(SyncError):
        MasterInfo.from_json(text)


def test_read_local_state(dbh, work_db_path):
    create_db(work_db_path, 5, {"db_uuid": "u", "sync_token": "t", "change_counter": "4"})
    dbh.open_db_connection()
    assert read_local_state(dbh) == LocalState("u", "t", 5, 4)


def test_read_local_state_without_sync_keys(dbh, work_db_path):
    create_db(work_db_path, 4)
    dbh.open_db_connection()
    with pytest.raises(SyncError):
        read_local_state(dbh)


def test_read_local_state_with_invalid_counter(dbh, work_db_path):
    create_db(work_db_path, 5, {"db_uuid": "u", "sync_token": "t", "change_counter": "abc"})
    dbh.open_db_connection()
    with pytest.raises(SyncError):
        read_local_state(dbh)


@pytest.fixture
def channel(tmp_path: Path) -> FolderChannel:
    return FolderChannel(tmp_path / "exchange")


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    path = tmp_path / "source.db"
    path.write_bytes(b"database content" * 1000)
    return path


def test_channel_without_master_returns_none(channel):
    assert channel.read_master_info() is None


def test_channel_upload_then_read_and_download(channel, source_file, tmp_path):
    info = master_info("t9")
    channel.upload_master(source_file, info)
    assert channel.read_master_info() == info
    downloaded = tmp_path / "downloaded.db"
    channel.download_master(downloaded)
    assert downloaded.read_bytes() == source_file.read_bytes()


def test_channel_upload_leaves_no_temp_files(channel, source_file):
    channel.upload_master(source_file, master_info())
    assert sorted(item.name for item in channel.folder.iterdir()) == ["master.db", "master.json"]


def test_channel_upload_replaces_previous_master(channel, source_file, tmp_path):
    channel.upload_master(source_file, master_info("t1"))
    new_source = tmp_path / "new.db"
    new_source.write_bytes(b"new content")
    channel.upload_master(new_source, master_info("t2"))
    assert channel.read_master_info().sync_token == "t2"
    assert channel.master_db_path.read_bytes() == b"new content"


def test_channel_failed_upload_keeps_previous_master(channel, source_file, tmp_path):
    channel.upload_master(source_file, master_info("t1"))
    with pytest.raises(SyncError):
        channel.upload_master(tmp_path / "missing.db", master_info("t2"))
    assert channel.read_master_info().sync_token == "t1"
    assert channel.master_db_path.read_bytes() == source_file.read_bytes()
    assert sorted(item.name for item in channel.folder.iterdir()) == ["master.db", "master.json"]


def test_channel_db_without_info_means_no_master(channel, source_file):
    channel.folder.mkdir()
    channel.master_db_path.write_bytes(b"half uploaded")
    assert channel.read_master_info() is None


def test_channel_download_without_master_fails(channel, tmp_path):
    with pytest.raises(SyncError):
        channel.download_master(tmp_path / "downloaded.db")


def test_channel_backup_copies_current_master(channel, source_file):
    channel.backup_master()
    assert not channel.backups_path.exists()
    channel.upload_master(source_file, master_info())
    channel.backup_master()
    backups = list(channel.backups_path.iterdir())
    assert len(backups) == 1
    assert backups[0].read_bytes() == source_file.read_bytes()
    long_backups = list(channel.long_backups_path.iterdir())
    assert [item.name for item in long_backups] == [backups[0].name]


def test_only_first_backup_of_the_day_goes_to_long_folder(channel, source_file):
    channel.upload_master(source_file, master_info())
    channel.backup_master()
    channel.backup_master()
    assert len(list(channel.backups_path.iterdir())) == 2
    assert len(list(channel.long_backups_path.iterdir())) == 1


def test_backup_from_a_new_day_goes_to_long_folder(channel, source_file):
    channel.upload_master(source_file, master_info())
    channel.long_backups_path.mkdir(parents=True)
    yesterday = datetime.now() - timedelta(days=1)
    (channel.long_backups_path / f"master_{yesterday.strftime(BACKUP_TIME_FORMAT)}.db").write_bytes(b"x")
    channel.backup_master()
    assert len(list(channel.long_backups_path.iterdir())) == 2


def test_channel_removes_only_old_backups(channel):
    channel.backups_path.mkdir(parents=True)
    now = datetime.now()
    old = f"master_{(now - timedelta(days=4)).strftime(BACKUP_TIME_FORMAT)}.db"
    fresh = f"master_{(now - timedelta(days=1)).strftime(BACKUP_TIME_FORMAT)}.db"
    for name in (old, fresh, "master_notadate.db", "other.txt"):
        (channel.backups_path / name).write_bytes(b"x")
    channel.remove_old_backups(30)
    assert sorted(item.name for item in channel.backups_path.iterdir()) == sorted([fresh, "master_notadate.db", "other.txt"])


def test_long_backups_are_removed_by_given_period(channel):
    channel.long_backups_path.mkdir(parents=True)
    now = datetime.now()
    old = f"master_{(now - timedelta(days=40)).strftime(BACKUP_TIME_FORMAT)}.db"
    fresh = f"master_{(now - timedelta(days=20)).strftime(BACKUP_TIME_FORMAT)}.db"
    for name in (old, fresh):
        (channel.long_backups_path / name).write_bytes(b"x")
    channel.remove_old_backups(30)
    assert [item.name for item in channel.long_backups_path.iterdir()] == [fresh]


def test_channel_remove_old_backups_without_folder(channel):
    channel.remove_old_backups(30)


def test_backups_made_in_the_same_second_do_not_overwrite_each_other(channel, source_file):
    channel.upload_master(source_file, master_info())
    channel.backup_master()
    channel.backup_master()
    assert len(list(channel.backups_path.iterdir())) == 2


@pytest.mark.parametrize("name, expected", [
    ("master_20261009-165303.db", datetime(2026, 10, 9, 16, 53, 3)),
    ("master_20261009-165303-123456.db", datetime(2026, 10, 9, 16, 53, 3, 123456)),
    ("master_20261009.db", None),
    ("backup_20261009-165303.db", None),
])
def test_backup_time_is_read_from_both_name_formats(name, expected):
    assert backup_time_from_name(name) == expected


def test_old_backups_with_precise_names_are_removed(channel):
    channel.backups_path.mkdir(parents=True)
    now = datetime.now()
    old = f"master_{(now - timedelta(days=4)).strftime(PRECISE_BACKUP_TIME_FORMAT)}.db"
    fresh = f"master_{(now - timedelta(days=1)).strftime(PRECISE_BACKUP_TIME_FORMAT)}.db"
    for name in (old, fresh):
        (channel.backups_path / name).write_bytes(b"x")
    channel.remove_old_backups(30)
    assert [item.name for item in channel.backups_path.iterdir()] == [fresh]


def test_backups_cleanup_due_once_a_day():
    today = datetime.now().isoformat(timespec="seconds")
    yesterday = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
    assert backups_cleanup_due(None)
    assert backups_cleanup_due(master_info("t", uploaded_at=yesterday))
    assert backups_cleanup_due(master_info("t", uploaded_at="broken"))
    assert not backups_cleanup_due(master_info("t", uploaded_at=today))
