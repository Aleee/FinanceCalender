import shutil
from pathlib import Path

import pytest

import base.sync as syncmod
from base.sync import (FolderChannel, MasterChangedError, MasterInfo, MasterUpdatingError, SyncAction, SyncError, SyncParams,
                       pull_master, push_master, restore_master_info, synchronize)
from gui.syncmanager import connect_to_master, create_master, discard_unsent_changes, overwrite_master, take_master
from tests.dbtools import create_db, read_meta

PARAMS = SyncParams("Автор", "PC-1", "2026.10.04")


class Machine:
    def __init__(self, dbh, work_db_path: Path, file: Path):
        self.dbh = dbh
        self.work_db_path = work_db_path
        self.file = file
        self.base_file = file.with_name(file.stem + "_base.db")

    def __enter__(self):
        self.dbh.db.close()
        shutil.copy(self.file, self.work_db_path)
        self.dbh.open_db_connection()
        self.saved_base_path = syncmod.sync_base_path
        syncmod.sync_base_path = lambda: str(self.base_file)
        return self.dbh

    def __exit__(self, *exc):
        syncmod.sync_base_path = self.saved_base_path
        self.dbh.db.close()
        shutil.copy(self.work_db_path, self.file)

    def meta(self) -> dict[str, str]:
        return read_meta(self.file)


@pytest.fixture(autouse=True)
def patch_backup_dir(backup_folder, monkeypatch):
    monkeypatch.setattr(syncmod, "backup_dir", lambda: str(backup_folder))


@pytest.fixture
def make_machine(dbh, work_db_path, tmp_path, migrated_files):
    def make(name: str) -> Machine:
        dbh.db.close()
        file = tmp_path / f"{name}.db"
        if name not in migrated_files:
            work_db_path.unlink(missing_ok=True)
            create_db(work_db_path, 4, {"marker": name})
            assert dbh.migrate_db()
            dbh.db.close()
            migrated_files[name] = work_db_path.read_bytes()
        work_db_path.parent.mkdir(parents=True, exist_ok=True)
        work_db_path.write_bytes(migrated_files[name])
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


def test_gui_discard_unsent_changes_without_conflict(connected, channel, backup_folder):
    machine_a, _ = connected
    with machine_a as dbh:
        edit(dbh, "from a")
        assert discard_unsent_changes(dbh, channel) == SyncAction.PULL
        assert dbh.get_setting("marker") != "from a"
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    assert machine_a.meta()["change_counter"] == "0"
    assert any(read_meta(copy)["marker"] == "from a" for copy in backup_folder.glob("discarded_*.db"))
    assert not list(backup_folder.glob("conflict_*.db"))


def test_gui_discard_refused_when_nothing_to_discard(connected, channel):
    machine_a, _ = connected
    with machine_a as dbh:
        with pytest.raises(SyncError):
            discard_unsent_changes(dbh, channel)


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
    dbh.DB_VERSION = 9
    migrations[9] = ["INSERT INTO meta (key, value) VALUES ('key8', 'z')"]
    machine_b = make_machine("b")
    with machine_b as dbh_b:
        pull_master(dbh_b, channel, (SyncAction.FOREIGN_DB,))
        assert dbh_b.get_setting("marker") == "a"
        assert dbh_b.get_setting("key8") == "z"
        assert dbh_b.get_setting("db_version") == "9"
        assert dbh_b.get_setting("change_counter") != "0"
        assert synchronize(dbh_b, channel, PARAMS) == SyncAction.PUSH
    assert channel.read_master_info().db_version == 9
    assert not (machine_b.work_db_path.parent / "db_restore_temp.db").exists()


def test_outdated_client_neither_pushes_nor_pulls(connected, channel, dbh, migrations):
    machine_a, machine_b = connected
    dbh.DB_VERSION = 9
    migrations[9] = ["INSERT INTO meta (key, value) VALUES ('key8', 'z')"]
    with machine_b as dbh_b:
        assert dbh_b.migrate_db()
        dbh_b.open_db_connection()
        assert synchronize(dbh_b, channel, PARAMS) == SyncAction.PUSH
    dbh.DB_VERSION = 8
    with machine_a as dbh_a:
        assert synchronize(dbh_a, channel, PARAMS) == SyncAction.CLIENT_OUTDATED
        with pytest.raises(SyncError):
            pull_master(dbh_a, channel)
        assert dbh_a.get_setting("marker") == "a"


