import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_manual import build_manual

WORKFLOW = "macos.yml"
MAC_DIR = ROOT / "dist" / "release-mac"


def step(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess:
    print(">", " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=check, text=True, encoding="utf-8")


def output_of(*command: str) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(f"Команда {' '.join(command)} завершилась с ошибкой: {result.stderr.strip()}")
    return result.stdout.strip()


def check_pushed() -> str:
    branch = output_of("git", "rev-parse", "--abbrev-ref", "HEAD")
    if output_of("git", "status", "--porcelain", "--untracked-files=no"):
        sys.exit("Есть незакоммиченные изменения: GitHub Actions соберёт только то, что запушено")
    output_of("git", "fetch", "origin", branch)
    if output_of("git", "rev-parse", "HEAD") != output_of("git", "rev-parse", f"origin/{branch}"):
        sys.exit(f"Ветка {branch} не совпадает с origin/{branch}: сделайте git push")
    return branch


def build_mac(branch: str) -> None:
    started = time.time()
    run("gh", "workflow", "run", WORKFLOW, "--ref", branch)
    run_id = None
    for _ in range(30):
        time.sleep(5)
        runs = json.loads(output_of("gh", "run", "list", "--workflow", WORKFLOW, "--branch", branch,
                                    "--limit", "5", "--json", "databaseId,createdAt"))
        fresh = [item for item in runs if item["createdAt"] >= time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(started - 10))]
        if fresh:
            run_id = str(fresh[0]["databaseId"])
            break
    if run_id is None:
        sys.exit("Запуск workflow не появился в списке за 2.5 минуты")
    run("gh", "run", "watch", run_id, "--exit-status")
    shutil.rmtree(MAC_DIR, ignore_errors=True)
    run("gh", "run", "download", run_id, "--dir", str(MAC_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="Тесты, руководство и сборка релизов для Windows и macOS")
    parser.add_argument("--notes", default="", help="Текст «Что нового» для version*.json")
    parser.add_argument("--skip-tests", action="store_true", help="Не запускать тесты")
    parser.add_argument("--skip-mac", action="store_true", help="Не собирать macOS через GitHub Actions")
    args = parser.parse_args()

    mac_branch = None
    if not args.skip_mac:
        if shutil.which("gh") is None:
            sys.exit("Не найден gh (GitHub CLI). Установите его и выполните gh auth login, либо запустите с --skip-mac")
        step("Проверка репозитория для сборки macOS")
        mac_branch = check_pushed()

    if not args.skip_tests:
        step("Тесты")
        run(sys.executable, "-m", "pytest")

    step("Руководство")
    if not build_manual():
        sys.exit("Нет руководства в manual/ и нет исходников в docs/manual, из которых его можно собрать")

    step("Сборка для Windows")
    run(sys.executable, "tools/build_release.py", "--notes", args.notes)

    if mac_branch is not None:
        step("Сборка для macOS (GitHub Actions)")
        build_mac(mac_branch)

    step("Готово")
    print(f"Windows: {ROOT / 'dist' / 'release'}")
    if mac_branch is not None:
        print(f"macOS:   {MAC_DIR}")


if __name__ == "__main__":
    main()
