import json
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QWidget

import gui.manualdialog as manualdialog
import tools.build_manual as buildmod
from tests.conftest import FakeSettingsHandler

FRONT = "---\nsection: {section}\ntitle: {title}\n---\n\n"


def write_source(root: Path) -> None:
    src = root / "src"
    (root / "images" / "01").mkdir(parents=True)
    src.mkdir()
    QImage(20, 10, QImage.Format.Format_RGB32).save(str(root / "images" / "01" / "pic.png"))
    (src / "01-first.md").write_text(
        FRONT.format(section=1, title="Первый") + "# Раздел 1. Первый\n\n## Начало\n\nСм. раздел 2.\n\n"
        "Подробнее в разделах 2 и приложении 2, «Устройство», а также раздел 1 и раздел 99.\n\n"
        "![Рис](../images/01/pic.png)\n\n*Рис. 1. Подпись.*\n\n"
        "Текст {+принятая правка+}{-удалённое-}.\n\n<!-- TODO-код: убрать -->\n\n"
        "> ⚠️ **Внимание.** Осторожно.\n\n> 💡 **Совет.** Удобно.\n", encoding="utf-8")
    (src / "02-second.md").write_text(
        FRONT.format(section=2, title="Второй") + "# Раздел 2. Второй\n\n| А | Б |\n|---|---|\n| раздел 1 | x |\n\n"
        "Список:\n- один\n- два\n", encoding="utf-8")
    (src / "03-third.md").write_text(
        FRONT.format(section=3, title="Третий") + "# Раздел 3. Третий\n\nТекст.\n", encoding="utf-8")
    (src / "P2-extra.md").write_text(
        FRONT.format(section="приложение 2", title="Допы") + "# Приложение 2. Допы\n\n## Устройство\n\nТекст.\n",
        encoding="utf-8")
    (root / "GLOSSARY.md").write_text(
        "# Приложение 1. Глоссарий\n\n### А\n\n**Альфа.** Первая буква.\n\n**Бета** — см. «Альфа». См. раздел 1.\n",
        encoding="utf-8")


@pytest.fixture
def built_manual(tmp_path, monkeypatch) -> Path:
    source = tmp_path / "source"
    write_source(source)
    monkeypatch.setattr(buildmod, "SOURCE_DIR", source)
    output = tmp_path / "manual"
    assert buildmod.build_manual(output)
    return output


def test_references_become_links(built_manual):
    first = (built_manual / "01-first.html").read_text(encoding="utf-8")
    assert '<a href="02-second.html">раздел 2</a>' in first
    assert '<a href="02-second.html">разделах 2</a>' in first
    assert 'приложении <a href="P2-extra.html">2</a>, <a href="P2-extra.html#s2">«Устройство»</a>' in first
    assert "раздел 1 и раздел 99" in first
    assert "<h1" in first and "<a" not in first.split("</h1>")[0]


def test_table_cells_and_glossary_are_linked(built_manual):
    second = (built_manual / "02-second.html").read_text(encoding="utf-8")
    assert '<a href="01-first.html">раздел 1</a>' in second
    assert "<li>один</li>" in second
    glossary = (built_manual / "GLOSSARY.html").read_text(encoding="utf-8")
    assert '<a href="01-first.html">раздел 1</a>' in glossary
    assert '<a href="#t1">«Альфа»</a>' in glossary
    assert '<p id="t1"><strong>Альфа.</strong>' in glossary


def test_markup_is_cleaned_and_images_are_copied(built_manual):
    first = (built_manual / "01-first.html").read_text(encoding="utf-8")
    assert "принятая правка" in first and "удалённое" not in first
    assert "{+" not in first and "TODO" not in first
    assert 'src="images/01/pic.png"' in first
    assert (built_manual / "images" / "01" / "pic.png").is_file()
    assert first.count('<td width="5"') == 2


def test_contents_and_page_without_footer(built_manual):
    contents = json.loads((built_manual / "contents.json").read_text(encoding="utf-8"))
    titles = {group["title"]: [chapter["title"] for chapter in group["chapters"]] for group in contents["groups"]}
    assert titles["Начало"] == ["1. Первый"]
    assert titles["Основная работа"] == ["2. Второй", "3. Третий"]
    assert titles["Приложения"] == ["Приложение 1. Глоссарий", "Приложение 2. Допы"]
    first_chapter = contents["groups"][0]["chapters"][0]
    assert [item["title"] for item in first_chapter["headings"]] == ["Начало"]
    first = (built_manual / "01-first.html").read_text(encoding="utf-8")
    assert "&rarr;" not in first and "&larr;" not in first


