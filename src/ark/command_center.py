"""Serve the next UI with the unchanged Local UI conversation API on loopback."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlsplit

from .ui.server import Handler, LocalServer
from .ui.session import LocalSession, SessionError, load_runtime

_ASSET_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
_MAX_ASSET_BYTES = 8 * 1024 * 1024
_MAX_BUNDLE_BYTES = 32 * 1024 * 1024


def load_assets(directory: Path) -> MappingProxyType:
    """Snapshot only built presentation assets; never serve a filesystem tree."""
    directory = directory.absolute()
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("UI build not found. Run npm ci and npm run build in frontend first.")
    if any(parent.is_symlink() for parent in directory.parents):
        raise ValueError("UI build directory must not contain symbolic-link ancestors.")
    index = directory / "index.html"
    if index.is_symlink() or not index.is_file():
        raise ValueError("UI index.html not found. Build frontend before starting.")
    if index.stat().st_size > _MAX_ASSET_BYTES:
        raise ValueError("UI index.html exceeds the asset size limit.")
    index_bytes = index.read_bytes()
    assets = {
        "/": (index_bytes, "text/html; charset=utf-8"),
        "/index.html": (index_bytes, "text/html; charset=utf-8"),
    }
    total = len(index_bytes)
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("UI build must not contain symbolic links.")
        relative = path.relative_to(directory)
        # Vite emits chunks under assets/. Only explicitly public image/font
        # extensions are allowed at the root. Maps, HTML, source and data stay private.
        if not path.is_file() or path.suffix not in _ASSET_TYPES:
            continue
        if len(relative.parts) > 1 and relative.parts[0] != "assets":
            continue
        if path.stat().st_size > _MAX_ASSET_BYTES:
            raise ValueError("UI asset exceeds the asset size limit.")
        content = path.read_bytes()
        total += len(content)
        if total > _MAX_BUNDLE_BYTES:
            raise ValueError("UI build exceeds the bundle size limit.")
        assets["/" + relative.as_posix()] = (content, _ASSET_TYPES[path.suffix])
    return MappingProxyType(assets)


class CommandCenterHandler(Handler):
    """Replace presentation GETs while inheriting all frozen API write checks."""

    server: CommandCenterServer

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/api/status":
            super().do_GET()
            return
        try:
            self._check_origin()
            asset = self.server.ui_assets.get(urlsplit(self.path).path)
            if asset is None:
                raise SessionError(404, "Not found.")
            self._send(200, *asset)
        except SessionError as exc:
            self._json(exc.status, {"error": str(exc)})


class CommandCenterServer(LocalServer):
    """The existing single-session API; no additional backend capabilities."""

    def __init__(self, session: LocalSession, directory: Path, port: int = 8766):
        # Validate and capture all assets before opening a listener.
        self.ui_assets = load_assets(directory)
        super().__init__(session, port)
        self.RequestHandlerClass = CommandCenterHandler


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ARK Command Center — next UI, loopback only, existing V2 conversation API"
    )
    parser.add_argument("--config", help="existing ARK TOML configuration")
    parser.add_argument("--mock", action="store_true",
                        help="explicit Echo demo; no model inference")
    parser.add_argument("--dist", type=Path, default=Path("frontend/dist"),
                        help="built UI directory (default: frontend/dist from working directory)")
    parser.add_argument("--port", type=int, default=8766, help="loopback port (default: 8766)")
    args = parser.parse_args(argv)
    if args.mock and args.config:
        parser.error("--mock cannot be combined with --config")
    if not args.mock and not args.config:
        parser.error("--config is required for local inference; use --mock only for UI tests")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    session = LocalSession(partial(load_runtime, args.config, mock=args.mock))
    try:
        server = CommandCenterServer(session, args.dist, args.port)
    except (OSError, ValueError) as exc:
        print(f"ARK Command Center startup error: {exc}", flush=True)
        return 1
    with server:
        print(f"ARK Command Center ready\n{server.origin}", flush=True)
        print("Model loading; see the browser. Ctrl+C stops the server.", flush=True)
        session.start()
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print("\nARK Command Center stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
