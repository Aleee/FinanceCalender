import os
import sys


def app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    return os.path.join(app_dir(), "data")


def update_dir() -> str:
    return os.path.join(app_dir(), "_update")


def _data_subdir(name: str) -> str:
    path: str = os.path.join(data_dir(), name)
    os.makedirs(path, exist_ok=True)
    return path


def db_path() -> str:
    return os.path.join(_data_subdir("db"), "db.db")


def settings_path() -> str:
    return os.path.join(_data_subdir("config"), "settings.ini")


def logs_dir() -> str:
    return _data_subdir("logs")


def backup_dir() -> str:
    return _data_subdir("backup")


def export_dir() -> str:
    return _data_subdir("export")


def to_stored_path(path: str) -> str:
    if not path:
        return ""
    abs_path: str = os.path.abspath(path)
    try:
        rel_path: str = os.path.relpath(abs_path, app_dir())
    except ValueError:
        return abs_path
    if rel_path == ".." or rel_path.startswith(".." + os.sep):
        return abs_path
    return rel_path


def from_stored_path(value: str) -> str:
    if not value:
        return ""
    if os.path.isabs(value):
        return value
    return os.path.join(app_dir(), value)
