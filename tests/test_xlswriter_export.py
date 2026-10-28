import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QFileDialog

import base.xlswriter as xlsmod
from base.liability import Col, LiabilityCategory
from base.xlswriter import (ExportFormat, FulfilmentXlsWriter, HiddenDisplayMode, LiabilityXlsWriter,
                            PdfConversionError)
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.fulfilmentmodel import FulfilmentModel
from tests.conftest import FakeSettingsHandler
from tests.test_readpath import add_event, day, db_file, models, open_models  # noqa: F401

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
HEADER_ROWS = LiabilityXlsWriter.HEADER_ROWS_NUMBER


def read_sheet(path: Path) -> dict[tuple[int, int], str | float]:
    with zipfile.ZipFile(path) as archive:
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.itertext()) for node in shared.findall("m:si", NS)]
    cells: dict[tuple[int, int], str | float] = {}
    for cell in sheet.iter(f"{{{NS['m']}}}c"):
        value = cell.find("m:v", NS)
        if value is None:
            continue
        match = re.fullmatch(r"([A-Z]+)(\d+)", cell.get("r"))
        column = 0
        for letter in match.group(1):
            column = column * 26 + ord(letter) - 64
        position = (int(match.group(2)) - 1, column - 1)
        cells[position] = strings[int(value.text)] if cell.get("t") == "s" else float(value.text)
    return cells


def all_columns() -> list[bool]:
    return [True] * (max(Col) + 1)


class Dialogs:

    def __init__(self):
        self.target = ""
        self.answer = YesNoMessagebox.YES_RETURN_VALUE
        self.questions: list[str] = []
        self.errors: list[str] = []


@pytest.fixture
def dialogs(monkeypatch) -> Dialogs:
    state = Dialogs()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (state.target, ""))
    monkeypatch.setattr(YesNoMessagebox, "exec", lambda self: state.questions.append(self.text()) or state.answer)
    monkeypatch.setattr(ErrorInfoMessageBox, "exec", lambda self: state.errors.append(self.text()) or 0)
    return state


@pytest.fixture
def settings(tmp_path) -> FakeSettingsHandler:
    return FakeSettingsHandler(tmp_path / "settings.ini")


@pytest.fixture
def temp_dir(tmp_path, monkeypatch) -> Path:
    folder = tmp_path / "temp"
    folder.mkdir()
    monkeypatch.setattr(xlsmod.BaseXlsWriter, "_make_temp_paths",
                        lambda self: (str(folder / "a.xlsx"), str(folder / "a.pdf")))
    return folder


@pytest.fixture
def writer(models, settings, temp_dir) -> LiabilityXlsWriter:
    return LiabilityXlsWriter(models.table, None, settings)


def export(writer, db_file, tmp_path, dialogs, *, mode=HiddenDisplayMode.NONE, columns=None, name="out.xlsx") -> Path:
    writer.model.reload()
    dialogs.target = str(tmp_path / name)
    assert writer.write(ExportFormat.XLSX, columns or all_columns(), mode)
    return tmp_path / name


def column_values(cells, column: int) -> list:
    return [value for (row, col), value in sorted(cells.items()) if col == column and row >= HEADER_ROWS]


def test_export_contains_rows_and_numeric_amounts(db_file, writer, tmp_path, dialogs):
    add_event(db_file, receiver="ООО Первая", total="1234.56")
    add_event(db_file, receiver="ООО Вторая", total="100.00")
    cells = read_sheet(export(writer, db_file, tmp_path, dialogs))
    receivers = column_values(cells, Col.RECEIVER)
    assert "ООО Первая" in receivers and "ООО Вторая" in receivers
    amounts = column_values(cells, Col.TOTALAMOUNT)
    assert 1234.56 in amounts and 100.0 in amounts
    assert all(isinstance(value, float) for value in amounts)


@pytest.mark.parametrize("text", ["=1+1", "+SUM(A1)", "@cmd", "http://example.com/x"])
def test_dangerous_text_is_written_as_plain_string(db_file, writer, tmp_path, dialogs, text):
    add_event(db_file, receiver=text)
    target = export(writer, db_file, tmp_path, dialogs)
    with zipfile.ZipFile(target) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "<f>" not in sheet and "<hyperlink" not in sheet
        assert not any(name.endswith(".rels") and "hyperlink" in archive.read(name).decode("utf-8")
                       for name in archive.namelist() if "worksheets/_rels" in name)
    assert text in column_values(read_sheet(target), Col.RECEIVER)


