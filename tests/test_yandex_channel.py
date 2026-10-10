from datetime import datetime, timedelta

import pytest

from base.sync import AuthError, BACKUP_TIME_FORMAT, NetworkError, SyncAction, SyncError, pull_master, push_master, synchronize
from base.yandexchannel import YandexDiskApiChannel
from tests.test_sync_flow import PARAMS, edit, make_machine, patch_backup_dir  # noqa: F401
from tests.yandexfake import FakeDisk, json_response


@pytest.fixture
def disk() -> FakeDisk:
    return FakeDisk()


@pytest.fixture
def channel(disk) -> YandexDiskApiChannel:
    return YandexDiskApiChannel("good-token", disk)


@pytest.fixture
def machine_a(make_machine):
    return make_machine("a")


def test_no_master_means_none(channel):
    assert channel.read_master_info() is None


def test_first_push_and_connect_second_machine(machine_a, make_machine, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    assert set(disk.files) == {"app:/master.db", "app:/master.json"}
    assert channel.read_master_info().sync_token == machine_a.meta()["sync_token"]
    with make_machine("b") as dbh:
        pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
        assert dbh.get_setting("marker") == "a"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING


def test_changes_travel_between_machines(machine_a, make_machine, channel):
    machine_b = make_machine("b")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
        edit(dbh, "from b")
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
        assert dbh.get_setting("marker") == "from b"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING


def test_second_push_saves_previous_master(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        first_master = disk.files["app:/master.db"]
        edit(dbh, "second")
        push_master(dbh, channel, PARAMS)
    backups = [path for path in disk.files if path.startswith("app:/master_backups/master_")]
    assert len(backups) == 1
    assert disk.files[backups[0]] == first_master
    assert not any(path.endswith(".tmp") for path in disk.files)


def test_old_backups_are_removed_by_name(channel, disk):
    disk.folders.add("app:/master_backups")
    disk.files["app:/master_backups/master_20200101-000000.db"] = b"old"
    disk.files["app:/master_backups/master_29990101-000000.db"] = b"new"
    disk.files["app:/master_backups/other.txt"] = b"foreign"
    channel.remove_old_backups(30)
    assert sorted(disk.files) == ["app:/master_backups/master_29990101-000000.db", "app:/master_backups/other.txt"]


def test_long_backups_are_removed_by_given_period(channel, disk):
    old = f"app:/master_backups_long/master_{(datetime.now() - timedelta(days=40)).strftime(BACKUP_TIME_FORMAT)}.db"
    fresh = f"app:/master_backups_long/master_{(datetime.now() - timedelta(days=20)).strftime(BACKUP_TIME_FORMAT)}.db"
    disk.folders.add("app:/master_backups_long")
    disk.files[old] = b"old"
    disk.files[fresh] = b"fresh"
    channel.remove_old_backups(30)
    assert sorted(disk.files) == [fresh]


def test_only_first_backup_of_the_day_goes_to_long_folder(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    channel.backup_master()
    channel.backup_master()
    assert len([path for path in disk.files if path.startswith("app:/master_backups/master_")]) == 2
    assert len([path for path in disk.files if path.startswith("app:/master_backups_long/master_")]) == 1


def test_remove_old_backups_without_folder_is_noop(channel):
    channel.remove_old_backups(30)


def test_asynchronous_operations_are_awaited(machine_a, channel, disk):
    disk.async_operations = True
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        edit(dbh, "second")
        push_master(dbh, channel, PARAMS)
    assert disk.operation_polls >= 3
    assert not any(path.endswith(".tmp") for path in disk.files)


def test_upload_is_confirmed_after_delay(machine_a, channel, disk):
    disk.pending_uploads = 2
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    assert channel.read_master_info().sync_token == machine_a.meta()["sync_token"]


def test_corrupted_upload_does_not_replace_master(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        old_files = dict(disk.files)
        edit(dbh, "second")
        disk.corrupt_uploads = True
        with pytest.raises(SyncError):
            push_master(dbh, channel, PARAMS)
        assert dbh.get_setting("change_counter") != "0"
    assert disk.files["app:/master.db"] == old_files["app:/master.db"]
    assert disk.files["app:/master.json"] == old_files["app:/master.json"]
    assert not any(path.endswith(".tmp") for path in disk.files)


def test_wrong_token_is_reported_without_leaking_it(disk):
    channel = YandexDiskApiChannel("secret-bad-token", disk)
    with pytest.raises(AuthError) as error:
        channel.read_master_info()
    assert "secret-bad-token" not in str(error.value)


def test_spurious_401_on_post_is_retried(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    original_send = disk.send
    rejected: list[str] = []

    def send_with_one_401(method, url, *args, **kwargs):
        if method == "POST" and not rejected:
            rejected.append(url)
            return json_response(401, {"message": "Unauthorized"})
        return original_send(method, url, *args, **kwargs)

    disk.send = send_with_one_401
    channel.backup_master()
    assert len(rejected) == 1
    assert any(path.startswith("app:/master_backups/") for path in disk.files)


def test_network_failure_is_propagated(channel, disk):
    disk.network_down = True
    with pytest.raises(NetworkError):
        channel.read_master_info()


def test_check_connection(channel, disk):
    channel.check_connection()
    with pytest.raises(AuthError):
        YandexDiskApiChannel("wrong", disk).check_connection()
    with pytest.raises(SyncError):
        YandexDiskApiChannel("good-token", disk, "app:/missing").check_connection()


def test_custom_folder_is_created_and_used(machine_a, disk):
    channel = YandexDiskApiChannel("good-token", disk, "app:/sub/inner")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    assert {"app:/sub", "app:/sub/inner"} <= disk.folders
    assert {"app:/sub/inner/master.db", "app:/sub/inner/master.json"} <= set(disk.files)


def test_backups_made_in_the_same_second_do_not_overwrite_each_other(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    channel.backup_master()
    channel.backup_master()
    assert len([path for path in disk.files if path.startswith("app:/master_backups/master_")]) == 2


def test_info_is_uploaded_without_temp_file_and_move(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    moves = [request for request in disk.requests if request == ("POST", "cloud-api.yandex.net/v1/disk/resources/move")]
    assert len(moves) == 1


def test_info_overwrite_waits_until_new_content_is_visible(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        edit(dbh, "second")
        disk.pending_uploads = 2
        disk.metadata_polls = 0
        push_master(dbh, channel, PARAMS)
    assert channel.read_master_info().sync_token == machine_a.meta()["sync_token"]


def test_backup_folder_is_created_only_when_missing(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        edit(dbh, "second")
        push_master(dbh, channel, PARAMS)
        folder_creations = len([request for request in disk.requests if request[0] == "PUT" and request[1].endswith("/resources")])
        edit(dbh, "third")
        push_master(dbh, channel, PARAMS)
    assert "app:/master_backups" in disk.folders
    assert len([request for request in disk.requests if request[0] == "PUT" and request[1].endswith("/resources")]) == folder_creations


def test_synchronize_reads_master_info_once(machine_a, make_machine, channel, disk):
    def info_reads() -> int:
        return len([request for request in disk.requests if request[1].endswith("/resources/download")])

    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with make_machine("b") as dbh:
        reader_b = YandexDiskApiChannel("good-token", disk)
        pull_master(dbh, reader_b, (SyncAction.FOREIGN_DB,))
        edit(dbh, "from b")
        before = info_reads()
        assert synchronize(dbh, reader_b, PARAMS) == SyncAction.PUSH
        assert info_reads() - before == 0
    with machine_a as dbh:
        before = info_reads()
        assert synchronize(dbh, YandexDiskApiChannel("good-token", disk), PARAMS) == SyncAction.PULL
        assert info_reads() - before == 2


def info_downloads(disk: FakeDisk) -> int:
    return len([request for request in disk.requests if request[1].endswith("/resources/download")])


def test_unchanged_master_info_is_not_downloaded_again(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    fresh_channel = YandexDiskApiChannel("good-token", disk)
    first = fresh_channel.read_master_info()
    downloads = info_downloads(disk)
    second = fresh_channel.read_master_info()
    assert info_downloads(disk) == downloads
    assert second == first
    assert second is not first


def test_changed_master_info_is_downloaded_again(machine_a, make_machine, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    reader = YandexDiskApiChannel("good-token", disk)
    old_token = reader.read_master_info().sync_token
    with machine_a as dbh:
        edit(dbh, "second")
        push_master(dbh, channel, PARAMS)
    new_token = reader.read_master_info().sync_token
    assert new_token != old_token
    assert new_token == machine_a.meta()["sync_token"]


def test_own_push_updates_cached_master_info(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        downloads = info_downloads(disk)
        token = channel.read_master_info().sync_token
    assert token == machine_a.meta()["sync_token"]
    assert info_downloads(disk) == downloads


def test_removed_master_info_is_noticed_with_cache(machine_a, channel, disk):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    channel.read_master_info()
    del disk.files["app:/master.json"]
    assert channel.read_master_info() is None
