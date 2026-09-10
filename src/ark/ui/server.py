"""Loopback-only, dependency-free HTTP presentation layer for ARK V2."""

from __future__ import annotations

import argparse
import json
import secrets
from collections.abc import Sequence
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlsplit

from .session import LocalSession, SessionError, load_runtime

HOST = "127.0.0.1"
MAX_BODY_BYTES = 65536
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/mark.svg": ("mark.svg", "image/svg+xml"),
}


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    # A second Windows process must not share an already bound listening port.
    allow_reuse_address = False

    def __init__(self, session: LocalSession, port: int = 8765):
        self.session = session
        self.token = secrets.token_urlsafe(32)
        super().__init__((HOST, port), Handler)
        self.authority = f"{HOST}:{self.server_port}"
        self.origin = f"http://{self.authority}"

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address


class Handler(BaseHTTPRequestHandler):
    server: LocalServer
    server_version = "ARKLocalUI"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        # Do not echo URL/query/user-controlled request data to the terminal.
        pass

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; "
                         "style-src 'self'; connect-src 'self'; img-src 'self'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # A closed tab does not cancel or duplicate an accepted generation.

    def _json(self, status: int, payload: dict[str, object]) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def send_error(self, code, message=None, explain=None):
        self._json(code, {"error": HTTPStatus(code).phrase})

    def _check_origin(self, *, write: bool = False) -> None:
        if self.headers.get_all("Host") != [self.server.authority]:
            raise SessionError(403, "Use the printed 127.0.0.1 URL.")
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            raise SessionError(403, "Cross-origin requests are not allowed.")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise SessionError(403, "Cross-site requests are not allowed.")
        if write:
            if origin != self.server.origin:
                raise SessionError(403, "A same-origin browser request is required.")
            token = self.headers.get("X-ARK-Token", "")
            if not token.isascii() or not secrets.compare_digest(token, self.server.token):
                raise SessionError(403, "Reload the page before sending a request.")

    def do_GET(self) -> None:
        try:
            self._check_origin()
            path = urlsplit(self.path).path
            if path == "/api/status":
                self._json(200, {**self.server.session.snapshot(), "token": self.server.token})
            elif path in ASSETS:
                name, mime = ASSETS[path]
                self._send(200, files("ark.ui").joinpath("static", name).read_bytes(), mime)
            else:
                raise SessionError(404, "Not found.")
        except SessionError as exc:
            self._json(exc.status, {"error": str(exc)})

    def do_POST(self) -> None:
        try:
            self._check_origin(write=True)
            if self.path not in ("/api/chat", "/api/reset"):
                raise SessionError(404, "Not found.")
            if self.headers.get_content_type() != "application/json":
                raise SessionError(415, "Use application/json.")
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
                raise SessionError(400, "A single Content-Length is required.")
            if len(lengths[0]) > 6:
                raise SessionError(413, "Request body is too large.")
            length = int(lengths[0])
            if not 0 < length <= MAX_BODY_BYTES or self.headers.get("Transfer-Encoding"):
                raise SessionError(413, "Request body is too large or unsupported.")
            data = self.rfile.read(length)
            if len(data) != length:
                raise SessionError(400, "Incomplete request.")
            try:
                payload = json.loads(data)
            except (ValueError, UnicodeError, RecursionError) as exc:
                raise SessionError(400, "Invalid JSON.") from exc
            fields = {"message", "revision"} if self.path == "/api/chat" else {"revision"}
            if not isinstance(payload, dict) or set(payload) != fields:
                raise SessionError(400, "Unexpected request fields.")
            if self.path == "/api/chat":
                self.server.session.chat(payload["message"], payload["revision"])
                self._json(202, {"accepted": True})
            else:
                self.server.session.reset(payload["revision"])
                self._json(200, {"reset": True})
        except SessionError as exc:
            self._json(exc.status, {"error": str(exc)})
        except TimeoutError:
            self._json(408, {"error": "Request timed out."})


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ARK Local UI — loopback only, V2 Intelligence")
    parser.add_argument("--config", help="existing ARK TOML configuration")
    parser.add_argument("--mock", action="store_true",
                        help="explicit echo demo; no model inference")
    parser.add_argument("--port", type=int, default=8765, help="loopback port (default: 8765)")
    args = parser.parse_args(argv)
    if args.mock and args.config:
        parser.error("--mock cannot be combined with --config")
    if not args.mock and not args.config:
        parser.error("--config is required for local model inference; use --mock only for UI tests")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    session = LocalSession(partial(load_runtime, args.config, mock=args.mock))
    try:
        server = LocalServer(session, args.port)
    except OSError as exc:
        print(f"ARK Local UI startup error: {exc}. Try --port 8766.", flush=True)
        return 1
    with server:
        print(f"ARK Local UI ready\n{server.origin}", flush=True)
        print("Model loading; see the browser for status. Ctrl+C stops the server.", flush=True)
        session.start()
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print("\nARK Local UI stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
