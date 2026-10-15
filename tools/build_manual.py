import argparse
import html
import itertools
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "docs" / "manual"
OUTPUT_DIR = ROOT / "manual"

GROUPS = (
    ("Начало", "section", range(0, 2)),
    ("Основная работа", "section", range(2, 8)),
    ("Сверка и отчёты", "section", range(8, 12)),
    ("Настройка и сохранность данных", "section", range(12, 16)),
    ("Приложения", "appendix", range(1, 5)),
)

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CALLOUT_GAP = re.compile(r"(?m)^(>[^\n]*)\n\n(?=> (?:⚠️|💡|🍎|ℹ️))")
CHANGE_ADDED = re.compile(r"\{\+(.+?)\+\}", re.DOTALL)
CHANGE_REMOVED = re.compile(r"\{-(.+?)-\}", re.DOTALL)
CHANGE_REMOVED_QUOTE = re.compile(r"(?m)^>[ \t]*\{-[^\n]*?-\}[ \t]*\n")
LIST_WITHOUT_GAP = re.compile(r"(?m)^(?![-*+] |\d+\. |\s|>|\||#)([^\n]+)\n(?=[-*] )")
HTML_TAG = re.compile(r"(<[^>]+>)")
TAG_NAME = re.compile(r"</?\s*([a-zA-Z0-9]+)")
UNLINKED_TAGS = {"a", "code", "pre", "h1", "h2", "h3", "h4", "h5", "h6"}

REF_WORD = (r"(?:[Рр]аздел(?:а|е|у|ом|ы|ов|ам|ах|ами)?"
            r"|[Пп]риложени(?:е|я|ю|ем|и|й|ям|ях|ями))")
REF_NUMBERS = r"\d+(?:(?:\s*[–-]\s*|\s*,\s*|\s+и\s+)\d+)*"
REFERENCE = re.compile(rf"\b({REF_WORD})\s+({REF_NUMBERS})(?:,\s*«([^»]+)»)?")
GLOSSARY_REFERENCE = re.compile(r"(?i:см\.)\s*«([^»]+)»")
GLOSSARY_TERM = re.compile(r"<p><strong>([^<]+?)(\.?)</strong>")

CALLOUT_STYLES = {
    "⚠": ("#d98a00", "#fff6e3"),
    "💡": ("#2e9d4f", "#ebf7ee"),
    "🍎": ("#8a8f98", "#f1f2f4"),
    "ℹ": ("#2f7fd0", "#e8f2fc"),
}
DEFAULT_CALLOUT_STYLE = ("#5b7aa6", "#f1f4f9")
FIRST_STRONG = re.compile(r"<strong>(.*?)</strong>", re.DOTALL)

ACCENT = "#1f3a5f"
TABLE_HEADER_BG = "#e6ecf4"
TABLE_STRIPE_BG = "#f7f9fc"
TABLE_LINE = "#d9e0e9"

CSS = """
p { line-height: 135%; margin-top: 0px; margin-bottom: 12px; }
h1 { color: #1f3a5f; margin-top: 6px; margin-bottom: 4px; }
h2 { color: #1f3a5f; margin-top: 4px; margin-bottom: 4px; }
h3 { color: #2b5287; margin-top: 34px; margin-bottom: 8px; }
h4 { color: #44546a; margin-top: 18px; margin-bottom: 6px; }
a { color: #1a62c4; }
code { background-color: #edf0f5; color: #7a2e55; font-family: Consolas, monospace; }
ul, ol { margin-top: 2px; margin-bottom: 14px; }
li { line-height: 135%; margin-top: 3px; margin-bottom: 3px; }
th { color: #1f3a5f; }
"""

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


@dataclass
class Chapter:
    kind: str
    number: int
    source: Path
    title: str = ""
    text: str = ""
    body: str = ""
    headings: list[dict] = field(default_factory=list)

    @property
    def file(self) -> str:
        return self.source.stem + ".html"


def split_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t", "-")):
            meta[key.strip()] = value.split("#")[0].strip()
    return meta, text[match.end():]


def accept_change_marks(text: str) -> str:
    text = CHANGE_REMOVED_QUOTE.sub("", text)
    text = CHANGE_REMOVED.sub("", CHANGE_ADDED.sub(lambda match: match.group(1).strip(), text))
    return re.sub(r"(?m)^(?:[-*]|\d+\.)[ \t]*\n", "", text)


def read_chapter(path: Path) -> Chapter:
    meta, text = split_front_matter(path.read_text(encoding="utf-8"))
    if path.name == "GLOSSARY.md":
        kind, number = "appendix", 1
    else:
        section = meta.get("section", "")
        kind = "appendix" if section.startswith("приложение") else "section"
        number = int(section.split()[-1])
    text = HTML_COMMENT.sub("", accept_change_marks(text))
    return Chapter(kind, number, path, text=text)


