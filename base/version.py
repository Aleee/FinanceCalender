import re

APP_VERSION: str = "2026.10.05"
DB_VERSION: int = 5

_NEW_VERSION_RE = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})$")
_OLD_VERSION_RE = re.compile(r"^(\d{2})\.(\d{4})-(\d{2})$")


def parse_version(text: str) -> tuple[int, int, int]:
    text = text.strip()
    if match := _NEW_VERSION_RE.match(text):
        year, month, build = (int(g) for g in match.groups())
    elif match := _OLD_VERSION_RE.match(text):
        month, year, build = (int(g) for g in match.groups())
    else:
        raise ValueError(f"Неверный формат версии: {text!r} (ожидается YYYY.MM.NN)")
    if not 1 <= month <= 12:
        raise ValueError(f"Неверный месяц в версии: {text!r}")
    return year, month, build


def is_newer(candidate: str, current: str = APP_VERSION) -> bool:
    return parse_version(candidate) > parse_version(current)
