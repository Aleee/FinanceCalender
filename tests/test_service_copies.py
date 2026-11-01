from types import SimpleNamespace

from PySide6.QtCore import QDate

import base.backup as backupmod
from base.backup import clean_service_copies


def settings_with_period(days):
    return SimpleNamespace(settings=SimpleNamespace(value=lambda key, default=None: days))


def stamp(days_ago: int) -> str:
    return QDate.currentDate().addDays(-days_ago).toString("yyyyMMdd")


def test_old_service_copies_removed_recent_and_foreign_kept(backup_folder, monkeypatch):
    monkeypatch.setattr(backupmod, "backup_dir", lambda: str(backup_folder))
    old, recent = stamp(91), stamp(10)
    names = [f"conflict_{old}-101010-000001.db", f"discarded_{old}-101010-000001.db", f"db_corrupt_{old}-101010.db",
             f"before_sync_{old}-101010-000001.db", f"before_restore_{old}-101010.db",
             f"conflict_{recent}-101010-000001.db", f"before_sync_{recent}-101010-000001.db", "before_migration_v7.db", "notes.txt", "conflict_bad.db"]
    for name in names:
        (backup_folder / name).write_bytes(b"x")
    assert clean_service_copies(settings_with_period(30))
    assert sorted(p.name for p in backup_folder.iterdir()) == sorted(names[5:])


def test_service_copies_follow_longer_user_period(backup_folder, monkeypatch):
    monkeypatch.setattr(backupmod, "backup_dir", lambda: str(backup_folder))
    kept, removed = f"before_sync_{stamp(150)}-101010-000001.db", f"conflict_{stamp(200)}-101010-000001.db"
    for name in (kept, removed):
        (backup_folder / name).write_bytes(b"x")
    assert clean_service_copies(settings_with_period(180))
    assert [p.name for p in backup_folder.iterdir()] == [kept]
    assert clean_service_copies(settings_with_period(9999))
    assert [p.name for p in backup_folder.iterdir()] == [kept]
    assert clean_service_copies(settings_with_period("неверно"))
    assert list(backup_folder.iterdir()) == []