def test_fetch_master_creates_local_db(machine_a, channel, dbh, work_db_path):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    dbh.db.close()
    work_db_path.unlink()
    syncmod.fetch_master(dbh, channel)
    assert dbh.open_db_connection()
    assert dbh.get_setting("marker") == "a"
    assert syncmod.decide_action(syncmod.read_local_state(dbh), channel.read_master_info()) == SyncAction.NOTHING


def test_fetch_master_without_master_creates_nothing(channel, dbh, work_db_path):
    work_db_path.parent.mkdir(parents=True, exist_ok=True)
    work_db_path.unlink(missing_ok=True)
    with pytest.raises(SyncError):
        syncmod.fetch_master(dbh, channel)
    assert not work_db_path.exists()


def test_fetch_master_refuses_newer_master(machine_a, channel, dbh, work_db_path):
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    info = channel.read_master_info()
    info.db_version = dbh.DB_VERSION + 1
    channel.master_info_path.write_text(info.to_json(), encoding="utf-8")
    dbh.db.close()
    work_db_path.unlink()
    with pytest.raises(SyncError):
        syncmod.fetch_master(dbh, channel)
    assert not work_db_path.exists()


def master_info_aged(minutes: int) -> MasterInfo:
    from datetime import datetime, timedelta
    uploaded_at = (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
    return MasterInfo("uuid", "token", 5, "Автор", "PC", uploaded_at, "2026.10.04")


def test_master_backup_due_by_interval():
    due = syncmod.master_backup_due
    assert due(None, 30)
    assert due(master_info_aged(1), 0)
    assert not due(master_info_aged(5), 30)
    assert due(master_info_aged(31), 30)
    assert due(master_info_aged(-10), 30)
    assert due(MasterInfo("u", "t", 5, "a", "m", "не дата", "v"), 30)


def test_push_skips_backup_within_interval(machine_a, channel):
    params = SyncParams("Автор", "PC-1", "2026.10.04", backup_interval_minutes=30)
    with machine_a as dbh:
        push_master(dbh, channel, params)
        edit(dbh, "second")
        push_master(dbh, channel, params)
        edit(dbh, "third")
        push_master(dbh, channel, params)
    assert not channel.backups_path.exists()
    assert channel.read_master_info().sync_token == machine_a.meta()["sync_token"]


def test_overwrite_makes_backup_within_interval(connected, channel):
    machine_a, machine_b = connected
    params = SyncParams("Автор", "PC-1", "2026.10.04", backup_interval_minutes=30)
    with machine_a as dbh:
        edit(dbh, "from a")
        push_master(dbh, channel, params)
    with machine_b as dbh:
        edit(dbh, "from b")
        push_master(dbh, channel, params, overwrite=True)
    assert len(list(channel.backups_path.iterdir())) == 1


def add_event(machine: Machine, event_id: int, name: str) -> None:
    import sqlite3
    con = sqlite3.connect(machine.file)
    con.execute("INSERT INTO event (id, receiver, name, totalamount, duedate) VALUES (?, 'Получатель', ?, '10.00', '2026-10-15')",
                (event_id, name))
    con.commit()
    con.close()


def test_base_saved_after_push_and_pull(machine_a, make_machine, channel):
    with machine_a as dbh:
        assert syncmod.find_sync_base(dbh, syncmod.read_local_state(dbh)) is None
        push_master(dbh, channel, PARAMS)
        base = syncmod.find_sync_base(dbh, syncmod.read_local_state(dbh))
        assert base is not None and read_meta(base)["sync_token"] == channel.read_master_info().sync_token
        edit(dbh, "newer")
        assert syncmod.find_sync_base(dbh, syncmod.read_local_state(dbh)) is not None
    machine_b = make_machine("b")
    with machine_b as dbh:
        assert syncmod.find_sync_base(dbh, syncmod.read_local_state(dbh)) is None
        pull_master(dbh, channel, (SyncAction.FOREIGN_DB,))
        assert syncmod.find_sync_base(dbh, syncmod.read_local_state(dbh)) is not None


@pytest.mark.parametrize("key", ["sync_token", "db_uuid"])
def test_base_ignored_when_state_differs(machine_a, channel, key):
    import sqlite3
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
        local = syncmod.read_local_state(dbh)
        assert syncmod.find_sync_base(dbh, local) is not None
        con = sqlite3.connect(machine_a.base_file)
        con.execute("UPDATE meta SET value = 'other' WHERE key = ?", (key,))
        con.commit()
        con.close()
        assert syncmod.find_sync_base(dbh, local) is None


def test_pull_report_lists_other_users_changes(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "Аренда")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report) == SyncAction.PULL
    assert [row["name"] for row in report.their_changes.tables["event"].added] == ["Аренда"]
    assert report.my_changes is None


