import shutil
from pathlib import Path

import pytest

import base.sync as syncmod
from base.sync import (FolderChannel, MasterChangedError, MasterInfo, MasterUpdatingError, SyncAction, SyncError, SyncParams,
                       pull_master, push_master, synchronize)
from gui.syncmanager import connect_to_master, create_master, overwrite_master, take_master
from tests.dbtools import create_db, read_meta

PARAMS = SyncParams("Автор", "PC-1", "2026.10.04")


class Machine:
    def __init__(self, dbh, work_db_path: Path, file: Path):
        self.dbh = dbh
        self.work_db_path = work_db_path
        self.file = file

    def __enter__(self):
        self.dbh.db.close()
        shutil.copy(self.file, self.work_db_path)
        self.dbh.open_db_connection()
        return self.dbh

    def __exit__(self, *exc):
        self.dbh.db.close()
        shutil.copy(self.work_db_path, self.file)

    def meta(self) -> dict[str, str]:
        return read_meta(self.file)


@pytest.fixture(autouse=True)
def patch_backup_dir(backup_folder, monkeypatch):
    monkeypatch.setattr(syncmod, "backup_dir", lambda: str(backup_folder))


@pytest.fixture
def make_machine(dbh, work_db_path, tmp_path):
    def make(name: str) -> Machine:
        dbh.db.close()
        work_db_path.unlink(missing_ok=True)
        create_db(work_db_path, 4, {"marker": name})
        assert dbh.migrate_db()
        file = tmp_path / f"{name}.db"
        shutil.copy(work_db_path, file)
        return Machine(dbh, work_db_path, file)
    return make


@pytest.fixture
def channel(tmp_path) -> FolderChannel:
    return FolderChannel(tmp_path / "exchange")


@pytest.fixture
def machine_a(make_machine) -> Machine:
    return make_machine("a")


@pytest.fixture
def connected(machine_a, make_machine, channel):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    machine_b = make_machine("b")
    with machine_b as dbh:
        pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
    return machine_a, machine_b


def edit(dbh, value: str) -> None:
    assert dbh.set_setting("marker", value)


def test_push_creates_master(machine_a, channel):
    with machine_a as dbh:
        assert machine_a.meta()["change_counter"] == "1"
        push_master(dbh, channel, PARAMS)
    info = channel.read_master_info()
    meta = machine_a.meta()
    assert info.sync_token == meta["sync_token"]
    assert info.db_uuid == meta["db_uuid"]
    assert (info.author, info.machine, info.app_version) == ("Автор", "PC-1", "2026.10.04")
    assert meta["change_counter"] == "0"
    master_file = machine_a.file.with_name("master_copy.db")
    channel.download_master(master_file)
    master_meta = read_meta(master_file)
    assert master_meta["sync_token"] == info.sync_token
    assert master_meta["change_counter"] == "0"
    assert master_meta["marker"] == "a"


def test_push_keeps_working_db_usable(machine_a, channel):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        assert dbh.is_db_connected()
        edit(dbh, "after push")
        assert dbh.get_setting("marker") == "after push"


def test_push_saves_previous_master_backup(machine_a, channel):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        assert not channel.backups_path.exists()
        edit(dbh, "second")
        push_master(dbh, channel, PARAMS)
    assert len(list(channel.backups_path.iterdir())) == 1


def test_connect_to_master_replaces_foreign_db(connected, backup_folder, channel):
    machine_a, machine_b = connected
    meta_a, meta_b = machine_a.meta(), machine_b.meta()
    assert meta_b["db_uuid"] == meta_a["db_uuid"]
    assert meta_b["sync_token"] == meta_a["sync_token"]
    assert meta_b["marker"] == "a"
    assert meta_b["change_counter"] == "0"
    copies = list(backup_folder.glob("before_sync_*.db"))
    assert len(copies) == 1
    assert read_meta(copies[0])["marker"] == "b"


