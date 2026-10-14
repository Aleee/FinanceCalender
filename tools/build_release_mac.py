import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from base.macupdate import APP_BUNDLE
from base.version import APP_VERSION, DB_VERSION, parse_version

DIST = ROOT / "dist"
BUILD = ROOT / "build"
RELEASE_DIR = DIST / "release"


def build_app() -> Path:
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(DIST),
               "--workpath", str(BUILD / "app"), "main.spec"]
    print(">", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)
    app_path = DIST / APP_BUNDLE
    if not app_path.is_dir():
        sys.exit(f"Сборка не дала {APP_BUNDLE} в {DIST}")
    return app_path


def check_app(app_path: Path) -> None:
    if (app_path / "Contents" / "MacOS" / "data").exists():
        sys.exit(f"В {app_path} есть папка data — в релиз она попасть не должна. Удалите её и повторите сборку")
    result = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app_path)],
                            capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"Подпись пакета нарушена: {result.stderr.strip()}")


def make_zip(app_path: Path, zip_path: Path) -> None:
    zip_path.unlink(missing_ok=True)
    subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app_path), str(zip_path)],
                   check=True)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка релиза Платежного календаря для macOS")
    parser.add_argument("--notes", default="", help="Текст «Что нового» для version-mac-<архитектура>.json")
    args = parser.parse_args()

    if sys.platform != "darwin":
        sys.exit("Скрипт собирает релиз для macOS и запускается только на Mac")

    parse_version(APP_VERSION)
    arch = platform.machine()
    print(f"Версия: {APP_VERSION}, архитектура: {arch}")

    app_path = build_app()
    check_app(app_path)

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    zip_name = f"FinanceCalender-{APP_VERSION}-mac-{arch}.zip"
    zip_path = RELEASE_DIR / zip_name
    make_zip(app_path, zip_path)

    version_info = {
        "version": APP_VERSION,
        "db_version": DB_VERSION,
        "file": zip_name,
        "sha256": sha256_of(zip_path),
        "notes": args.notes,
    }
    version_name = f"version-mac-{arch}.json"
    (RELEASE_DIR / version_name).write_text(json.dumps(version_info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Готово. Загрузите на Яндекс.Диск два файла из {RELEASE_DIR}:")
    print(f"  {zip_name} ({zip_path.stat().st_size / 1024 / 1024:.1f} МБ)")
    print(f"  {version_name}")


if __name__ == "__main__":
    main()
