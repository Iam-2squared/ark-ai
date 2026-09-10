"""Safe daily launcher for the existing loopback-only Local UI."""

from __future__ import annotations

import argparse
import json
import webbrowser
from collections.abc import Callable, Sequence
from functools import partial
from http.client import HTTPConnection

from .ui.server import HOST, LocalServer
from .ui.session import LocalSession, load_runtime

DEFAULT_PORT = 8765
FALLBACK_PORT = 8766


def compatible_ui(port: int, *, timeout: float = 0.5) -> bool:
    """Return true only for the narrow status contract of an ARK V2 Local UI."""
    connection = HTTPConnection(HOST, port, timeout=timeout)
    try:
        connection.request("GET", "/api/status", headers={"Host": f"{HOST}:{port}"})
        response = connection.getresponse()
        body = response.read(131072)
        if (
            response.status != 200
            or not response.getheader("Server", "").startswith("ARKLocalUI")
            or "application/json" not in response.getheader("Content-Type", "")
        ):
            return False
        payload = json.loads(body)
        return (
            isinstance(payload, dict)
            and payload.get("intelligence") == "V2"
            and payload.get("state") in {"loading", "ready", "generating", "error"}
            and type(payload.get("revision")) is int
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    finally:
        connection.close()


def open_browser(url: str, opener: Callable[[str], bool] = webbrowser.open) -> None:
    try:
        opened = opener(url)
    except Exception as exc:  # Browser launch is optional; the server stays healthy.
        print(f"Browser did not open automatically: {exc}", flush=True)
        return
    if not opened:
        print(f"Browser did not open automatically. Open {url}", flush=True)


def launch(
    config: str,
    *,
    ports: tuple[int, ...] = (DEFAULT_PORT, FALLBACK_PORT),
    opener: Callable[[str], bool] = webbrowser.open,
    probe: Callable[[int], bool] = compatible_ui,
    server_factory: Callable[[LocalSession, int], LocalServer] = LocalServer,
) -> int:
    for port in ports:
        url = f"http://{HOST}:{port}"
        if probe(port):
            print(f"Reusing compatible ARK Local UI\n{url}", flush=True)
            open_browser(url, opener)
            return 0

        session = LocalSession(partial(load_runtime, config, mock=False))
        try:
            server = server_factory(session, port)
        except OSError:
            print(f"Port {port} is occupied by another service; not stopping it.", flush=True)
            continue

        with server:
            print(f"ARK Launcher ready\n{server.origin}", flush=True)
            print("Model loading in the existing Local UI. Ctrl+C stops ARK.", flush=True)
            session.start()
            open_browser(server.origin, opener)
            try:
                server.serve_forever(poll_interval=0.2)
            except KeyboardInterrupt:
                print("\nARK stopped.", flush=True)
        return 0

    print(
        f"ARK Launcher startup error: ports {', '.join(map(str, ports))} are unavailable.\n"
        "Stop the known application using a port, then retry. No process was killed.",
        flush=True,
    )
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Start or reuse the loopback-only ARK Local UI"
    )
    parser.add_argument("--config", default="config.toml", help="ARK TOML configuration")
    args = parser.parse_args(argv)
    try:
        return launch(args.config)
    except OSError as exc:
        print(f"ARK Launcher error: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
