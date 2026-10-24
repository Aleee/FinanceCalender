import zipfile

import pytest

from base.liability import Col
from base.xlswriter import ExportFormat, HiddenDisplayMode, LiabilityXlsWriter
from tests.conftest import FakeSettingsHandler
from tests.test_readpath import add_event, db_file, models, open_models  # noqa: F401


@pytest.fixture
def writer(models, tmp_path, monkeypatch):
    xls_writer = LiabilityXlsWriter(models.table, None, FakeSettingsHandler(tmp_path / "settings.ini"))
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    monkeypatch.setattr(xls_writer, "_make_temp_paths", lambda: (str(temp_dir / "a.xlsx"), str(temp_dir / "a.pdf")))
    return xls_writer


def columns_to_export() -> list[bool]:
    return [True] * (max(Col) + 1)


def test_text_starting_with_equals_stays_text(db_file, writer, tmp_path, monkeypatch):
    add_event(db_file, receiver="=1+1")
    writer.model.reload()
    target = tmp_path / "out.xlsx"
    monkeypatch.setattr(writer, "_ask_save_path", lambda *args: str(target))
    assert writer.write(ExportFormat.XLSX, columns_to_export(), HiddenDisplayMode.NONE)
    with zipfile.ZipFile(target) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "<f>" not in sheet


def test_cancelled_export_removes_temp_files(db_file, writer, tmp_path, monkeypatch):
    add_event(db_file)
    writer.model.reload()
    monkeypatch.setattr(writer, "_ask_save_path", lambda *args: "")
    assert not writer.write(ExportFormat.XLSX, columns_to_export(), HiddenDisplayMode.NONE)
    assert not list((tmp_path / "temp").iterdir())
