import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import lovely_logger as log

from base.httpclient import HttpClient, HttpResponse
from base.sync import (AuthError, MASTER_BACKUPS_DIR, MASTER_DB_NAME, MASTER_INFO_NAME,
                       MasterInfo, SyncChannel, SyncError, TEMP_SUFFIX, backup_time_from_name, file_md5, master_backup_name)

API_URL = "https://cloud-api.yandex.net/v1/disk"
DEFAULT_DISK_FOLDER = "app:/"
UPLOAD_CONFIRM_ATTEMPTS = 10
UPLOAD_CONFIRM_PAUSE_MS = 1000
OPERATION_ATTEMPTS = 60
OPERATION_PAUSE_MS = 500
BACKUPS_LIST_LIMIT = 1000
UNAUTHORIZED_RETRIES = 2
UNAUTHORIZED_RETRY_PAUSE_MS = 500


class YandexDiskApiChannel(SyncChannel):
    def __init__(self, token: str, http: HttpClient, folder: str = DEFAULT_DISK_FOLDER):
        self.token: str = token.strip()
        self.http: HttpClient = http
        folder = folder.strip() or DEFAULT_DISK_FOLDER
        self.folder: str = folder if folder.endswith("/") else folder + "/"
        self.cached_info: tuple[str, MasterInfo] | None = None

    def check_connection(self) -> None:
        response = self.api("GET", "resources", {"path": self.folder, "fields": "name,type"}, (200, 404))
        if response.status == 404:
            raise SyncError(f"Папка {self.folder} не найдена на Яндекс.Диске")

    def read_master_info(self) -> MasterInfo | None:
        if self.cached_info is not None:
            metadata = self.metadata(MASTER_INFO_NAME)
            if metadata is None:
                return None
            if metadata.get("md5") == self.cached_info[0]:
                return replace(self.cached_info[1])
        href = self.link("resources/download", {"path": self.remote_path(MASTER_INFO_NAME)})
        if href is None:
            return None
        response = self.http.send("GET", href, self.auth_headers())
        if response.status != 200:
            raise self.error_from(response)
        info = MasterInfo.from_json(response.body.decode("utf-8"))
        self.cached_info = (hashlib.md5(response.body).hexdigest(), info)
        return replace(info)

    def download_master(self, destination: Path) -> None:
        href = self.link("resources/download", {"path": self.remote_path(MASTER_DB_NAME)})
        if href is None:
            raise SyncError("Файл мастера не найден на Яндекс.Диске")
        response = self.http.send("GET", href, self.auth_headers(), download_file=destination)
        if response.status != 200:
            raise self.error_from(response)
        metadata = self.metadata(MASTER_DB_NAME)
        if metadata is None:
            raise SyncError("Файл мастера исчез с Яндекс.Диска во время скачивания")
        if metadata.get("md5") and file_md5(destination) != metadata["md5"]:
            raise SyncError("Скачанный файл мастера не совпадает с файлом на Яндекс.Диске")

    def upload_master(self, source: Path, info: MasterInfo) -> None:
        temp_db = self.remote_path(MASTER_DB_NAME + TEMP_SUFFIX)
        self.ensure_folder_chain(self.folder)
        info_bytes = info.to_json().encode("utf-8")
        try:
            self.put_file(temp_db, file_md5(source), source.stat().st_size, upload_file=source)
            self.move(temp_db, self.remote_path(MASTER_DB_NAME))
            self.put_file(self.remote_path(MASTER_INFO_NAME), hashlib.md5(info_bytes).hexdigest(), len(info_bytes),
                          data=info_bytes)
        except SyncError:
            self.delete_quietly(temp_db)
            raise
        self.cached_info = (hashlib.md5(info_bytes).hexdigest(), replace(info))

    def backup_master(self) -> None:
        if self.metadata(MASTER_DB_NAME) is None:
            return
        backups_folder = self.remote_path(MASTER_BACKUPS_DIR)
        copy_params = {"from": self.remote_path(MASTER_DB_NAME), "path": f"{backups_folder}/{master_backup_name()}",
                       "overwrite": "true"}
        response = self.api("POST", "resources/copy", copy_params, (201, 202, 409))
        if response.status == 409:
            self.ensure_folder_chain(backups_folder)
            response = self.api("POST", "resources/copy", copy_params, (201, 202))
        self.wait_operation(response)

    def remove_old_backups(self, keep_days: int) -> None:
        response = self.api("GET", "resources", {"path": self.remote_path(MASTER_BACKUPS_DIR), "limit": BACKUPS_LIST_LIMIT,
                                                 "fields": "_embedded.items.name"}, (200, 404))
        if response.status == 404:
            return
        minimum_time = datetime.now() - timedelta(days=keep_days)
        for item in self.parse_json(response).get("_embedded", {}).get("items", []):
            backup_time = backup_time_from_name(str(item.get("name", "")))
            if backup_time is not None and backup_time < minimum_time:
                self.api("DELETE", "resources", {"path": self.remote_path(f"{MASTER_BACKUPS_DIR}/{item['name']}"),
                                                 "permanently": "true"}, (202, 204, 404))

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"OAuth {self.token}"}

    def remote_path(self, name: str) -> str:
        return self.folder + name

    def api(self, method: str, endpoint: str, params: dict, allowed: tuple[int, ...]) -> HttpResponse:
        url = f"{API_URL}/{endpoint}?{urlencode(params)}"
        response = self.http.send(method, url, self.auth_headers())
        for _ in range(UNAUTHORIZED_RETRIES):
            if response.status != 401 or method != "GET":
                break
            self.http.pause(UNAUTHORIZED_RETRY_PAUSE_MS)
            response = self.http.send(method, url, self.auth_headers())
        if response.status not in allowed:
            if response.status in (401, 403):
                log.w(f"Отказ в доступе {response.status}: {method} {endpoint}, "
                      f"ответ: {response.body[:300].decode('utf-8', 'replace')}")
            raise self.error_from(response)
        return response

    def link(self, endpoint: str, params: dict) -> str | None:
        response = self.api("GET", endpoint, params, (200, 404))
        if response.status == 404:
            return None
        return self.read_href(response)

    def metadata(self, name: str) -> dict | None:
        response = self.api("GET", "resources", {"path": self.remote_path(name), "fields": "name,size,md5"}, (200, 404))
        return None if response.status == 404 else self.parse_json(response)

    def put_file(self, remote_path: str, expected_md5: str, expected_size: int, data: bytes = b"",
                 upload_file: Path | None = None) -> None:
        name = remote_path[len(self.folder):]
        href = self.link("resources/upload", {"path": remote_path, "overwrite": "true"})
        if href is None:
            raise SyncError("Яндекс.Диск не выдал ссылку для загрузки")
        response = self.http.send("PUT", href, data=data, upload_file=upload_file)
        if response.status not in (201, 202):
            raise self.error_from(response)
        mismatch = False
        for _ in range(UPLOAD_CONFIRM_ATTEMPTS):
            metadata = self.metadata(name)
            if metadata is not None and metadata.get("md5"):
                if metadata["md5"] == expected_md5 and metadata.get("size") == expected_size:
                    return
                mismatch = True
            self.http.pause(UPLOAD_CONFIRM_PAUSE_MS)
        if mismatch:
            raise SyncError("Файл на Яндекс.Диске не совпадает с отправленным")
        raise SyncError("Не удалось подтвердить загрузку файла на Яндекс.Диск")

    def move(self, source_path: str, target_path: str) -> None:
        response = self.api("POST", "resources/move", {"from": source_path, "path": target_path, "overwrite": "true"}, (201, 202))
        self.wait_operation(response)

    def delete_quietly(self, remote_path: str) -> None:
        try:
            self.api("DELETE", "resources", {"path": remote_path, "permanently": "true"}, (202, 204, 404))
        except SyncError:
            pass

    def ensure_folder_chain(self, folder_path: str) -> None:
        root, separator, rest = folder_path.partition(":/")
        current = root + separator
        segments = [part for part in rest.split("/") if part]
        if len(segments) > 1 and self.api("GET", "resources", {"path": folder_path, "fields": "name"}, (200, 404)).status == 200:
            return
        for segment in segments:
            current += segment
            self.api("PUT", "resources", {"path": current}, (201, 409))
            current += "/"

    def wait_operation(self, response: HttpResponse) -> None:
        if response.status != 202:
            return
        href = self.read_href(response)
        for _ in range(OPERATION_ATTEMPTS):
            status_response = self.http.send("GET", href, self.auth_headers())
            if status_response.status != 200:
                raise self.error_from(status_response)
            status = self.parse_json(status_response).get("status")
            if status == "success":
                return
            if status == "failed":
                raise SyncError("Операция на Яндекс.Диске завершилась неудачей")
            self.http.pause(OPERATION_PAUSE_MS)
        raise SyncError("Операция на Яндекс.Диске не завершилась за отведённое время")

    @staticmethod
    def parse_json(response: HttpResponse) -> dict:
        try:
            data = json.loads(response.body.decode("utf-8"))
        except ValueError as e:
            raise SyncError(f"Яндекс.Диск вернул неожиданный ответ: {e}") from e
        if not isinstance(data, dict):
            raise SyncError("Яндекс.Диск вернул неожиданный ответ")
        return data

    @classmethod
    def read_href(cls, response: HttpResponse) -> str:
        href = cls.parse_json(response).get("href")
        if not isinstance(href, str) or not href:
            raise SyncError("Яндекс.Диск вернул ответ без ссылки")
        return href

    @staticmethod
    def error_from(response: HttpResponse) -> SyncError:
        details = ""
        try:
            data = json.loads(response.body.decode("utf-8"))
            details = str(data.get("description") or data.get("message") or "")
        except (ValueError, AttributeError):
            pass
        if response.status == 401:
            return AuthError("Токен недействителен или истёк")
        if response.status == 403:
            return AuthError("Нет доступа к Яндекс.Диску: проверьте токен и права приложения")
        if response.status == 507:
            return SyncError("На Яндекс.Диске недостаточно места")
        if response.status == 423:
            return SyncError("Ресурс на Яндекс.Диске заблокирован, повторите позже")
        return SyncError(f"Яндекс.Диск вернул ошибку {response.status}" + (f": {details}" if details else ""))
