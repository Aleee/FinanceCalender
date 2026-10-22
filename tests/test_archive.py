import sqlite3
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, Qt

import gui.contractordialog as contractordialog
from base.sync import LocalState, MasterInfo, SyncAction, decide_action
from base.version import DB_VERSION
from tests.dbtools import create_db, fetch_all, read_meta, read_version, table_columns
from tests.test_readpath import db_file, open_models  # noqa: F401


SYNC_META = {"db_uuid": "u", "sync_token": "t", "change_counter": "0"}


def fill_contacts(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute("INSERT INTO contractor (id, name) VALUES (1, 'Альфа'), (2, 'Бета'), (3, 'Гамма')")
        con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '5', '2026-02-03'), (2, 1, '7', '2026-03-01')")
        con.execute("INSERT INTO contractdocument (id, contract_id, document_type, document_name) VALUES (1, 1, 1, 'Счет')")
        con.commit()
    finally:
        con.close()


def test_migration_adds_archive_columns(dbh, work_db_path):
    create_db(work_db_path, 7, SYNC_META)
    fill_contacts(work_db_path)

    assert dbh.migrate_db()

    assert read_version(work_db_path) == DB_VERSION
    assert "archived" in table_columns(work_db_path, "contractor")
    assert "archived" in table_columns(work_db_path, "contract")
    assert fetch_all(work_db_path, "SELECT archived FROM contractor") == [(0,), (0,), (0,)]
    assert fetch_all(work_db_path, "SELECT archived FROM contract") == [(0,), (0,)]
    assert int(read_meta(work_db_path)["change_counter"]) > 0


def test_old_master_is_migrated_on_copy(dbh, work_db_path, tmp_path):
    master = create_db(tmp_path / "master" / "db.db", 7, SYNC_META)
    fill_contacts(master)
    work_db_path.parent.mkdir(parents=True, exist_ok=True)

    migrated = dbh.make_migrated_copy(str(master))

    assert migrated is not None
    assert read_version(Path(migrated)) == DB_VERSION
    assert fetch_all(Path(migrated), "SELECT name, archived FROM contractor ORDER BY id") == [("Альфа", 0), ("Бета", 0), ("Гамма", 0)]
    assert read_version(master) == 7


def test_outdated_client_does_not_touch_new_master():
    local = LocalState("uuid", "token", 7, 0)
    master = MasterInfo("uuid", "other", DB_VERSION, "a", "m", "2026-10-21T10:00:00", "2026.10.21")
    assert decide_action(local, master) == SyncAction.CLIENT_OUTDATED


def test_set_archived_and_loaders(db_file, open_models, shared_dbh):
    fill_contacts(db_file)
    open_models(db_file)
    dbh = shared_dbh

    assert dbh.set_archived("contractor", 2, True)
    assert dbh.set_archived("contract", 2, True)

    assert dbh.load_contractors() == [(1, "Альфа", False), (2, "Бета", True), (3, "Гамма", False)]
    assert [row[3] for row in dbh.load_contracts(1)] == [False, True]
    assert fetch_all(db_file, "SELECT archived FROM contractor WHERE id = 2") == [(1,)]
    assert not dbh.set_archived("contractor", 99, True)
    with pytest.raises(ValueError):
        dbh.set_archived("event", 1, True)

    assert dbh.set_archived("contractor", 2, False)
    assert dbh.load_contractors()[1] == (2, "Бета", False)


def test_comboboxes_hide_archived_but_keep_included(db_file, open_models, shared_dbh):
    fill_contacts(db_file)
    open_models(db_file)
    dbh = shared_dbh
    dbh.set_archived("contractor", 2, True)
    dbh.set_archived("contract", 2, True)

    assert [name for _, name in dbh.load_contractors_for_combobox()] == ["Альфа", "Гамма"]
    assert [name for _, name in dbh.load_contractors_for_combobox(2)] == ["Альфа", "Бета (архив)", "Гамма"]
    assert [name for _, name in dbh.load_contracts_for_combobox(1)] == ["№ 5 от 03.02.2026"]
    assert [name for _, name in dbh.load_contracts_for_combobox(1, 2)] == ["№ 5 от 03.02.2026", "№ 7 от 01.03.2026 (архив)"]


def texts(list_widget, hidden: bool = False) -> list[str]:
    return [list_widget.item(i).text() for i in range(list_widget.count()) if list_widget.item(i).isHidden() == hidden]


