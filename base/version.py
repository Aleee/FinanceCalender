import re

APP_VERSION: str = "10.2026-01"
DB_VERSION: int = 2

_VERSION_RE = re.compile(r"^(\d{2})\.(\d{4})-(\d{2})$")


def parse_version(text: str) -> tuple[int, int, int]:
    match = _VERSION_RE.match(text.strip())
    if match is None:
        raise ValueError(f"Неверный формат версии: {text!r} (ожидается MM.YYYY-NN)")
    month, year, build = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if not 1 <= month <= 12:
        raise ValueError(f"Неверный месяц в версии: {text!r}")
    return year, month, build


def is_newer(candidate: str, current: str = APP_VERSION) -> bool:
    return parse_version(candidate) > parse_version(current)
