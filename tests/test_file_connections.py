from PySide6.QtCore import qInstallMessageHandler

from tests.dbtools import create_db


def test_helper_connections_leave_no_qt_warnings(dbh, work_db_path, tmp_path):
    messages: list[str] = []
    create_db(work_db_path, 4, {"marker": "a"})
    assert dbh.migrate_db()
    dbh.open_db_connection()
    bad = tmp_path / "bad.db"
    bad.write_bytes(b"not sqlite" * 100)
    copy = tmp_path / "copy.db"
    qInstallMessageHandler(lambda mode, context, message: messages.append(message))
    try:
        assert dbh.copy_db_file(str(copy))
        assert dbh.check_file_integrity(str(copy))
        assert dbh.read_file_settings(str(copy), ("db_uuid",))
        assert dbh.create_sync_snapshot(str(tmp_path / "snapshot.db"), "token") is not None
        assert not dbh.check_file_integrity(str(bad))
        assert dbh.read_file_settings(str(bad), ("db_uuid",)) is None
        assert not dbh.copy_db_file(str(copy))
    finally:
        qInstallMessageHandler(None)
    assert [message for message in messages if "still in use" in message] == []