def test_conflict_report_separates_my_and_their_changes(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_event(machine_b, 1, "От второго")
    add_event(machine_b, 2, "Ещё от второго")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.CONFLICT
        syncmod.collect_conflict_report(dbh, channel, report)
    assert [row["name"] for row in report.their_changes.tables["event"].added] == ["От первого"]
    assert [row["name"] for row in report.my_changes.tables["event"].added] == ["От второго", "Ещё от второго"]


def test_conflict_report_empty_without_base(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_event(machine_b, 1, "От второго")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    machine_b.base_file.unlink()
    report = syncmod.SyncReport()
    with machine_b as dbh:
        syncmod.collect_conflict_report(dbh, channel, report)
    assert report.their_changes is None and report.my_changes is None


def add_payment(machine: Machine, payment_id: int, event_id: int, amount: str) -> None:
    import sqlite3
    con = sqlite3.connect(machine.file)
    con.execute("INSERT INTO payment (id, eventid, paymentdate, sum, createdate) VALUES (?, ?, '2026-10-11', ?, '2026-10-11')",
                (payment_id, event_id, amount))
    con.commit()
    con.close()


def rows(machine: Machine, sql: str) -> list[tuple]:
    from tests.dbtools import fetch_all
    return fetch_all(machine.file, sql)


@pytest.fixture
def shared_event(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "Общее")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    return machine_a, machine_b


def test_merge_adds_new_events_and_payments_with_new_ids(connected, channel, backup_folder):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_payment(machine_a, 1, 1, "3.00")
    add_event(machine_b, 1, "От второго")
    add_payment(machine_b, 1, 1, "4.00")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report, merge=True) == SyncAction.MERGE
        assert report.merge_pushed
    assert rows(machine_b, "SELECT id, name FROM event ORDER BY id") == [(1, "От первого"), (2, "От второго")]
    assert rows(machine_b, "SELECT id, eventid, sum FROM payment ORDER BY id") == [(1, 1, "3.00"), (2, 2, "4.00")]
    assert [row["name"] for row in report.their_changes.tables["event"].added] == ["От первого"]
    assert [row["name"] for row in report.my_changes.tables["event"].added] == ["От второго"]
    assert report.warnings.is_empty
    assert machine_b.meta()["change_counter"] == "0"
    assert any(read_meta(copy)["change_counter"] != "0" for copy in backup_folder.glob("conflict_*.db"))
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    assert rows(machine_a, "SELECT id, name FROM event ORDER BY id") == rows(machine_b, "SELECT id, name FROM event ORDER BY id")
    assert rows(machine_a, "SELECT id, eventid, sum FROM payment ORDER BY id") == rows(machine_b, "SELECT id, eventid, sum FROM payment ORDER BY id")


def test_merge_payments_to_existing_event_and_overpayment_warning(shared_event, channel):
    machine_a, machine_b = shared_event
    add_payment(machine_a, 1, 1, "8.00")
    add_payment(machine_b, 1, 1, "8.00")
    add_payment(machine_b, 2, 1, "1.00")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report, merge=True) == SyncAction.MERGE
    assert rows(machine_b, "SELECT id, eventid, sum FROM payment ORDER BY id") == [(1, 1, "8.00"), (2, 1, "8.00"), (3, 1, "1.00")]
    assert [row["name"] for row in report.warnings.overpaid_events] == ["Общее"]
    assert [row["sum"] for row in report.warnings.duplicate_payments] == ["8.00"]