@pytest.mark.parametrize("mode, visible, hidden_receiver, hidden_amount", [
    (HiddenDisplayMode.NONE, True, False, False),
    (HiddenDisplayMode.FULL, True, True, True),
    (HiddenDisplayMode.SUMONLY, True, False, True),
])
def test_hidden_rows_follow_display_mode(db_file, writer, tmp_path, dialogs, mode, visible, hidden_receiver, hidden_amount):
    add_event(db_file, receiver="Видимый", total="111.00")
    add_event(db_file, receiver="Скрытый", total="222.00", hidden=1)
    cells = read_sheet(export(writer, db_file, tmp_path, dialogs, mode=mode))
    receivers = column_values(cells, Col.RECEIVER)
    assert ("Видимый" in receivers) == visible
    assert ("Скрытый" in receivers) == hidden_receiver
    assert (222.0 in column_values(cells, Col.TOTALAMOUNT)) == hidden_amount


def test_hidden_filter_is_restored_after_export(db_file, writer, tmp_path, dialogs):
    add_event(db_file)
    assert not writer.model.store.exclude_hidden
    export(writer, db_file, tmp_path, dialogs, mode=HiddenDisplayMode.NONE)
    assert not writer.model.store.exclude_hidden


def test_hidden_filter_is_restored_when_export_fails(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    writer.model.reload()

    def broken(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(writer, "_estimate_line_count", broken)
    with pytest.raises(RuntimeError):
        writer.write(ExportFormat.XLSX, all_columns(), HiddenDisplayMode.NONE)
    assert not writer.model.store.exclude_hidden
    assert not list((tmp_path / "temp").glob("*.pdf"))


def test_unselected_columns_are_not_exported(db_file, writer, tmp_path, dialogs):
    add_event(db_file, receiver="ООО Колонки")
    columns = all_columns()
    columns[Col.RECEIVER] = False
    cells = read_sheet(export(writer, db_file, tmp_path, dialogs, columns=columns))
    assert column_values(cells, Col.RECEIVER) == []
    assert column_values(cells, Col.TOTALAMOUNT) != []


def test_suffix_is_added_and_temp_files_removed(db_file, writer, tmp_path, dialogs):
    add_event(db_file)
    target = export(writer, db_file, tmp_path, dialogs, name="report")
    assert not target.exists() and (tmp_path / "report.xlsx").exists()
    assert not list((tmp_path / "temp").iterdir())


def test_overwrite_is_confirmed_and_can_be_declined(db_file, writer, tmp_path, dialogs):
    add_event(db_file)
    writer.model.reload()
    target = tmp_path / "out.xlsx"
    target.write_bytes(b"precious")
    dialogs.target = str(target)
    dialogs.answer = YesNoMessagebox.NO_RETURN_VALUE
    assert not writer.write(ExportFormat.XLSX, all_columns(), HiddenDisplayMode.NONE)
    assert target.read_bytes() == b"precious" and len(dialogs.questions) == 1
    assert not list((tmp_path / "temp").iterdir())
    dialogs.answer = YesNoMessagebox.YES_RETURN_VALUE
    assert writer.write(ExportFormat.XLSX, all_columns(), HiddenDisplayMode.NONE)
    assert target.read_bytes() != b"precious"


def test_copy_failure_reports_error_and_cleans_up(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    writer.model.reload()
    dialogs.target = str(tmp_path / "out.xlsx")

    def failing_copy(source, target):
        raise PermissionError("file is open in Excel")

    monkeypatch.setattr(xlsmod.shutil, "copy2", failing_copy)
    assert not writer.write(ExportFormat.XLSX, all_columns(), HiddenDisplayMode.NONE)
    assert len(dialogs.errors) == 1
    assert not (tmp_path / "out.xlsx").exists()
    assert not list((tmp_path / "temp").iterdir())
    assert writer.settings_handler.settings.value("Export/lastpath") is None


def test_last_directory_is_remembered_and_reused(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    folder = tmp_path / "exports"
    folder.mkdir()
    export(writer, db_file, folder, dialogs)
    assert writer.settings_handler.settings.value("Export/lastpath") == str(folder)
    assert writer._default_file_path("a.xlsx") == str(folder / "a.xlsx")
    writer.settings_handler.settings.setValue("Export/lastpath", str(tmp_path / "gone"))
    monkeypatch.setattr(xlsmod, "export_dir", lambda: str(tmp_path / "default"))
    assert writer._default_file_path("a.xlsx") == str(tmp_path / "default" / "a.xlsx")


def test_pdf_without_excel_reports_error(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    writer.model.reload()
    dialogs.target = str(tmp_path / "out.pdf")
    monkeypatch.setattr(xlsmod, "get_pdf_converter", lambda: None)
    assert not writer.write(ExportFormat.PDF, all_columns(), HiddenDisplayMode.NONE)
    assert len(dialogs.errors) == 1 and "Excel" in dialogs.errors[0]
    assert not (tmp_path / "out.pdf").exists()
    assert not list((tmp_path / "temp").iterdir())


class FakeConverter:

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.converted: list[tuple[str, str]] = []

    def convert(self, xlsx_path: str, pdf_path: str) -> None:
        self.converted.append((xlsx_path, pdf_path))
        if self.fail:
            raise PdfConversionError("Excel не смог записать PDF")
        Path(pdf_path).write_bytes(b"%PDF")


def test_pdf_is_converted_and_copied(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    writer.model.reload()
    converter = FakeConverter()
    monkeypatch.setattr(xlsmod, "get_pdf_converter", lambda: converter)
    dialogs.target = str(tmp_path / "out.pdf")
    assert writer.write(ExportFormat.PDF, all_columns(), HiddenDisplayMode.NONE)
    assert (tmp_path / "out.pdf").read_bytes() == b"%PDF"
    assert len(converter.converted) == 1
    assert not list((tmp_path / "temp").iterdir())


def test_pdf_conversion_failure_is_reported(db_file, writer, tmp_path, dialogs, monkeypatch):
    add_event(db_file)
    writer.model.reload()
    monkeypatch.setattr(xlsmod, "get_pdf_converter", lambda: FakeConverter(fail=True))
    dialogs.target = str(tmp_path / "out.pdf")
    assert not writer.write(ExportFormat.PDF, all_columns(), HiddenDisplayMode.NONE)
    assert dialogs.errors == ["Excel не смог записать PDF"]
    assert not (tmp_path / "out.pdf").exists()
    assert not list((tmp_path / "temp").iterdir())


def test_fulfilment_export_writes_plan_fact_and_percent(qapp, tmp_path, settings, temp_dir, dialogs):
    model = FulfilmentModel()
    payments = [(int(LiabilityCategory.SALARIES), "500", day(0), "=Получатель", "Зарплата", 0, 0, 0)]
    model.setup_model(True, payments, [100, 200, 300, 0, 0], {31101: 1000})
    writer = FulfilmentXlsWriter(model, None, settings)
    dialogs.target = str(tmp_path / "plan.xlsx")
    assert writer.write(True, QDate.currentDate().addDays(-30), QDate.currentDate(), ExportFormat.XLSX)
    cells = read_sheet(tmp_path / "plan.xlsx")
    row = next(r for (r, c), value in cells.items() if c == 0 and value == "3.1.1.1.")
    assert cells[(row, 2)] == 1000 and cells[(row, 3)] == 500 and cells[(row, 4)] == -500
    assert cells[(row, 5)] == pytest.approx(0.5)
    assert not list((tmp_path / "temp").iterdir())
    assert settings.settings.value("Export/fulfilmentlastpath") == str(tmp_path)


def test_fulfilment_export_cancelled_leaves_nothing(qapp, tmp_path, settings, temp_dir, dialogs):
    model = FulfilmentModel()
    model.setup_model(True, [], [0, 0, 0, 0, 0], {})
    writer = FulfilmentXlsWriter(model, None, settings)
    dialogs.target = ""
    assert not writer.write(True, QDate.currentDate(), QDate.currentDate(), ExportFormat.XLSX)
    assert not list((tmp_path / "temp").iterdir())