def test_pull_refused_for_foreign_db_by_default(machine_a, make_machine, channel):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    machine_b = make_machine("b")
    with machine_b as dbh:
        with pytest.raises(SyncError):
            pull_master(dbh, channel)
        assert dbh.get_setting("marker") == "b"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.FOREIGN_DB


def test_first_connection_helpers_of_gui(machine_a, make_machine, channel):
    with machine_a as dbh:
        assert create_master(dbh, channel, PARAMS) == SyncAction.PUSH
    machine_b = make_machine("b")
    with machine_b as dbh:
        assert connect_to_master(dbh, channel) == SyncAction.PULL
        assert dbh.get_setting("marker") == "a"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING


def test_changes_travel_between_machines(connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
        assert dbh.get_setting("marker") == "from b"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    assert machine_a.meta()["change_counter"] == "0"
    assert machine_a.meta()["sync_token"] == channel.read_master_info().sync_token


def test_conflict_changes_nothing(connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    master_bytes = channel.master_db_path.read_bytes()
    with machine_a as dbh:
        edit(dbh, "from a")
        assert synchronize(dbh, channel, PARAMS) == SyncAction.CONFLICT
        assert dbh.get_setting("marker") == "from a"
        with pytest.raises(SyncError):
            push_master(dbh, channel, PARAMS)
        with pytest.raises(SyncError):
            pull_master(dbh, channel)
        assert dbh.get_setting("marker") == "from a"
    assert channel.master_db_path.read_bytes() == master_bytes


def test_conflict_resolved_by_overwriting_master(connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    with machine_a as dbh:
        edit(dbh, "from a")
        push_master(dbh, channel, PARAMS, overwrite=True)
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
        assert dbh.get_setting("marker") == "from a"


def test_conflict_resolved_by_taking_master(connected, channel, backup_folder):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    with machine_a as dbh:
        edit(dbh, "from a")
        pull_master(dbh, channel, (SyncAction.CONFLICT,))
        assert dbh.get_setting("marker") == "from b"
    assert machine_a.meta()["change_counter"] == "0"
    assert any(read_meta(copy)["marker"] == "from a" for copy in backup_folder.glob("before_sync_*.db"))


def test_gui_conflict_choice_take_master_keeps_conflict_copy(connected, channel, backup_folder):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    with machine_a as dbh:
        edit(dbh, "from a")
        assert take_master(dbh, channel) == SyncAction.PULL
        assert dbh.get_setting("marker") == "from b"
    assert any(read_meta(copy)["marker"] == "from a" for copy in backup_folder.glob("conflict_*.db"))


def test_gui_conflict_choice_overwrite_keeps_conflict_copy(connected, channel, backup_folder):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    with machine_a as dbh:
        edit(dbh, "from a")
        assert overwrite_master(dbh, channel, PARAMS) == SyncAction.PUSH
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    assert read_meta(channel.master_db_path)["marker"] == "from a"
    assert any(read_meta(copy)["marker"] == "from a" for copy in backup_folder.glob("conflict_*.db"))
    assert len(list(channel.backups_path.iterdir())) == 2
    assert any(read_meta(copy)["marker"] == "from b" for copy in channel.backups_path.iterdir())


def test_nothing_to_push_or_pull_is_refused(connected, channel):
    machine_a, _ = connected
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
        with pytest.raises(SyncError):
            push_master(dbh, channel, PARAMS)
        with pytest.raises(SyncError):
            pull_master(dbh, channel)


def test_synchronize_without_master(machine_a, channel):
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NO_MASTER
    assert channel.read_master_info() is None


class MasterChangesDuringPush(FolderChannel):
    def __init__(self, folder):
        super().__init__(folder)
        self.reads = 0

    def read_master_info(self):
        info = super().read_master_info()
        self.reads += 1
        if self.reads >= 2:
            info.sync_token = "changed by someone else"
        return info


def test_push_cancelled_when_master_changed_during_snapshot(connected, channel):
    machine_a, _ = connected
    racing = MasterChangesDuringPush(channel.folder)
    master_bytes = channel.master_db_path.read_bytes()
    info_text = channel.master_info_path.read_text(encoding="utf-8")
    with machine_a as dbh:
        edit(dbh, "from a")
        with pytest.raises(MasterChangedError):
            push_master(dbh, racing, PARAMS)
        assert dbh.get_setting("change_counter") != "0"
    assert channel.master_db_path.read_bytes() == master_bytes
    assert channel.master_info_path.read_text(encoding="utf-8") == info_text
    assert not channel.backups_path.exists()


class EditsDuringUpload(FolderChannel):
    def __init__(self, folder, dbh):
        super().__init__(folder)
        self.dbh = dbh

    def upload_master(self, source, info):
        super().upload_master(source, info)
        edit(self.dbh, "typed during upload")


def test_edit_during_upload_stays_unsent(connected, channel):
    machine_a, _ = connected
    with machine_a as dbh:
        edit(dbh, "before upload")
        push_master(dbh, EditsDuringUpload(channel.folder, dbh), PARAMS)
        assert dbh.get_setting("sync_token") == channel.read_master_info().sync_token
        assert int(dbh.get_setting("change_counter")) > 0
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
        assert dbh.get_setting("change_counter") == "0"
    assert read_meta(channel.master_db_path)["marker"] == "typed during upload"


def test_pull_refused_when_master_db_and_info_disagree(connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    info = channel.read_master_info()
    channel.master_info_path.write_text(MasterInfo(info.db_uuid, "newer token", info.db_version, "x", "y", "z", "w").to_json(),
                                        encoding="utf-8")
    with machine_a as dbh:
        with pytest.raises(MasterUpdatingError):
            pull_master(dbh, channel)
        assert dbh.get_setting("marker") == "a"


def test_pull_refused_when_master_is_corrupted(connected, channel):
    machine_a, machine_b = connected
    with machine_b as dbh:
        edit(dbh, "from b")
        synchronize(dbh, channel, PARAMS)
    channel.master_db_path.write_bytes(b"this is not a sqlite database" * 100)
    with machine_a as dbh:
        with pytest.raises(SyncError):
            pull_master(dbh, channel)
        assert dbh.get_setting("marker") == "a"
        assert dbh.is_db_connected()


def test_pull_of_older_master_migrates_and_marks_changed(machine_a, channel, make_machine, dbh, migrations):
    with machine_a as dbh_a:
        push_master(dbh_a, channel, PARAMS)
    dbh.DB_VERSION = 6
    migrations[6] = ["INSERT INTO meta (key, value) VALUES ('key6', 'z')"]
    machine_b = make_machine("b")
    with machine_b as dbh_b:
        pull_master(dbh_b, channel, (SyncAction.FOREIGN_DB,))
        assert dbh_b.get_setting("marker") == "a"
        assert dbh_b.get_setting("key6") == "z"
        assert dbh_b.get_setting("db_version") == "6"
        assert dbh_b.get_setting("change_counter") != "0"
        assert synchronize(dbh_b, channel, PARAMS) == SyncAction.PUSH
    assert channel.read_master_info().db_version == 6
    assert not (machine_b.work_db_path.parent / "db_restore_temp.db").exists()


def test_outdated_client_neither_pushes_nor_pulls(connected, channel, dbh, migrations):
    machine_a, machine_b = connected
    dbh.DB_VERSION = 6
    migrations[6] = ["INSERT INTO meta (key, value) VALUES ('key6', 'z')"]
    with machine_b as dbh_b:
        assert dbh_b.migrate_db()
        dbh_b.open_db_connection()
        assert synchronize(dbh_b, channel, PARAMS) == SyncAction.PUSH
    dbh.DB_VERSION = 5
    with machine_a as dbh_a:
        assert synchronize(dbh_a, channel, PARAMS) == SyncAction.CLIENT_OUTDATED
        with pytest.raises(SyncError):
            pull_master(dbh_a, channel)
        assert dbh_a.get_setting("marker") == "a"