def test_merge_warns_about_duplicate_event(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "Одинаковое")
    add_event(machine_b, 1, "Одинаковое")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report, merge=True) == SyncAction.MERGE
    assert [row["name"] for row in report.warnings.duplicate_events] == ["Одинаковое"]
    assert rows(machine_b, "SELECT COUNT(*) FROM event") == [(2,)]


def test_merge_not_done_when_other_table_changed(shared_event, channel):
    import sqlite3
    machine_a, machine_b = shared_event
    add_event(machine_a, 2, "От первого")
    con = sqlite3.connect(machine_b.file)
    con.execute("INSERT INTO department (id, name) VALUES (1, 'Новый')")
    con.commit()
    con.close()
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, merge=True) == SyncAction.CONFLICT


def test_merge_not_done_when_event_deleted_in_master(shared_event, channel):
    import sqlite3
    machine_a, machine_b = shared_event
    con = sqlite3.connect(machine_a.file)
    con.execute("DELETE FROM event WHERE id = 1")
    con.commit()
    con.close()
    add_payment(machine_b, 1, 1, "5.00")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, merge=True) == SyncAction.CONFLICT
    assert rows(machine_b, "SELECT COUNT(*) FROM payment") == [(1,)]


def test_merge_not_done_without_base(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_event(machine_b, 1, "От второго")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    machine_b.base_file.unlink()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, merge=True) == SyncAction.CONFLICT


def test_merge_without_flag_stays_conflict(connected, channel):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_event(machine_b, 1, "От второго")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.CONFLICT


def test_merge_keeps_changes_for_next_push_when_push_fails(connected, channel, monkeypatch):
    machine_a, machine_b = connected
    add_event(machine_a, 1, "От первого")
    add_event(machine_b, 1, "От второго")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    real_push = syncmod.push_master
    monkeypatch.setattr(syncmod, "push_master", lambda *args, **kwargs: (_ for _ in ()).throw(SyncError("нет связи")))
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report, merge=True) == SyncAction.MERGE
        assert not report.merge_pushed
    monkeypatch.setattr(syncmod, "push_master", real_push)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PUSH
    assert rows(machine_b, "SELECT COUNT(*) FROM event") == [(2,)]
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    assert rows(machine_a, "SELECT COUNT(*) FROM event") == [(2,)]


def run_sql(machine: Machine, sql: str, *params) -> None:
    import sqlite3
    con = sqlite3.connect(machine.file)
    if params:
        con.execute(sql, params)
    else:
        con.executescript(sql)
    con.commit()
    con.close()


NEW_EVENT_2 = ("INSERT INTO event (id, receiver, name, totalamount, duedate) "
               "VALUES (2, 'Р', 'Другое', '1', '2026-10-15')")


def sync_both(machine_a, machine_b, channel, sql_a: str, sql_b: str, report=None):
    run_sql(machine_a, sql_a)
    run_sql(machine_b, sql_b)
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        return synchronize(dbh, channel, PARAMS, report, merge=True)


def test_merge_keeps_my_edit_of_existing_event_and_their_new_event(shared_event, channel):
    machine_a, machine_b = shared_event
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2, "UPDATE event SET totalamount = '99.00' WHERE id = 1", report)
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT id, totalamount FROM event ORDER BY id") == [(1, "99.00"), (2, "1")]
    assert [new["totalamount"] for _, new in report.my_changes.tables["event"].changed] == ["99.00"]
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    assert rows(machine_a, "SELECT id, totalamount FROM event ORDER BY id") == [(1, "99.00"), (2, "1")]


def test_merge_combines_different_columns_of_same_event(shared_event, channel):
    machine_a, machine_b = shared_event
    action = sync_both(machine_a, machine_b, channel,
                       "UPDATE event SET notes = 'заметка', receiver = 'Новый' WHERE id = 1",
                       "UPDATE event SET totalamount = '77.00' WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT receiver, notes, totalamount FROM event WHERE id = 1") == [
        ("Новый", "заметка", "77.00")]


def test_merge_takes_my_receiver(shared_event, channel):
    machine_a, machine_b = shared_event
    action = sync_both(machine_a, machine_b, channel, "UPDATE event SET notes = 'чужая' WHERE id = 1",
                       "UPDATE event SET receiver = 'ООО Мой' WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT receiver, notes FROM event WHERE id = 1") == [("ООО Мой", "чужая")]


