import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

ERROR_MORE_DATA = 234
RM_SESSION_KEY_LENGTH = 33
RM_APP_NAME_LENGTH = 256
RM_SERVICE_NAME_LENGTH = 64


class RmUniqueProcess(ctypes.Structure):
    _fields_ = [("dwProcessId", wintypes.DWORD),
                ("ProcessStartTime", wintypes.FILETIME)]


class RmProcessInfo(ctypes.Structure):
    _fields_ = [("Process", RmUniqueProcess),
                ("strAppName", wintypes.WCHAR * RM_APP_NAME_LENGTH),
                ("strServiceShortName", wintypes.WCHAR * RM_SERVICE_NAME_LENGTH),
                ("ApplicationType", wintypes.DWORD),
                ("AppStatus", wintypes.ULONG),
                ("TSSessionId", wintypes.DWORD),
                ("bRestartable", wintypes.BOOL)]


def check_rm_result(result: int) -> None:
    if result != 0:
        raise OSError(f"код Restart Manager {result}")


def windows_lock_holders(path: str) -> list[str]:
    rstrtmgr = ctypes.WinDLL("rstrtmgr")
    session = wintypes.DWORD()
    session_key = ctypes.create_unicode_buffer(RM_SESSION_KEY_LENGTH)
    check_rm_result(rstrtmgr.RmStartSession(ctypes.byref(session), 0, session_key))
    try:
        files = (wintypes.LPCWSTR * 1)(path)
        check_rm_result(rstrtmgr.RmRegisterResources(session, 1, files, 0, None, 0, None))
        needed = wintypes.UINT(0)
        count = wintypes.UINT(0)
        reasons = wintypes.DWORD(0)
        result = rstrtmgr.RmGetList(session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons))
        if result != ERROR_MORE_DATA:
            check_rm_result(result)
            return []
        processes = (RmProcessInfo * needed.value)()
        count = wintypes.UINT(needed.value)
        check_rm_result(rstrtmgr.RmGetList(session, ctypes.byref(needed), ctypes.byref(count), processes, ctypes.byref(reasons)))
        return [f"{item.strAppName} (PID {item.Process.dwProcessId}"
                f"{', наш процесс' if item.Process.dwProcessId == os.getpid() else ''})" for item in processes[:count.value]]
    finally:
        rstrtmgr.RmEndSession(session)


def lock_holders(path: Path) -> str:
    if sys.platform != "win32":
        return "не определяются на этой системе"
    try:
        return ", ".join(windows_lock_holders(str(path))) or "не найдены"
    except Exception as e:
        return f"не удалось определить ({e})"