def test_missing_sources_keep_existing_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(buildmod, "SOURCE_DIR", tmp_path / "none")
    output = tmp_path / "manual"
    assert not buildmod.build_manual(output)
    output.mkdir()
    (output / "contents.json").write_text("{}", encoding="utf-8")
    assert buildmod.build_manual(output)
    assert (output / "contents.json").read_text(encoding="utf-8") == "{}"


def test_dialog_navigates_and_follows_tree(qapp, built_manual, tmp_path, monkeypatch):
    monkeypatch.setattr(manualdialog, "manual_dir", lambda: str(built_manual))
    assert manualdialog.ManualDialog.is_available()
    dialog = manualdialog.ManualDialog(FakeSettingsHandler(tmp_path / "s.ini"))
    dialog.open_page("02-second.html")
    assert dialog.browser.source().fileName() == "02-second.html"
    assert dialog.trw_contents.currentItem().text(0) == "2. Второй"
    dialog.browser.setSource(QUrl.fromLocalFile(str(built_manual / "P2-extra.html")))
    assert dialog.trw_contents.currentItem().text(0) == "Приложение 2. Допы"
    assert dialog.browser.backwardHistoryCount() == 1
    dialog.le_find.setText("Текст")
    assert dialog.browser.textCursor().selectedText() == "Текст"
    dialog.le_find.setText("нет такого")
    assert not dialog.la_notfound.isHidden()


@pytest.fixture
def dialog(qapp, built_manual, tmp_path, monkeypatch):
    monkeypatch.setattr(manualdialog, "manual_dir", lambda: str(built_manual))
    manual = manualdialog.ManualDialog(FakeSettingsHandler(tmp_path / "s.ini"))
    manual.show()
    manual.open_page("01-first.html")
    yield manual
    if shiboken6.isValid(manual):
        manual.close()


def test_click_on_chapter_below_opened_one_selects_that_chapter(qapp, dialog):
    tree = dialog.trw_contents
    target = dialog.chapter_items["02-second.html"]
    assert dialog.chapter_items["01-first.html"].isExpanded()
    position = tree.visualItemRect(target).center()
    QTest.mousePress(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
    QTest.mouseMove(tree.viewport(), position + QPoint(1, 0))
    QTest.mouseRelease(tree.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position + QPoint(1, 0))
    QTest.qWait(50)
    assert dialog.browser.source().fileName() == "02-second.html"
    assert tree.currentItem() is target


def test_search_lists_matches_and_opens_the_exact_place(qapp, dialog):
    dialog.le_search.setText("Осторожно")
    dialog.run_search()
    assert dialog.lw_results.count() == 1
    assert dialog.la_found.text() == "Найдено: 1"
    dialog.go_to_result(dialog.lw_results.item(0))
    assert dialog.browser.source().fileName() == "01-first.html"
    assert dialog.browser.textCursor().selectedText() == "Осторожно"
    assert len(dialog.browser.extraSelections()) == 1
    dialog.le_search.setText("нет такого слова")
    dialog.run_search()
    assert dialog.la_found.text() == "Ничего не найдено" and dialog.lw_results.count() == 0
    dialog.le_search.clear()
    dialog.run_search()
    assert dialog.stw_left.currentWidget() is dialog.trw_contents and not dialog.browser.extraSelections()


def test_search_treats_yo_as_ye(qapp, dialog):
    dialog.le_search.setText("удалённое")
    dialog.run_search()
    assert dialog.lw_results.count() == 0
    dialog.le_search.setText("первая")
    dialog.run_search()
    assert dialog.lw_results.count() == 1
    dialog.le_search.setText("ПЕРВАЯ БУКВА")
    dialog.run_search()
    assert dialog.lw_results.count() == 1


def test_manual_moves_to_modal_dialog_and_back(qapp, dialog):
    main = QWidget()
    owner = QDialog(main)
    dialog.set_owner(owner)
    assert dialog.parentWidget() is owner and dialog.isVisible()
    owner.finished.emit(0)
    assert dialog.parentWidget() is main
    assert dialog.isVisible()