def test_merge_accepts_identical_change_of_same_column(shared_event, channel):
    machine_a, machine_b = shared_event
    action = sync_both(machine_a, machine_b, channel, "UPDATE event SET totalamount = '50.00' WHERE id = 1",
                       "UPDATE event SET totalamount = '50.00', notes = 'моя' WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT totalamount, notes FROM event WHERE id = 1") == [("50.00", "моя")]


def test_conflict_when_same_column_changed_differently(shared_event, channel):
    machine_a, machine_b = shared_event
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "UPDATE event SET totalamount = '50.00' WHERE id = 1",
                       "UPDATE event SET totalamount = '60.00' WHERE id = 1", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Сумма", "60,00", "50,00")]
    assert rows(machine_b, "SELECT totalamount FROM event WHERE id = 1") == [("60.00",)]


def test_conflict_report_contains_conflicts_for_dialog(shared_event, channel):
    machine_a, machine_b = shared_event
    run_sql(machine_a, "UPDATE event SET totalamount = '50.00' WHERE id = 1")
    run_sql(machine_b, "UPDATE event SET totalamount = '60.00' WHERE id = 1")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        syncmod.collect_conflict_report(dbh, channel, report)
    assert len(report.conflicts) == 1


def test_merge_applies_payment_edit_and_warns_about_overpayment(shared_event, channel):
    machine_a, machine_b = shared_event
    run_sql(machine_a, "INSERT INTO payment (id, eventid, paymentdate, sum) VALUES (1, 1, '2026-10-11', '5.00')")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2, "UPDATE payment SET sum = '15.00' WHERE id = 1", report)
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT sum FROM payment WHERE id = 1") == [("15.00",)]
    assert [row["name"] for row in report.warnings.overpaid_events] == ["Общее"]


def test_merge_deletes_event_with_payments_removed_by_me(shared_event, channel):
    machine_a, machine_b = shared_event
    run_sql(machine_a, "INSERT INTO payment (id, eventid, paymentdate, sum) VALUES (1, 1, '2026-10-11', '5.00')")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    run_sql(machine_b, "DELETE FROM payment WHERE eventid = 1")
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2, "DELETE FROM event WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT id FROM event ORDER BY id") == [(2,)]
    assert rows(machine_b, "SELECT COUNT(*) FROM payment") == [(0,)]


def test_conflict_when_deleted_event_got_payment_in_master(shared_event, channel):
    machine_a, machine_b = shared_event
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel,
                       "INSERT INTO payment (id, eventid, paymentdate, sum) VALUES (1, 1, '2026-10-11', '5.00')",
                       "DELETE FROM event WHERE id = 1", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine) for c in report.conflicts] == [("Оплата", "платеж удалён")]


def test_conflict_when_deleted_by_me_and_changed_by_other(shared_event, channel):
    machine_a, machine_b = shared_event
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "UPDATE event SET notes = 'правка' WHERE id = 1",
                       "DELETE FROM event WHERE id = 1", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Платеж", "удаление", "правка")]


def test_conflict_when_changed_by_me_and_deleted_by_other(shared_event, channel):
    machine_a, machine_b = shared_event
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "DELETE FROM event WHERE id = 1",
                       "UPDATE event SET notes = 'правка' WHERE id = 1", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Платеж", "правка", "удаление")]


def test_merge_ignores_event_deleted_on_both_sides(shared_event, channel):
    machine_a, machine_b = shared_event
    action = sync_both(machine_a, machine_b, channel, "DELETE FROM event WHERE id = 1", "DELETE FROM event WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT COUNT(*) FROM event") == [(0,)]


def chain_sql(number: int, contractor: str, term: bool = True) -> str:
    sql = (f"INSERT INTO contractor (id, name) VALUES ({number}, '{contractor}');"
           f"INSERT INTO contract (id, contractor_id, name, date) VALUES ({number}, {number}, '1', '2026-02-01');"
           f"INSERT INTO contractdocument (id, contract_id, document_name) VALUES ({number}, {number}, 'Приложение');")
    return sql + (f"INSERT INTO contractpaymentterm (document_id, payment_type) VALUES ({number}, 'RELATIVE');" if term else "")


