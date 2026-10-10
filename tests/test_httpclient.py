import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from base.httpclient import QtHttpClient
from base.sync import NetworkError

FILE_CONTENT = bytes(range(256)) * 1000


class Handler(BaseHTTPRequestHandler):
    received: list[tuple[str, str, dict, bytes]] = []

    def log_message(self, format, *args):
        pass

    def read_body(self) -> bytes:
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def answer(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_any(self) -> None:
        body = self.read_body()
        self.received.append((self.command, self.path, dict(self.headers), body))
        if self.path.startswith("/file"):
            self.answer(200, FILE_CONTENT)
        elif self.path.startswith("/missing"):
            self.answer(404, b'{"message": "not found"}')
        elif self.path.startswith("/upload"):
            self.answer(201, b"")
        else:
            self.answer(200, b'{"ok": true}')

    do_GET = do_PUT = do_POST = do_DELETE = handle_any


@pytest.fixture
def server():
    Handler.received = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def client(qapp) -> QtHttpClient:
    return QtHttpClient()


def test_get_returns_status_and_body(client, server):
    response = client.send("GET", f"{server}/json?path=app%3A%2F", {"Authorization": "OAuth abc"})
    assert (response.status, response.body) == (200, b'{"ok": true}')
    method, path, headers, _ = Handler.received[-1]
    assert (method, path) == ("GET", "/json?path=app%3A%2F")
    assert headers["Authorization"] == "OAuth abc"


def test_error_status_is_returned_not_raised(client, server):
    response = client.send("GET", f"{server}/missing")
    assert (response.status, response.body) == (404, b'{"message": "not found"}')


def test_post_and_delete_use_requested_verbs(client, server):
    client.send("POST", f"{server}/json")
    client.send("DELETE", f"{server}/json")
    assert [item[0] for item in Handler.received] == ["POST", "DELETE"]


def test_put_sends_file_content(client, server, tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(FILE_CONTENT)
    response = client.send("PUT", f"{server}/upload", upload_file=source)
    assert response.status == 201
    assert Handler.received[-1][3] == FILE_CONTENT


def test_put_sends_bytes(client, server):
    client.send("PUT", f"{server}/upload", data=b"hello")
    assert Handler.received[-1][3] == b"hello"


def test_download_goes_to_file(client, server, tmp_path):
    target = tmp_path / "downloaded.bin"
    response = client.send("GET", f"{server}/file", download_file=target)
    assert response.status == 200
    assert target.read_bytes() == FILE_CONTENT


def test_error_body_is_not_written_to_download_file(client, server, tmp_path):
    target = tmp_path / "downloaded.bin"
    response = client.send("GET", f"{server}/missing", download_file=target)
    assert response.status == 404
    assert not target.exists()
    assert response.body == b'{"message": "not found"}'


def test_unreachable_server_raises_network_error(client):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with pytest.raises(NetworkError):
        client.send("GET", f"http://127.0.0.1:{port}/json")


def test_pause_returns(client):
    client.pause(10)
