"""Launcher behavior without loading model weights or opening a real browser."""

from threading import Thread

from ark.launcher import FALLBACK_PORT, compatible_ui, launch, open_browser
from ark.ui.server import LocalServer
from ark.ui.session import LocalSession, load_runtime


class FakeServer:
    def __init__(self, session, port, *, occupied=()):
        if port in occupied:
            raise OSError("occupied")
        self.session = session
        self.port = port
        self.origin = f"http://127.0.0.1:{port}"
        self.served = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def serve_forever(self, poll_interval):
        self.served = True


def factory(occupied, made):
    def build(session, port):
        server = FakeServer(session, port, occupied=occupied)
        session.start = lambda: made.append(("start", port))
        made.append(("server", server))
        return server

    return build


def test_starts_default_loopback_then_browser():
    made, opened = [], []
    assert launch(
        "config.toml", opener=lambda url: opened.append(url) or True,
        probe=lambda port: False, server_factory=factory((), made)
    ) == 0
    assert opened == ["http://127.0.0.1:8765"]
    assert made[0][0] == "server" and made[0][1].served
    assert made[1] == ("start", 8765)


def test_reuses_compatible_server_without_duplicate():
    opened, made = [], []
    assert launch(
        "config.toml", opener=lambda url: opened.append(url) or True,
        probe=lambda port: port == 8765, server_factory=factory((), made)
    ) == 0
    assert opened == ["http://127.0.0.1:8765"] and made == []


def test_occupied_default_uses_fixed_fallback_without_killing():
    made, opened = [], []
    assert launch(
        "config.toml", opener=lambda url: opened.append(url) or True,
        probe=lambda port: False, server_factory=factory((8765,), made)
    ) == 0
    assert opened == [f"http://127.0.0.1:{FALLBACK_PORT}"]


def test_both_ports_occupied_fails_safely():
    assert launch(
        "config.toml", opener=lambda url: True, probe=lambda port: False,
        server_factory=factory((8765, 8766), [])
    ) == 1


def test_browser_failure_never_raises(capsys):
    open_browser("http://127.0.0.1:8765", lambda url: False)
    open_browser("http://127.0.0.1:8765", lambda url: (_ for _ in ()).throw(OSError("no app")))
    output = capsys.readouterr().out
    assert "Open http://127.0.0.1:8765" in output and "no app" in output


def test_compatibility_probe_accepts_actual_ark_status_only():
    session = LocalSession(lambda: load_runtime(None, mock=True))
    with LocalServer(session, port=0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            assert compatible_ui(server.server_port)
        finally:
            server.shutdown()
            thread.join(5)