CONTRACT_ROWS = {
    "contractor": "SELECT id, name FROM contractor ORDER BY id",
    "contract": "SELECT id, contractor_id FROM contract ORDER BY id",
    "contractdocument": "SELECT id, contract_id FROM contractdocument ORDER BY id",
    "contractpaymentterm": "SELECT document_id, days_count FROM contractpaymentterm ORDER BY document_id",
    "contractsavedvalues": "SELECT contractdocumentid, receiver FROM contractsavedvalues ORDER BY contractdocumentid",
    "event": "SELECT id, contractdocument_id FROM event ORDER BY id",
}


@pytest.fixture
def shared_contract(connected, channel):
    machine_a, machine_b = connected
    run_sql(machine_a, chain_sql(1, "Ромашка") + "INSERT INTO contractdocument (id, contract_id, document_name) VALUES (2, 1, 'Без сроков');")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    return machine_a, machine_b


def test_merge_adds_contractor_contract_document_chain_with_new_ids(connected, channel):
    machine_a, machine_b = connected
    run_sql(machine_a, chain_sql(1, "Альфа"))
    run_sql(machine_b, chain_sql(1, "Бета") + "INSERT INTO contractsavedvalues (contractdocumentid, receiver) VALUES (1, 'Бета');"
                       "INSERT INTO event (id, receiver, name, totalamount, duedate, contractdocument_id) "
                       "VALUES (1, 'Р', 'Н', '1', '2026-10-15', 1)")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    report = syncmod.SyncReport()
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS, report, merge=True) == SyncAction.MERGE
    assert rows(machine_b, CONTRACT_ROWS["contractor"]) == [(1, "Альфа"), (2, "Бета")]
    assert rows(machine_b, CONTRACT_ROWS["contract"]) == [(1, 1), (2, 2)]
    assert rows(machine_b, CONTRACT_ROWS["contractdocument"]) == [(1, 1), (2, 2)]
    assert rows(machine_b, CONTRACT_ROWS["contractpaymentterm"]) == [(1, 0), (2, 0)]
    assert rows(machine_b, CONTRACT_ROWS["contractsavedvalues"]) == [(2, "Бета")]
    assert rows(machine_b, CONTRACT_ROWS["event"]) == [(1, 2)]
    assert report.warnings.is_empty
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    for sql in CONTRACT_ROWS.values():
        assert rows(machine_a, sql) == rows(machine_b, sql)


