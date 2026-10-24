import sqlite3

import pytest
from PySide6.QtCore import QDate

from base.version import DB_VERSION
from gui.fulfillmentoptiondialog import FulfillmentOptionDialog
from tests.dbtools import create_db, fetch_all

BEGIN = QDate(2026, 1, 1)
END = QDate(2026, 1, 31)


@pytest.fixture
def hdb(tmp_path, shared_dbh):
    path = create_db(tmp_path / "db" / "db.db", DB_VERSION)
    with sqlite3.connect(path) as con:
        con.execute('DROP TABLE fulfillmentdata')
        con.execute('CREATE TABLE fulfillmentdata (startdate TEXT, enddate TEXT, "10000" INTEGER, "21000" INTEGER, '
                    '"22000" INTEGER, "23100" INTEGER, "23200" INTEGER, UNIQUE(enddate, startdate))')
    con.close()
    shared_dbh.db.close()
    shared_dbh.db.setDatabaseName(str(path))
    assert shared_dbh.db.open()
    shared_dbh.path = path
    yield shared_dbh
    shared_dbh.db.close()
    shared_dbh.db.setConnectOptions("")


class FakeSpinBox:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class FakeUi:
    def __init__(self, values):
        for name, value in zip(("spb_10000", "spb_21000", "spb_22000", "spb_23100", "spb_23200"), values):
            setattr(self, name, FakeSpinBox(value))


class FakeDialog:
    def __init__(self, db_handler, values):
        self.db_handler = db_handler
        self.ui = FakeUi(values)


def rows(hdb):
    return fetch_all(hdb.path, "SELECT * FROM fulfillmentdata")


def save(hdb, values):
    FulfillmentOptionDialog.save_inflow(FakeDialog(hdb, values), BEGIN, END)


def test_zero_values_without_saved_row_write_nothing(hdb):
    save(hdb, [0, 0, 0, 0, 0])
    assert rows(hdb) == []


def test_zeroing_saved_values_overwrites_them(hdb):
    save(hdb, [100, 200, 300, 400, 500])
    assert len(rows(hdb)) == 1
    save(hdb, [0, 0, 0, 0, 0])
    assert [int(value) for value in rows(hdb)[0][2:]] == [0, 0, 0, 0, 0]
