import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from base.httpclient import HttpClient, HttpResponse
from base.sync import NetworkError

API_HOST = "cloud-api.yandex.net"
DOWNLOAD_HOST = "download.fake"
UPLOAD_HOST = "upload.fake"


def json_response(status: int, data: dict) -> HttpResponse:
    return HttpResponse(status, json.dumps(data).encode("utf-8"))


class FakeDisk(HttpClient):
    def __init__(self, token: str = "good-token"):
        self.token: str = token
        self.files: dict[str, bytes] = {}
        self.folders: set[str] = set()
        self.requests: list[tuple[str, str]] = []
        self.async_operations: bool = False
        self.pending_uploads: int = 0
        self.corrupt_uploads: bool = False
        self.network_down: bool = False
        self.operation_polls: int = 0
        self.metadata_polls: int = 0

    def pause(self, milliseconds: int) -> None:
        pass

    def send(self, method: str, url: str, headers: dict[str, str] | None = None, data: bytes = b"",
             upload_file: Path | None = None, download_file: Path | None = None) -> HttpResponse:
        if self.network_down:
            raise NetworkError("Нет связи с сервером: test")
        parsed = urlparse(url)
        params = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        self.requests.append((method, f"{parsed.netloc}{parsed.path}"))
        if parsed.netloc == UPLOAD_HOST:
            return self.store(params["path"], upload_file.read_bytes() if upload_file else data)
        if parsed.netloc == DOWNLOAD_HOST:
            return self.give(params["path"], download_file)
        if (headers or {}).get("Authorization") != f"OAuth {self.token}":
            return json_response(401, {"message": "Unauthorized", "error": "UnauthorizedError"})
        route = parsed.path.removeprefix("/v1/disk/")
        handler = {
            ("GET", "resources/download"): self.download_link,
            ("GET", "resources/upload"): self.upload_link,
            ("GET", "resources"): self.metadata,
            ("PUT", "resources"): self.create_folder,
            ("POST", "resources/move"): self.move,
            ("POST", "resources/copy"): self.copy,
            ("DELETE", "resources"): self.delete,
        }.get((method, route))
        if route.startswith("operations/"):
            return self.operation_status()
        if handler is None:
            return json_response(400, {"message": f"unknown route {method} {route}"})
        return handler(params)

    def download_link(self, params: dict) -> HttpResponse:
        if params["path"] not in self.files:
            return json_response(404, {"message": "not found", "error": "DiskNotFoundError"})
        return json_response(200, {"href": f"https://{DOWNLOAD_HOST}/file?{urlencode({'path': params['path']})}"})

    def upload_link(self, params: dict) -> HttpResponse:
        if params["path"] in self.files and params.get("overwrite") != "true":
            return json_response(409, {"message": "exists"})
        return json_response(200, {"href": f"https://{UPLOAD_HOST}/file?{urlencode({'path': params['path']})}"})

    def store(self, path: str, content: bytes) -> HttpResponse:
        self.files[path] = content + b"!" if self.corrupt_uploads else content
        if self.pending_uploads:
            return HttpResponse(202, b"")
        return HttpResponse(201, b"")

    def give(self, path: str, download_file: Path | None) -> HttpResponse:
        if path not in self.files:
            return HttpResponse(404, b"")
        if download_file is not None:
            download_file.write_bytes(self.files[path])
            return HttpResponse(200, b"")
        return HttpResponse(200, self.files[path])

    def metadata(self, params: dict) -> HttpResponse:
        path = params["path"]
        if path in self.files:
            if self.pending_uploads:
                self.metadata_polls += 1
                if self.metadata_polls <= self.pending_uploads:
                    return json_response(200, {"name": path.rsplit("/", 1)[-1]})
            content = self.files[path]
            return json_response(200, {"name": path.rsplit("/", 1)[-1], "size": len(content),
                                       "md5": hashlib.md5(content).hexdigest()})
        if path == "app:/" or path in self.folders:
            prefix = path if path.endswith("/") else path + "/"
            names = [name[len(prefix):] for name in self.files if name.startswith(prefix) and "/" not in name[len(prefix):]]
            return json_response(200, {"_embedded": {"items": [{"name": name} for name in names]}})
        return json_response(404, {"message": "not found", "error": "DiskNotFoundError"})

    def create_folder(self, params: dict) -> HttpResponse:
        if params["path"] in self.folders:
            return json_response(409, {"message": "exists"})
        self.folders.add(params["path"])
        return json_response(201, {"href": "x"})

    def move(self, params: dict) -> HttpResponse:
        return self.relocate(params, keep_source=False)

    def copy(self, params: dict) -> HttpResponse:
        return self.relocate(params, keep_source=True)

    def relocate(self, params: dict, keep_source: bool) -> HttpResponse:
        source, target = params["from"], params["path"]
        if source not in self.files:
            return json_response(404, {"message": "not found"})
        if target in self.files and params.get("overwrite") != "true":
            return json_response(409, {"message": "exists"})
        parent = target.rsplit("/", 1)[0]
        if not parent.endswith(":") and parent not in self.folders:
            return json_response(409, {"message": "parent missing", "error": "DiskPathDoesntExistsError"})
        self.files[target] = self.files[source] if keep_source else self.files.pop(source)
        if self.async_operations:
            return json_response(202, {"href": f"https://{API_HOST}/v1/disk/operations/op-1"})
        return json_response(201, {"href": "x"})

    def delete(self, params: dict) -> HttpResponse:
        if self.files.pop(params["path"], None) is None:
            return json_response(404, {"message": "not found"})
        return HttpResponse(204, b"")

    def operation_status(self) -> HttpResponse:
        self.operation_polls += 1
        return json_response(200, {"status": "in-progress" if self.operation_polls < 3 else "success"})
