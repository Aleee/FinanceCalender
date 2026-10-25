import os
import shutil
import subprocess

import pytest

from base import macupdate
from base.macupdate import APP_BUNDLE, UPDATE_SCRIPT

GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
BASH = shutil.which("bash") if os.name != "nt" else (GIT_BASH if os.path.exists(GIT_BASH) else None)

pytestmark = pytest.mark.skipif(BASH is None, reason="нужен bash")


def write_tool(folder, name, body):
    path = folder / name
    path.write_text("#!/bin/bash\n" + body, encoding="utf-8", newline="\n")
    path.chmod(0o755)


@pytest.fixture
def stand(tmp_path):
    apps = tmp_path / "apps"
    app = apps / APP_BUNDLE
    new_app = tmp_path / "update" / "new" / APP_BUNDLE
    fake_bin = tmp_path / "bin"
    for folder in (app, new_app, fake_bin):
        folder.mkdir(parents=True)
    (app / "old.txt").write_text("old")
    (new_app / "new.txt").write_text("new")
    write_tool(fake_bin, "ditto", 'mkdir -p "$2" && cp -R "$1"/. "$2"/\n')
    write_tool(fake_bin, "open", f'echo "$1" >> "{(tmp_path / "opened.txt").as_posix()}"\n')
    write_tool(fake_bin, "osascript", f'echo alert >> "{(tmp_path / "alerts.txt").as_posix()}"\n')
    script = tmp_path / "update.sh"
    script.write_text(UPDATE_SCRIPT, encoding="utf-8", newline="\n")
    return tmp_path, app, new_app, fake_bin, script


def run_script(stand_values, pid="999999"):
    tmp_path, app, new_app, fake_bin, script = stand_values
    env = dict(os.environ, PATH=fake_bin.as_posix() + os.pathsep + os.environ["PATH"])
    return subprocess.run([BASH, script.as_posix(), pid, app.as_posix(), new_app.as_posix(),
                           (tmp_path / "update").as_posix(), (tmp_path / "updater.log").as_posix()],
                          env=env, capture_output=True, timeout=60)


def test_update_replaces_bundle(stand):
    tmp_path, app, *_ = stand
    result = run_script(stand)
    assert result.returncode == 0
    assert (app / "new.txt").exists() and not (app / "old.txt").exists()
    assert not (app.parent / (APP_BUNDLE + ".old")).exists()
    assert not (app.parent / (APP_BUNDLE + ".new")).exists()
    assert not (tmp_path / "update").exists()
    assert (tmp_path / "opened.txt").read_text(errors="replace").strip().endswith(".app")
    assert not (tmp_path / "alerts.txt").exists()


def test_failed_copy_keeps_old_version(stand):
    tmp_path, app, new_app, fake_bin, script = stand
    write_tool(fake_bin, "ditto", "exit 1\n")
    result = run_script(stand)
    assert result.returncode == 1
    assert (app / "old.txt").exists() and not (app / "new.txt").exists()
    assert not (app.parent / (APP_BUNDLE + ".new")).exists()
    assert (tmp_path / "alerts.txt").exists()
    assert (tmp_path / "opened.txt").read_text(errors="replace").strip().endswith(".app")
    assert new_app.exists()


def test_waits_for_running_process(stand, monkeypatch):
    tmp_path, app, *_ = stand
    if os.name == "nt":
        pytest.skip("pid Windows не виден из msys bash")
    process = subprocess.Popen([BASH, "-c", "sleep 2"])
    try:
        result = run_script(stand, str(process.pid))
    finally:
        process.kill()
        process.wait()
    assert result.returncode == 0
    assert (app / "new.txt").exists()


def test_install_location_problem_for_non_app(monkeypatch):
    monkeypatch.setattr(macupdate, "current_bundle", lambda: "/tmp/FinanceCalender")
    assert macupdate.install_location_problem()


def test_install_location_problem_for_translocation(monkeypatch):
    monkeypatch.setattr(macupdate, "current_bundle", lambda: "/private/var/AppTranslocation/X/d/App.app")
    assert "временного" in macupdate.install_location_problem()


def test_install_location_ok_in_writable_folder(monkeypatch, tmp_path):
    bundle = tmp_path / APP_BUNDLE
    bundle.mkdir()
    monkeypatch.setattr(macupdate, "current_bundle", lambda: str(bundle))
    assert macupdate.install_location_problem() == ""
