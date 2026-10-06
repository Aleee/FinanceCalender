import argparse
import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

APP_EXE = "FinanceCalender.exe"
ITEMS = (APP_EXE, "_internal")
MOVE_ATTEMPTS = 10
MOVE_PAUSE = 1.0

SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x00000102

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

log = logging.getLogger("updater")
silent = False


class UpdateError(Exception):
    pass


def setup_logging(app_dir: Path) -> None:
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    try:
        logs_dir = app_dir / "data" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(logs_dir / "updater.log", encoding="utf-8")
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.addHandler(handler)


def wait_for_process(pid: int, timeout: float) -> bool:
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        log.info(f"Процесс {pid} уже завершён (или недоступен)")
        return True
    try:
        return kernel32.WaitForSingleObject(handle, int(timeout * 1000)) != WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(handle)


def rename_with_retries(source: Path, target: Path) -> None:
    for attempt in range(1, MOVE_ATTEMPTS + 1):
        try:
            os.rename(source, target)
            return
        except OSError as e:
            log.warning(f"Не удалось переместить {source} -> {target} (попытка {attempt}/{MOVE_ATTEMPTS}): {e}")
            if attempt == MOVE_ATTEMPTS:
                raise
            time.sleep(MOVE_PAUSE)


def check_new_files(new_dir: Path) -> None:
    for name in ITEMS:
        if not (new_dir / name).exists():
            raise UpdateError(f"В {new_dir} нет {name}")
    if (new_dir / "data").exists():
        raise UpdateError(f"В {new_dir} есть папка data — обновление отменено")


def replace_files(app_dir: Path, new_dir: Path, old_dir: Path) -> None:
    moved_old: list[str] = []
    placed_new: list[str] = []
    try:
        for name in ITEMS:
            if (app_dir / name).exists():
                rename_with_retries(app_dir / name, old_dir / name)
                moved_old.append(name)
        for name in ITEMS:
            rename_with_retries(new_dir / name, app_dir / name)
            placed_new.append(name)
    except OSError:
        log.exception("Ошибка при замене файлов, выполняется откат")
        rollback(app_dir, new_dir, old_dir, moved_old, placed_new)
        raise


def rollback(app_dir: Path, new_dir: Path, old_dir: Path, moved_old: list[str], placed_new: list[str]) -> None:
    try:
        for name in reversed(placed_new):
            os.rename(app_dir / name, new_dir / name)
        for name in reversed(moved_old):
            os.rename(old_dir / name, app_dir / name)
    except OSError:
        log.critical(f"Откат не удался. Старые файлы программы лежат в {old_dir}, их нужно вернуть в {app_dir} вручную",
                     exc_info=True)
        raise UpdateError("Откат не удался")
    log.info("Откат выполнен, старая версия восстановлена")


def start_app(app_dir: Path) -> None:
    exe_path = app_dir / APP_EXE
    try:
        process = subprocess.Popen([str(exe_path)], cwd=str(app_dir), close_fds=True,
                                   creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        log.info(f"Программа запущена, pid {process.pid}")
    except OSError:
        log.exception(f"Не удалось запустить {exe_path}")


def clean_up(new_dir: Path, old_dir: Path) -> None:
    for folder in (new_dir, old_dir):
        shutil.rmtree(folder, ignore_errors=True)
        if folder.exists():
            log.warning(f"Не удалось полностью удалить {folder}")
    for archive in new_dir.parent.glob("*.zip"):
        try:
            archive.unlink()
        except OSError:
            log.warning(f"Не удалось удалить {archive}")


def show_error(text: str) -> None:
    if silent:
        return
    try:
        ctypes.windll.user32.MessageBoxW(None, text, "Платежный календарь", 0x10)
    except Exception:
        pass


def run_update(pid: int, app_dir: Path, new_dir: Path, wait_timeout: float) -> int:
    old_dir = new_dir.parent / "old"
    log.info(f"Обновление: pid={pid}, app_dir={app_dir}, new_dir={new_dir}")

    if not wait_for_process(pid, wait_timeout):
        log.error("Программа не завершилась за отведённое время, обновление отменено")
        show_error("Не удалось обновить программу: она не закрылась. Закройте её и повторите обновление.")
        return 2

    try:
        check_new_files(new_dir)
        shutil.rmtree(old_dir, ignore_errors=True)
        old_dir.mkdir(parents=True)
    except (UpdateError, OSError) as e:
        log.error(f"Обновление отменено до замены файлов: {e}")
        start_app(app_dir)
        show_error("Не удалось подготовить обновление. Запущена прежняя версия.\nПодробности: data\\logs\\updater.log")
        return 2

    try:
        replace_files(app_dir, new_dir, old_dir)
    except (UpdateError, OSError):
        start_app(app_dir)
        show_error("Не удалось установить обновление. Запущена прежняя версия.\nПодробности: data\\logs\\updater.log")
        return 1

    log.info("Файлы заменены, запуск новой версии")
    start_app(app_dir)
    clean_up(new_dir, old_dir)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--new-dir", required=True)
    parser.add_argument("--wait-timeout", type=float, default=60)
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args()

    global silent
    silent = args.silent
    app_dir = Path(args.app_dir).resolve()
    new_dir = Path(args.new_dir).resolve()
    setup_logging(app_dir)
    try:
        return run_update(args.pid, app_dir, new_dir, args.wait_timeout)
    except Exception:
        log.exception("Непредвиденная ошибка апдейтера")
        return 3


if __name__ == "__main__":
    sys.exit(main())