def find_headings(tokens: list[dict]) -> list[dict]:
    flat = []

    def walk(items: list[dict]) -> None:
        for token in items:
            if token["level"] > 1:
                flat.append(token)
            walk(token["children"])

    walk(tokens)
    if not flat:
        return []
    level = min(token["level"] for token in flat)
    return [{"title": token["name"], "anchor": token["id"]} for token in flat if token["level"] == level]


def render_markdown(chapter: Chapter) -> None:
    import markdown

    ids = itertools.count(1)
    converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": lambda value, separator: f"s{next(ids)}"}})
    text = LIST_WITHOUT_GAP.sub(r"\1\n\n", chapter.text)
    chapter.body = converter.convert(CALLOUT_GAP.sub(r"\1\n\n<!-- -->\n\n", text))
    chapter.headings = find_headings(converter.toc_tokens)
    first_heading = re.search(r"<h1[^>]*>(.*?)</h1>", chapter.body, re.DOTALL)
    chapter.title = html.unescape(re.sub(r"<[^>]+>", "", first_heading.group(1))) if first_heading else chapter.source.stem


def make_callout(match: re.Match) -> str:
    content = match.group(1)
    first_text = re.sub(r"<[^>]+>", "", content).lstrip()
    bar_color, background = CALLOUT_STYLES.get(first_text[:1], DEFAULT_CALLOUT_STYLE)
    if first_text[:1] in CALLOUT_STYLES:
        content = FIRST_STRONG.sub(rf'<strong><font color="{bar_color}">\1</font></strong>', content, count=1)
    return (f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top: 6px; margin-bottom: 18px;"><tr>'
            f'<td width="5" bgcolor="{bar_color}"></td>'
            f'<td bgcolor="{background}" style="padding: 10px 16px 0px 16px;">{content}</td></tr></table>')


def make_heading(match: re.Match) -> str:
    level = match.group(1)
    margin = 24 if level == "2" else 0
    return (f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top: {margin}px; margin-bottom: 10px;">'
            f'<tr><td style="border-bottom: 1px solid {TABLE_LINE};">{match.group(0)}</td></tr></table>')


def stripe_rows(match: re.Match) -> str:
    rows = itertools.count()
    return re.sub(r"<tr>", lambda _: f'<tr bgcolor="{TABLE_STRIPE_BG}">' if next(rows) % 2 else "<tr>", match.group(0))


def adapt_for_qt(body: str) -> str:
    body = HTML_COMMENT.sub("", body)
    body = re.sub(r"<blockquote>(.*?)</blockquote>", make_callout, body, flags=re.DOTALL)
    body = re.sub(r"<h([12])[ >].*?</h\1>", make_heading, body, flags=re.DOTALL)
    body = re.sub(r"<tbody>.*?</tbody>", stripe_rows, body, flags=re.DOTALL)
    body = body.replace("<table>", '<table width="100%" cellspacing="0" cellpadding="8" '
                                   'style="border-collapse: collapse; margin-top: 18px; margin-bottom: 18px;">')
    body = re.sub(r"<th(?=[ >])", f'<th align="left" bgcolor="{TABLE_HEADER_BG}" style="border-bottom: 2px solid {ACCENT};"', body)
    body = re.sub(r"<td(?=[ >])(?![^>]*bgcolor)(?![^>]*width=\"5\")", f'<td style="border-bottom: 1px solid {TABLE_LINE};"', body)
    body = re.sub(r"<p>(<img [^>]*>)</p>", r'<p align="center" style="margin-top: 10px; margin-bottom: 4px; line-height: 100%;">\1</p>', body)
    body = re.sub(r"<p>(<em>Рис\. .*?</em>)</p>",
                  r'<p align="center" style="margin-top: 0px; margin-bottom: 22px; line-height: 100%;"><span style="color: #6b7280; font-size: 9.5pt;">\1</span></p>',
                  body, flags=re.DOTALL)
    return body


def copy_images(chapter: Chapter, output_dir: Path) -> list[str]:
    missing = []

    def replace(match: re.Match) -> str:
        link = match.group(1)
        if link.startswith(("http://", "https://", "data:")):
            return match.group(0)
        source = (chapter.source.parent / link).resolve()
        if not source.is_file():
            missing.append(link)
            return match.group(0)
        relative = Path("images") / source.relative_to((SOURCE_DIR / "images").resolve())
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return f'src="{relative.as_posix()}"'

    chapter.body = re.sub(r'src="([^"]+)"', replace, chapter.body)
    return missing


