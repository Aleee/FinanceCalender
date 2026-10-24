from PySide6.QtCore import QDate

import base.backup as backupmod
from base.backup import clean_service_copies


def test_old_service_copies_removed_recent_and_foreign_kept(backup_folder, monkeypatch):
    monkeypatch.setattr(backupmod, "backup_dir", lambda: str(backup_folder))
    old = QDate.currentDate().addDays(-91).toString("yyyyMMdd")
    recent = QDate.currentDate().addDays(-10).toString("yyyyMMdd")
    names = [f"conflict_{old}-101010-000001.db", f"discarded_{old}-101010-000001.db", f"db_corrupt_{old}-101010.db",
             f"before_sync_{old}-101010-000001.db", f"before_restore_{old}-101010.db",
             f"conflict_{recent}-101010-000001.db", f"before_sync_{recent}-101010-000001.db", "before_migration_v7.db", "notes.txt", "conflict_bad.db"]
    for name in names:
        (backup_folder / name).write_bytes(b"x")
    assert clean_service_copies()
    assert sorted(p.name for p in backup_folder.iterdir()) == sorted(names[5:])
