import os
import subprocess
import sys

from base.paths import logs_dir, update_dir

APP_BUNDLE = "Платежный календарь.app"

UPDATE_SCRIPT = """#!/bin/bash
PID="$1"
APP="$2"
NEW="$3"
UPDATE_DIR="$4"
LOG="$5"
STAGE="$APP.new"
OLD="$APP.old"

exec >>"$LOG" 2>&1
echo "$(date '+%F %T') Обновление: pid=$PID, app=$APP, new=$NEW"

fail() {
    echo "$(date '+%F %T') $1"
    rm -rf "$STAGE"
    osascript -e 'display alert "Платежный календарь" message "Не удалось установить обновление. Запущена прежняя версия."'
    open "$APP"
    exit 1
}

for i in $(seq 1 120); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.5
done
kill -0 "$PID" 2>/dev/null && fail "Программа не завершилась за отведённое время"

rm -rf "$STAGE" "$OLD"
ditto "$NEW" "$STAGE" || fail "Не удалось скопировать новую версию"
mv "$APP" "$OLD" || fail "Не удалось убрать старую версию"
if ! mv "$STAGE" "$APP"; then
    mv "$OLD" "$APP"
    fail "Не удалось поставить новую версию, старая восстановлена"
fi

echo "$(date '+%F %T') Файлы заменены, запуск новой версии"
open "$APP"
rm -rf "$OLD" "$UPDATE_DIR"
"""


def current_bundle() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.executable))))


def install_location_problem() -> str:
    bundle = current_bundle()
    if not bundle.endswith(".app"):
        return "Обновление поддерживается только для приложения в формате .app."
    if "/AppTranslocation/" in bundle:
        return ("macOS запустила программу из временного расположения. Перенесите «Платежный календарь» "
                "в папку «Программы», запустите её оттуда и повторите обновление.")
    folder = os.path.dirname(bundle)
    if not os.access(folder, os.W_OK):
        return (f"Нет прав на запись в папку {folder}. Перенесите программу в папку «Программы» "
                f"или в другую папку, доступную для записи.")
    return ""


def launch_mac_updater(new_dir: str) -> None:
    script_path = os.path.join(update_dir(), "update.sh")
    with open(script_path, "w", encoding="utf-8", newline="\n") as script_file:
        script_file.write(UPDATE_SCRIPT)
    os.chmod(script_path, 0o755)
    log_path = os.path.join(logs_dir(), "updater.log")
    subprocess.Popen(["/bin/bash", script_path, str(os.getpid()), current_bundle(),
                      os.path.join(new_dir, APP_BUNDLE), update_dir(), log_path],
                     cwd="/", close_fds=True, start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