def test_dialog_archive_flow(db_file, open_models, shared_dbh, monkeypatch, tmp_path):
    fill_contacts(db_file)
    open_models(db_file)
    dbh = shared_dbh
    monkeypatch.setattr(contractordialog, "ErrorInfoMessageBox", lambda *a, **k: pytest.fail("unexpected error box"))
    dlg = contractordialog.ContractorDialog(dbh, QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat))
    contractors = dlg.ui.lw_contractor

    assert texts(contractors) == ["Новый контрагент", "Альфа", "Бета", "Гамма"]
    contractors.setCurrentRow(2)
    assert dlg.ui.tb_archive_contractor.toolTip() == "В архив"

    dlg.on_toggle_contractor_archived()

    assert fetch_all(db_file, "SELECT archived FROM contractor ORDER BY id") == [(0,), (1,), (0,)]
    assert texts(contractors) == ["Новый контрагент", "Альфа", "Гамма"]
    assert texts(contractors, hidden=True) == ["Бета"]
    assert contractors.currentItem() is not None and not contractors.currentItem().isHidden()

    dlg.ui.chb_show_archived.setChecked(True)
    assert texts(contractors) == ["Новый контрагент", "Альфа", "Бета", "Гамма"]
    contractors.setCurrentRow(2)
    assert dlg.ui.tb_archive_contractor.toolTip() == "Вернуть из архива"
    assert contractors.currentItem().font().italic()

    dlg.on_toggle_contractor_archived()
    assert fetch_all(db_file, "SELECT archived FROM contractor ORDER BY id") == [(0,), (0,), (0,)]
    assert not contractors.currentItem().font().italic()

    contractors.setCurrentRow(1)
    dlg.on_continue_to_contracts()
    contracts = dlg.ui.lw_contract
    contracts.setCurrentRow(2)
    dlg.on_toggle_contract_archived()
    assert fetch_all(db_file, "SELECT archived FROM contract ORDER BY id") == [(0,), (1,)]
    assert texts(contracts) == ["Новый договор", "5 от 03.02.2026", "7 от 01.03.2026"]

    assert dlg.ui.chb_show_archived.isChecked()
    dlg.ui.chb_show_archived.setChecked(False)
    assert texts(contracts) == ["Новый договор", "5 от 03.02.2026"]
    assert texts(contracts, hidden=True) == ["7 от 01.03.2026"]
    assert contracts.currentItem().data(Qt.ItemDataRole.UserRole) in (0, 1)


def make_dialog(db_file, open_models, shared_dbh, tmp_path):
    open_models(db_file)
    return contractordialog.ContractorDialog(shared_dbh, QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat))


def test_steps_line_shows_chosen_values_escaped(db_file, open_models, shared_dbh, tmp_path):
    con = sqlite3.connect(db_file)
    con.execute("INSERT INTO contractor (id, name) VALUES (1, 'А<b>&Б')")
    con.execute("INSERT INTO contract (id, contractor_id, name, date) VALUES (1, 1, '5<i>', '2026-02-03')")
    con.commit()
    con.close()
    dlg = make_dialog(db_file, open_models, shared_dbh, tmp_path)
    assert "Контрагент" in dlg.ui.lbl_steps.text()

    dlg.ui.lw_contractor.setCurrentRow(1)
    dlg.on_continue_to_contracts()
    steps = dlg.ui.lbl_steps.text()
    assert "А&lt;b&gt;&amp;Б" in steps
    assert "А<b>&Б" not in steps
    assert "<b>Договор</b>" in steps

    dlg.ui.lw_contract.setCurrentRow(1)
    dlg.on_continue_to_documents()
    steps = dlg.ui.lbl_steps.text()
    assert "А&lt;b&gt;&amp;Б" in steps
    assert "5&lt;i&gt; от 03.02.2026" in steps
    assert "<b>Документ</b>" in steps


def test_dialog_navigation(db_file, open_models, shared_dbh, tmp_path):
    fill_contacts(db_file)
    dlg = make_dialog(db_file, open_models, shared_dbh, tmp_path)
    ui = dlg.ui

    assert ui.stw_main.currentIndex() == 0
    assert ui.pb_back.isHidden()
    assert not ui.chb_show_archived.isHidden()
    assert ui.pb_next.text() == "Далее"

    ui.lw_contractor.setCurrentRow(1)
    ui.pb_next.click()
    assert ui.stw_main.currentIndex() == 1
    assert not ui.pb_back.isHidden()
    assert ui.pb_next.text() == "Далее"

    ui.lw_contract.setCurrentRow(1)
    ui.pb_next.click()
    assert ui.stw_main.currentIndex() == 2
    assert ui.chb_show_archived.isHidden()
    ui.lw_document.setCurrentRow(0)
    assert ui.pb_next.text() == "Создать"
    ui.lw_document.setCurrentRow(1)
    assert ui.pb_next.text() == "Открыть"

    ui.pb_back.click()
    assert ui.stw_main.currentIndex() == 1
    assert not ui.chb_show_archived.isHidden()
    ui.pb_back.click()
    assert ui.stw_main.currentIndex() == 0
    assert ui.pb_back.isHidden()