def test_merge_links_existing_event_to_new_document(shared_event, channel):
    machine_a, machine_b = shared_event
    action = sync_both(machine_a, machine_b, channel, chain_sql(1, "Альфа"),
                       chain_sql(1, "Бета") + "UPDATE event SET contractdocument_id = 1 WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, CONTRACT_ROWS["contractdocument"]) == [(1, 1), (2, 2)]
    assert rows(machine_b, CONTRACT_ROWS["event"]) == [(1, 2)]


def test_merge_contractor_rename_and_their_new_contract(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "INSERT INTO contract (id, contractor_id, name, date) VALUES (2, 1, '13', '2026-03-01')",
                       "UPDATE contractor SET name = 'Ромашка плюс' WHERE id = 1", report)
    assert action == SyncAction.MERGE
    assert rows(machine_b, CONTRACT_ROWS["contractor"]) == [(1, "Ромашка плюс")]
    assert rows(machine_b, CONTRACT_ROWS["contract"]) == [(1, 1), (2, 1)]
    assert [new["name"] for _, new in report.my_changes.tables["contractor"].changed] == ["Ромашка плюс"]
    assert [row["name"] for row in report.their_changes.tables["contract"].added] == ["13"]


def test_conflict_when_contractor_renamed_differently(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "UPDATE contractor SET name = 'А' WHERE id = 1",
                       "UPDATE contractor SET name = 'Б' WHERE id = 1", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Наименование", "Б", "А")]


def test_merge_warns_about_duplicate_contractor(connected, channel):
    machine_a, machine_b = connected
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, chain_sql(1, "Одинаковый"), chain_sql(1, "Одинаковый"), report)
    assert action == SyncAction.MERGE
    assert [row["name"] for row in report.warnings.duplicate_contractors] == ["Одинаковый"]
    assert rows(machine_b, CONTRACT_ROWS["contractor"]) == [(1, "Одинаковый"), (2, "Одинаковый")]


def test_merge_warns_about_duplicate_contract(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    sql = "INSERT INTO contract (id, contractor_id, name, date) VALUES (2, 1, '13', '2026-03-01')"
    assert sync_both(machine_a, machine_b, channel, sql, sql, report) == SyncAction.MERGE
    assert [row["name"] for row in report.warnings.duplicate_contracts] == ["13"]
    assert rows(machine_b, CONTRACT_ROWS["contract"]) == [(1, 1), (2, 1), (3, 1)]


def test_merge_warns_about_duplicate_document(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    sql = "INSERT INTO contractdocument (id, contract_id, document_name) VALUES (3, 1, 'Акт')"
    assert sync_both(machine_a, machine_b, channel, sql, sql, report) == SyncAction.MERGE
    assert [row["document_name"] for row in report.warnings.duplicate_documents] == ["Акт"]
    assert rows(machine_b, CONTRACT_ROWS["contractdocument"]) == [(1, 1), (2, 1), (3, 1), (4, 1)]


def test_merge_edits_document_and_its_payment_term_separately(shared_contract, channel):
    machine_a, machine_b = shared_contract
    action = sync_both(machine_a, machine_b, channel, "UPDATE contractdocument SET description = 'опись' WHERE id = 1",
                       "UPDATE contractpaymentterm SET days_count = 10 WHERE document_id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT description FROM contractdocument WHERE id = 1") == [("опись",)]
    assert rows(machine_b, CONTRACT_ROWS["contractpaymentterm"]) == [(1, 10)]


def test_conflict_when_payment_term_added_on_both_sides(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "INSERT INTO contractpaymentterm (document_id, payment_type) VALUES (2, 'RELATIVE')",
                       "INSERT INTO contractpaymentterm (document_id, payment_type) VALUES (2, 'FIXED')", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Сроки оплаты", "добавлено", "тоже добавлено")]


def test_merge_deletes_document_with_payment_term_removed_by_me(shared_contract, channel):
    machine_a, machine_b = shared_contract
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2,
                       "DELETE FROM contractpaymentterm WHERE document_id = 1; DELETE FROM contractdocument WHERE id = 1")
    assert action == SyncAction.MERGE
    assert rows(machine_b, CONTRACT_ROWS["contractdocument"]) == [(2, 1)]
    assert rows(machine_b, CONTRACT_ROWS["contractpaymentterm"]) == []


def test_conflict_when_contract_added_to_contractor_deleted_in_master(shared_contract, channel):
    machine_a, machine_b = shared_contract
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel,
                       "DELETE FROM contractpaymentterm; DELETE FROM contractdocument; DELETE FROM contract; DELETE FROM contractor",
                       "INSERT INTO contract (id, contractor_id, name, date) VALUES (2, 1, '13', '2026-03-01')", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Договор", "добавлено или изменено", "контрагент удалён")]


def test_merge_not_done_when_new_document_refers_to_missing_position(shared_contract, channel):
    machine_a, machine_b = shared_contract
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2,
                       "INSERT INTO contractdocument (id, contract_id, document_name, position_id) VALUES (3, 1, 'Акт', 5)")
    assert action == SyncAction.CONFLICT


FINPLAN_ROWS = "SELECT year, category, m1 FROM finplan ORDER BY year, category"


@pytest.fixture
def shared_finplan(connected, channel):
    machine_a, machine_b = connected
    run_sql(machine_a, "INSERT INTO finplan (year, category, m1) VALUES (2027, 10000, 100), (2027, 21000, 200), (2028, 10000, 300)")
    with machine_a as dbh:
        push_master(dbh, channel, PARAMS)
    with machine_b as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    return machine_a, machine_b


def test_merge_finplan_edit_does_not_block_event_merge(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    action = sync_both(machine_a, machine_b, channel, "UPDATE finplan SET m1 = 150 WHERE year = 2027 AND category = 10000", NEW_EVENT_2)
    assert action == SyncAction.MERGE
    assert rows(machine_b, FINPLAN_ROWS) == [(2027, 10000, 150), (2027, 21000, 200), (2028, 10000, 300)]
    assert rows(machine_b, "SELECT name FROM event") == [("Другое",)]


def test_merge_my_finplan_edit_when_other_changed_events(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    action = sync_both(machine_a, machine_b, channel, NEW_EVENT_2, "UPDATE finplan SET m1 = 250 WHERE year = 2027 AND category = 21000")
    assert action == SyncAction.MERGE
    assert rows(machine_b, FINPLAN_ROWS) == [(2027, 10000, 100), (2027, 21000, 250), (2028, 10000, 300)]
    with machine_a as dbh:
        assert synchronize(dbh, channel, PARAMS) == SyncAction.PULL
    assert rows(machine_a, FINPLAN_ROWS) == rows(machine_b, FINPLAN_ROWS)


def test_conflict_when_same_finplan_cell_changed_differently(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "UPDATE finplan SET m1 = 1 WHERE year = 2027 AND category = 10000",
                       "UPDATE finplan SET m1 = 2 WHERE year = 2027 AND category = 10000", report)
    assert action == SyncAction.CONFLICT
    assert [(c.title, c.topic, c.mine, c.theirs) for c in report.conflicts] == [
        ("Финплан 2027: 1. Остаток средств на начало периода", "Январь", "2,00", "1,00")]


def test_merge_adds_and_deletes_finplan_year(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    action = sync_both(machine_a, machine_b, channel, "UPDATE finplan SET m1 = 5 WHERE year = 2027 AND category = 21000",
                       "DELETE FROM finplan WHERE year = 2028; INSERT INTO finplan (year, category, m1) VALUES (2029, 10000, 7)")
    assert action == SyncAction.MERGE
    assert rows(machine_b, FINPLAN_ROWS) == [(2027, 10000, 100), (2027, 21000, 5), (2029, 10000, 7)]


def test_merge_finplan_year_added_on_both_sides_identically(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    insert = "INSERT INTO finplan (year, category, m1) VALUES (2029, 10000, 7)"
    assert sync_both(machine_a, machine_b, channel, insert, insert) == SyncAction.MERGE
    assert rows(machine_b, "SELECT COUNT(*) FROM finplan WHERE year = 2029") == [(1,)]


def test_conflict_when_finplan_year_added_on_both_sides_differently(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    report = syncmod.SyncReport()
    action = sync_both(machine_a, machine_b, channel, "INSERT INTO finplan (year, category, m1) VALUES (2029, 10000, 7)",
                       "INSERT INTO finplan (year, category, m1) VALUES (2029, 10000, 8)", report)
    assert action == SyncAction.CONFLICT
    assert [(c.topic, c.mine, c.theirs) for c in report.conflicts] == [("Январь", "8,00", "7,00")]


def test_conflict_when_finplan_row_deleted_by_me_and_changed_by_other(shared_finplan, channel):
    machine_a, machine_b = shared_finplan
    action = sync_both(machine_a, machine_b, channel, "UPDATE finplan SET m1 = 1 WHERE year = 2028",
                       "DELETE FROM finplan WHERE year = 2028")
    assert action == SyncAction.CONFLICT


def test_merge_fulfillmentdata_of_different_periods(connected, channel):
    machine_a, machine_b = connected
    insert = "INSERT INTO fulfillmentdata (startdate, enddate, \"10000\") VALUES ('{0}-01', '{0}-30', {1})"
    action = sync_both(machine_a, machine_b, channel, insert.format("2026-06", 10), insert.format("2026-07", 20))
    assert action == SyncAction.MERGE
    assert rows(machine_b, "SELECT startdate, \"10000\" FROM fulfillmentdata ORDER BY startdate") == [("2026-06-01", 10), ("2026-07-01", 20)]


def test_restore_master_info_for_folder_channel(connected, channel):
    _, machine_b = connected
    channel.master_info_path.write_text("broken", encoding="utf-8")
    with machine_b as dbh:
        restored = restore_master_info(dbh, channel, PARAMS)
        assert restored.sync_token == machine_b.meta()["sync_token"]
        assert synchronize(dbh, channel, PARAMS) == SyncAction.NOTHING
