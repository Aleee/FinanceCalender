import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_manual import build_manual
from base.version import APP_VERSION, DB_VERSION, parse_version

APP_NAME = "FinanceCalender"
VIEWER_NAME = "FinanceCalenderViewer"
UPDATER_SOURCE = ROOT / "updater" / "updater.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
RELEASE_DIR = DIST / "release"


def run_pyinstaller(*args: str) -> None:
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", *args]
    print(">", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def build_app(app_name: str, spec: str) -> Path:
    run_pyinstaller("--distpath", str(DIST), "--workpath", str(BUILD / app_name), spec)
    app_folder = DIST / app_name
    if not (app_folder / f"{app_name}.exe").is_file() or not (app_folder / "_internal").is_dir():
        sys.exit(f"Сборка не дала {app_name}.exe и _internal в {app_folder}")
    return app_folder


def build_updater() -> Path:
    if not UPDATER_SOURCE.is_file():
        sys.exit(f"Не найден исходник апдейтера: {UPDATER_SOURCE}")
    updater_dist = DIST / "updater"
    run_pyinstaller("--onefile", "--noconsole", "--name", "updater",
                    "--icon", str(ROOT / "designer" / "icons" / "updater.ico"),
                    "--distpath", str(updater_dist), "--workpath", str(BUILD / "updater"),
                    "--specpath", str(BUILD / "updater"), str(UPDATER_SOURCE))
    return updater_dist / "updater.exe"


def make_zip(zip_path: Path, app_folder: Path, updater_exe: Path | None) -> None:
    if (app_folder / "data").exists():
        sys.exit(f"В {app_folder} есть папка data — в релиз она попасть не должна. Удалите её и повторите сборку")
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app_folder.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(app_folder).as_posix())
        if updater_exe is not None:
            archive.write(updater_exe, "updater.exe")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка релиза Платежного календаря")
    parser.add_argument("--notes", default="", help="Текст «Что нового» для version.json")
    parser.add_argument("--no-updater", action="store_true", help="Не собирать updater.exe (только для проверки сборки)")
    parser.add_argument("--viewer", action="store_true", help="Собрать версию для просмотра (FinanceCalenderViewer)")
    args = parser.parse_args()

    app_name = VIEWER_NAME if args.viewer else APP_NAME
    parse_version(APP_VERSION)
    if not args.viewer and not build_manual():
        sys.exit("Нет руководства в manual/ и нет исходников в docs/manual, из которых его можно собрать")
    print(f"Версия: {APP_VERSION}")

    app_folder = build_app(app_name, "viewer.spec" if args.viewer else "main.spec")
    updater_exe = None if args.no_updater else build_updater()
    if updater_exe is None:
        print("ВНИМАНИЕ: updater.exe не включён в архив — такой релиз выкладывать нельзя")

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    zip_name = f"{app_name}-{APP_VERSION}.zip"
    zip_path = RELEASE_DIR / zip_name
    make_zip(zip_path, app_folder, updater_exe)

    version_info = {
        "version": APP_VERSION,
        "db_version": DB_VERSION,
        "file": zip_name,
        "sha256": sha256_of(zip_path),
        "notes": args.notes,
    }
    version_path = RELEASE_DIR / ("version-viewer.json" if args.viewer else "version.json")
    version_path.write_text(json.dumps(version_info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Готово. Загрузите на Яндекс.Диск два файла из {RELEASE_DIR}:")
    print(f"  {zip_name} ({zip_path.stat().st_size / 1024 / 1024:.1f} МБ)")
    print(f"  {version_path.name}")


if __name__ == "__main__":
    main()
