"""Next UI assets and the unchanged conversation API on real loopback sockets."""

import json
from contextlib import closing, contextmanager
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from time import monotonic, sleep

import pytest

from ark.command_center import CommandCenterServer, load_assets, main
from ark.ui.session import LocalSession, load_runtime


def until_ready(session):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        snapshot = session.snapshot()
        if snapshot["state"] == "ready":
            return snapshot
        sleep(0.01)
    pytest.fail(f"session did not reach ready: {session.snapshot()}")


def request(server, path="/", payload=None, *, headers=None):
    supplied = {
        "Origin": server.origin,
        "X-ARK-Token": server.token,
        "Content-Type": "application/json",
    }
    supplied.update(headers or {})
    data = json.dumps(payload).encode() if payload is not None else None
    with closing(HTTPConnection("127.0.0.1", server.server_port, timeout=5)) as client:
        client.request("POST" if payload is not None else "GET", path, data, supplied)
        response = client.getresponse()
        body = response.read()
        if "application/json" in response.getheader("Content-Type", ""):
            body = json.loads(body)
        return response.status, dict(response.getheaders()), body


@contextmanager
def running(directory):
    session = LocalSession(lambda: load_runtime(None, mock=True))
    with CommandCenterServer(session, directory, port=0) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        session.start()
        until_ready(session)
        try:
            yield server, session
        finally:
            server.shutdown()
            thread.join(5)


@pytest.fixture
def bundle(tmp_path):
    directory = tmp_path / "dist"
    directory.mkdir()
    (directory / "assets").mkdir()
    (directory / "index.html").write_text('<script src="/assets/app-123.js"></script>')
    (directory / "assets" / "app-123.js").write_text("document.title='ARK';")
    (directory / "assets" / "app-123.css").write_text("body{color:cyan}")
    (directory / "assets" / "app-123.js.map").write_text("private source map")
    (directory / "private.json").write_text('{"secret":"not public"}')
    (directory / "nested").mkdir()
    (directory / "nested" / "private.js").write_text("private nested file")
    return directory


def test_built_assets_preserve_loopback_and_security_headers(bundle):
    with running(bundle) as (server, _):
        assert server.socket.getsockname()[0] == "127.0.0.1"
        status, headers, body = request(server)
        assert status == 200 and b"/assets/app-123.js" in body
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "script-src 'self'" in headers["Content-Security-Policy"]
        assert "unsafe-inline" not in headers["Content-Security-Policy"]
        assert "Access-Control-Allow-Origin" not in headers
        status, headers, body = request(server, "/assets/app-123.js?v=1")
        assert status == 200 and body == b"document.title='ARK';"
        assert headers["Content-Type"] == "text/javascript; charset=utf-8"
        assert request(server, "/assets/app-123.css")[0] == 200


@pytest.mark.parametrize("path", [
    "/private.json", "/assets/app-123.js.map", "/nested/private.js", "/../index.html",
    "/assets/../../private.json", "/assets/%2e%2e/private.json", "/conversation",
    "/app.js", "/api/memory", "/api/tools", "/api/cancel",
])
def test_no_filesystem_fallback_or_unimplemented_get_api(bundle, path):
    with running(bundle) as (server, _):
        assert request(server, path)[0] == 404


def test_assets_are_startup_snapshot_not_live_filesystem(bundle):
    with running(bundle) as (server, _):
        (bundle / "assets" / "app-123.js").write_text("changed after startup")
        (bundle / "assets" / "new.js").write_text("not allowlisted")
        assert request(server, "/assets/app-123.js")[2] == b"document.title='ARK';"
        assert request(server, "/assets/new.js")[0] == 404


def test_status_chat_reset_use_real_v2_session_and_revision_semantics(bundle):
    with running(bundle) as (server, session):
        status, _, snapshot = request(server, "/api/status")
        assert status == 200 and snapshot["state"] == "ready"
        assert snapshot["intelligence"] == "V2"
        assert snapshot["model"]["local_model"] is False
        assert snapshot["token"] == server.token
        revision = snapshot["revision"]
        payload = {"message": "こんにちは", "revision": revision}
        assert request(server, "/api/chat", payload)[0] == 202
        result = until_ready(session)
        assert result["messages"][0] == {"role": "user", "content": "こんにちは"}
        assert result["messages"][-1]["role"] == "assistant"
        assert "こんにちは" in result["messages"][-1]["content"]
        assert request(server, "/api/chat", payload)[0] == 409
        assert request(server, "/api/reset", {"revision": result["revision"]})[0] == 200
        assert session.snapshot()["messages"] == []


@pytest.mark.parametrize("headers", [
    {"Origin": "http://example.com"}, {"Host": "localhost:8766"},
    {"Sec-Fetch-Site": "cross-site"},
])
def test_same_origin_checks_cover_assets_and_api(bundle, headers):
    with running(bundle) as (server, session):
        assert request(server, "/", headers=headers)[0] == 403
        assert request(server, "/api/status", headers=headers)[0] == 403
        assert request(server, "/api/reset", {"revision": session.snapshot()["revision"]},
                       headers=headers)[0] == 403


def test_write_token_is_required_and_no_new_write_capability_exists(bundle):
    with running(bundle) as (server, session):
        payload = {"revision": session.snapshot()["revision"]}
        assert request(server, "/api/reset", payload, headers={"X-ARK-Token": "wrong"})[0] == 403
        for path in ("/api/cancel", "/api/tools/execute", "/api/memory", "/api/approve"):
            assert request(server, path, payload)[0] == 404


def test_missing_build_fails_before_model_loader(tmp_path):
    assert main(["--mock", "--dist", str(tmp_path / "missing")]) == 1
    with pytest.raises(ValueError, match="index.html"):
        load_assets(tmp_path)


def test_build_symlinks_are_rejected_without_serving_target(bundle, tmp_path):
    target = tmp_path / "secret.js"
    target.write_text("secret")
    link = bundle / "assets" / "leak.js"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links unavailable for current account")
    with pytest.raises(ValueError, match="symbolic"):
        load_assets(bundle)


@pytest.mark.parametrize("args", [[], ["--mock", "--config", "config.toml"],
                                  ["--mock", "--port", "0"],
                                  ["--mock", "--port", "65536"]])
def test_cli_rejects_ambiguous_runtime_and_non_user_ports(args):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2


def test_asset_snapshot_is_immutable(bundle):
    assets = load_assets(Path(bundle))
    with pytest.raises(TypeError):
        assets["/new.js"] = (b"alert(1)", "text/javascript")