def link_references(chapter: Chapter, chapters: dict[tuple[str, int], Chapter], warnings: list[str]) -> None:
    def chapter_link(kind: str, number: int, label: str, anchor: str = "") -> str:
        target = chapters.get((kind, number))
        if target is None:
            warnings.append(f"{chapter.file}: нет раздела для ссылки «{label}»")
            return label
        if target is chapter and not anchor:
            return label
        return f'<a href="{target.file}{"#" + anchor if anchor else ""}">{label}</a>'

    def replace(match: re.Match) -> str:
        word, numbers, title = match.groups()
        kind = "appendix" if word.lower().startswith("приложени") else "section"
        prefix = match.group(0)[:match.start(2) - match.start()]
        if numbers.isdigit() and not title:
            return chapter_link(kind, int(numbers), prefix + numbers)
        linked = re.sub(r"\d+", lambda number: chapter_link(kind, int(number.group()), number.group()), numbers)
        tail = ""
        if title:
            tail = f", «{title}»"
            target = chapters.get((kind, int(numbers))) if numbers.isdigit() else None
            heading = next((item for item in target.headings if item["title"].lower() == title.lower()), None) if target else None
            if heading:
                tail = f', <a href="{target.file}#{heading["anchor"]}">«{title}»</a>'
        return prefix + linked + tail

    chapter.body = process_text_nodes(chapter.body, lambda text: REFERENCE.sub(replace, text))


def process_text_nodes(body: str, handler) -> str:
    parts = HTML_TAG.split(body)
    depth = 0
    for index, part in enumerate(parts):
        if index % 2:
            name = TAG_NAME.match(part)
            if name and name.group(1).lower() in UNLINKED_TAGS and not part.endswith("/>"):
                depth += -1 if part.startswith("</") else 1
        elif depth == 0:
            parts[index] = handler(part)
    return "".join(parts)


def link_glossary(chapter: Chapter) -> None:
    terms: dict[str, str] = {}
    ids = itertools.count(1)

    def add_id(match: re.Match) -> str:
        anchor = f"t{next(ids)}"
        terms[html.unescape(match.group(1)).lower()] = anchor
        return f'<p id="{anchor}"><strong>{match.group(1)}{match.group(2)}</strong>'

    chapter.body = GLOSSARY_TERM.sub(add_id, chapter.body)

    def replace(match: re.Match) -> str:
        title = match.group(1)
        anchor = terms.get(html.unescape(title).lower())
        if not anchor:
            return match.group(0)
        return f'{match.group(0)[:match.start(1) - match.start() - 1]}<a href="#{anchor}">«{title}»</a>'

    chapter.body = process_text_nodes(chapter.body, lambda text: GLOSSARY_REFERENCE.sub(replace, text))


def make_contents(ordered: list[Chapter]) -> dict:
    groups = []
    for title, kind, numbers in GROUPS:
        items = [chapter for chapter in ordered if chapter.kind == kind and chapter.number in numbers]
        groups.append({"title": title, "chapters": [
            {"file": chapter.file, "title": re.sub(r"^Раздел\s+", "", chapter.title), "headings": chapter.headings}
            for chapter in items]})
    return {"groups": groups}


def build_manual(output_dir: Path = OUTPUT_DIR) -> bool:
    sources = sorted((SOURCE_DIR / "src").glob("*.md")) + [SOURCE_DIR / "GLOSSARY.md"]
    if not all(path.is_file() for path in sources) or not (SOURCE_DIR / "src").is_dir():
        print("Исходников руководства (docs/manual) нет, готовое руководство в manual/ не пересобиралось")
        return (output_dir / "contents.json").is_file()

    chapters = [read_chapter(path) for path in sources]
    for chapter in chapters:
        render_markdown(chapter)
    by_key = {(chapter.kind, chapter.number): chapter for chapter in chapters}
    grouped = [chapter for _, kind, numbers in GROUPS for number in numbers
               if (chapter := by_key.get((kind, number)))]
    if len(grouped) != len(chapters):
        print("Не все файлы руководства попали в GROUPS:",
              ", ".join(chapter.file for chapter in chapters if chapter not in grouped))
        return False

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    warnings: list[str] = []
    for chapter in grouped:
        for link in copy_images(chapter, output_dir):
            warnings.append(f"{chapter.file}: не найден рисунок {link}")
        link_references(chapter, by_key, warnings)
        if chapter.kind == "appendix" and chapter.number == 1:
            link_glossary(chapter)
        page = PAGE.format(title=html.escape(chapter.title), css=CSS, body=adapt_for_qt(chapter.body))
        (output_dir / chapter.file).write_text(page, encoding="utf-8")

    (output_dir / "contents.json").write_text(
        json.dumps(make_contents(grouped), ensure_ascii=False, indent=1), encoding="utf-8")
    for warning in warnings:
        print("  !", warning)
    print(f"Руководство собрано: {len(grouped)} разделов -> {output_dir}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка руководства для показа в программе (docs/manual -> manual)")
    parser.parse_args()
    if not build_manual():
        sys.exit(1)


if __name__ == "__main__":
    main()
