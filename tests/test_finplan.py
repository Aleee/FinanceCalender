import sqlite3
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt

from base.version import DB_VERSION
from gui.finplanmodel import FinPlanTableModel
from tests.dbtools import create_db

EDIT = Qt.ItemDataRole.EditRole
SALARY = 31101
MATERIALS = 31102
VARIABLE_COSTS = 31100


def cell(model: FinPlanTableModel, category: int, month: int = 1):
    return model.index(model.categories.index(category), month)


@pytest.mark.parametrize("text, expected", [("1000", 1000), ("1 000", 1000), ("1000,5", Decimal("1000.5")),
                                             ("1 000.50", Decimal("1000.5")), ("0,005", Decimal("0.01")),
                                             ("-2,25", Decimal("-2.25")), ("", None)])
def test_input_accepts_whole_and_fractional_numbers(qapp, text, expected):
    model = FinPlanTableModel()
    assert model.setData(cell(model, SALARY), text, EDIT)
    assert model.values[SALARY][0] == expected


@pytest.mark.parametrize("text", ["abc", "1,2,3", "1e999", "nan", "inf"])
def test_invalid_input_is_rejected_and_reported(qapp, text):
    model = FinPlanTableModel()
    model.setData(cell(model, SALARY), "5", EDIT)
    rejected = []
    model.invalidInput.connect(lambda: rejected.append(True))
    assert not model.setData(cell(model, SALARY), text, EDIT)
    assert model.values[SALARY][0] == 5
    assert rejected == [True]


def test_totals_are_exact_decimals(qapp):
    model = FinPlanTableModel()
    model.setData(cell(model, SALARY), "0,1", EDIT)
    model.setData(cell(model, MATERIALS), "0,2", EDIT)
    assert model.values[VARIABLE_COSTS][0] == Decimal("0.3")
    assert model.data(cell(model, VARIABLE_COSTS), Qt.ItemDataRole.DisplayRole) == "0,30"


def test_display_always_shows_kopecks(qapp):
    model = FinPlanTableModel()
    model.setData(cell(model, SALARY, 1), "1500000", EDIT)
    model.setData(cell(model, SALARY, 2), "1500000,5", EDIT)
    assert model.data(cell(model, SALARY, 1), Qt.ItemDataRole.DisplayRole) == "1 500 000,00"
    assert model.data(cell(model, SALARY, 2), Qt.ItemDataRole.DisplayRole) == "1 500 000,50"
    assert model.data(cell(model, SALARY, 2), EDIT) == "1500000,50"
    assert model.data(cell(model, SALARY, 1), FinPlanTableModel.internalValueRole) == 1500000
    assert model.data(cell(model, SALARY, 2), FinPlanTableModel.internalValueRole) == 1500000.5


def test_load_values_accepts_database_numbers(qapp):
    model = FinPlanTableModel()
    model.load_values({SALARY: [1, 2.5, None] + [None] * 9})
    assert model.values[SALARY][:3] == [Decimal(1), Decimal("2.5"), None]


def test_finplan_round_trip_through_database(dbh, work_db_path):
    create_db(work_db_path, DB_VERSION)
    dbh.db.close()
    dbh.db.setDatabaseName(str(work_db_path))
    assert dbh.db.open()
    try:
        model = FinPlanTableModel()
        model.setData(cell(model, SALARY, 1), "1000", EDIT)
        model.setData(cell(model, SALARY, 2), "1000,55", EDIT)
        model.setData(cell(model, SALARY, 3), "0,1", EDIT)
        assert dbh.save_finplan_to_db(2030, model.FINPLAN_STRUCTURE, model)
        loaded = dbh.load_finplan_from_db(2030, model.FINPLAN_STRUCTURE)
        assert loaded[SALARY][:4] == [1000, 1000.55, 0.1, None]
        plan = dbh.load_fulfillmentplanvalues_from_db(2030, 1, 3)
        assert plan[SALARY] == 2001
        assert isinstance(plan[SALARY], int)
        assert dbh.load_fulfillmentplanvalues_from_db(2030, 4, 5)[SALARY] is None
    finally:
        dbh.db.close()
    con = sqlite3.connect(work_db_path)
    try:
        stored = con.execute("SELECT typeof(m1), typeof(m2), typeof(m4) FROM finplan WHERE category = ?", (SALARY,)).fetchone()
    finally:
        con.close()
    assert stored == ("integer", "real", "null")
