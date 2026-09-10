"""Real loopback HTTP + deterministic V2 integration, without model weights."""

import json
from contextlib import closing, contextmanager
from http.client import HTTPConnection
from importlib.resources import files
from threading import Event, Thread
from time import monotonic, sleep

import pytest

from ark.intelligence.contracts import Capabilities
from ark.intelligence.engine import Intelligence
from ark.logging import SessionLogger
from ark.ui.server import ASSETS, LocalServer, main
from ark.ui.session import LocalSession, Runtime, SessionError, load_runtime


class ConversationBackend:
    name = "simulated-local.gguf"
    last_metrics = None

    def __init__(self):
        self.calls = []
        self.error = False
        self.entered = Event()
        self.release = Event()
        self.release.set()

    def generate(self, messages, config):
        self.calls.append(messages)
        self.entered.set()
        assert self.release.wait(5), "test generation was never released"
        if self.error:
            raise RuntimeError("simulated failure")
        if messages[-1]["content"] == "合言葉は？":
            return "青いりんご" if any("青いりんご" in m["content"] for m in messages) else "不明"
        return "こんにちは。" + messages[-1]["content"]


def until(session, state="ready"):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        snapshot = session.snapshot()
        if snapshot["state"] == state:
            return snapshot
        sleep(0.01)
    pytest.fail(f"session did not reach {state}: {session.snapshot()}")


@contextmanager
def running(session):
    with LocalServer(session, port=0) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        session.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(5)


def request(server, path="/api/status", payload=None, *, headers=None, method=None, raw=None):
    method = method or ("POST" if payload is not None or raw is not None else "GET")
    body = raw if raw is not None else (
        json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    )
    supplied = {"Origin": server.origin, "X-ARK-Token": server.token,
                "Content-Type": "application/json"}
    supplied.update(headers or {})
    with closing(HTTPConnection("127.0.0.1", server.server_port, timeout=5)) as client:
        client.request(method, path, body=body, headers=supplied)
        response = client.getresponse()
        data = response.read()
        if "application/json" in response.getheader("Content-Type", ""):
            data = json.loads(data)
        return response.status, dict(response.getheaders()), data


@pytest.fixture
def rig(tmp_path):
    backend = ConversationBackend()
    engine = Intelligence(backend, Capabilities(4096, True, "test simulation"))
    logger = SessionLogger(tmp_path / "logs")
    runtime = Runtime(engine, {"name": backend.name, "local_model": False}, logger)
    session = LocalSession(lambda: runtime)
    with running(session) as server:
        until(session)
        yield server, session, runtime, backend


def send(server, session, message):
    status, _, body = request(server, "/api/chat", {
        "message": message, "revision": session.snapshot()["revision"],
    })
    assert status == 202, body
    return until(session)


def test_loopback_only_and_model_metadata(rig):
    server, _, _, _ = rig
    assert server.socket.getsockname()[0] == "127.0.0.1"
    status, headers, body = request(server)
    assert status == 200
    assert body["state"] == "ready" and body["intelligence"] == "V2"
    assert body["model"]["name"] == "simulated-local.gguf"
    assert body["model"]["local_model"] is False
    assert body["logging"] is True
    assert headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers
    with pytest.raises(OSError):
        LocalServer(LocalSession(lambda: None), server.server_port)


def test_v2_multiturn_reset_logging_and_model_reuse(rig):
    server, session, runtime, backend = rig
    assert send(server, session, "合言葉は青いりんごです")["messages"][-1]["role"] == "assistant"
    assert send(server, session, "合言葉は？")["messages"][-1]["content"] == "青いりんご"
    assert [m["role"] for m in backend.calls[1]] == ["system", "user", "assistant", "user"]
    assert len(runtime.engine.history) == 4
    snapshot = session.snapshot()
    assert request(server, "/api/reset", {"revision": snapshot["revision"]})[0] == 200
    assert session.snapshot()["messages"] == [] and runtime.engine.history == ()
    assert send(server, session, "合言葉は？")["messages"][-1]["content"] == "不明"
    assert len(backend.calls) == 3
    rows = [json.loads(line) for line in
            runtime.logger.path.read_text(encoding="utf-8").splitlines()]
    assert [r["role"] for r in rows] == ["user", "assistant", "user", "assistant",
                                       "event", "user", "assistant"]
    assert rows[4]["content"] == "Conversation reset; history empty"


def test_loading_is_visible_and_loader_runs_once():
    release = Event()
    calls = []

    def loader():
        calls.append(1)
        assert release.wait(5)
        return load_runtime(None, mock=True)

    session = LocalSession(loader)
    with running(session) as server:
        try:
            assert request(server)[2]["state"] == "loading"
            session.start()
            assert request(server, "/api/chat", {"revision": 0, "message": "hello"})[0] == 409
        finally:
            release.set()
        until(session)
        send(server, session, "hello")
        send(server, session, "again")
        assert len(calls) == 1


def test_generation_serialized_and_stale_tabs_rejected(rig):
    server, session, runtime, backend = rig
    backend.release.clear()
    revision = session.snapshot()["revision"]
    try:
        payload = {"revision": revision, "message": "first"}
        assert request(server, "/api/chat", payload)[0] == 202
        assert backend.entered.wait(2)
        state = request(server)[2]
        assert state["state"] == "generating" and state["pending_message"] == "first"
        assert request(server, "/api/chat", payload)[0] == 409
        assert request(server, "/api/reset", {"revision": state["revision"]})[0] == 409
    finally:
        backend.release.set()
    until(session)
    assert len(runtime.engine.history) == 2
    assert request(server, "/api/chat", payload)[0] == 409
    assert request(server, "/api/reset", {"revision": revision})[0] == 409


def test_generation_error_preserves_v2_context_and_allows_retry(rig):
    server, session, runtime, backend = rig
    send(server, session, "合言葉は青いりんごです")
    history = runtime.engine.history
    backend.error = True
    result = send(server, session, "合言葉は？")
    assert "simulated failure" in result["error"]
    assert result["pending_message"] is None
    assert runtime.engine.history == history and len(result["messages"]) == 2
    backend.error = False
    assert send(server, session, "合言葉は？")["messages"][-1]["content"] == "青いりんご"


def test_model_load_failure_remains_visible(tmp_path):
    session = LocalSession(lambda: load_runtime(str(tmp_path / "missing.toml")))
    with running(session) as server:
        until(session, "error")
        result = request(server)[2]
        assert "configuration not found" in result["error"]
        assert result["model"] is None and result["messages"] == []
        assert request(server, "/api/reset", {"revision": result["revision"]})[0] == 409
        assert request(server, "/")[0] == 200


def test_real_adapter_uses_existing_config_and_v2(tmp_path, monkeypatch):
    backend = ConversationBackend()
    configs = []

    def build(config):
        configs.append(config)
        return backend

    monkeypatch.setattr("ark.intelligence.runtime.build_backend", build)
    path = tmp_path / "config.toml"
    path.write_text('[model]\npath="placeholder.gguf"\nfamily="independent family"\n'
                    'quantization="Q4_K_M"\nthreads=4\ncontext_size=4096\n'
                    '[generation]\nmax_tokens=256\ntemperature=0.2\n'
                    '[logging]\ndirectory=' + json.dumps(str(tmp_path / "logs")), encoding="utf-8")
    runtime = load_runtime(str(path))
    assert isinstance(runtime.engine, Intelligence)
    assert runtime.engine.backend is backend
    assert configs[0].threads == 4 and runtime.engine.generation.max_tokens == 256
    assert runtime.engine.generation.temperature == 0.2
    assert runtime.metadata["family"] == "independent family"
    assert runtime.metadata["quantization"] == "Q4_K_M"
    assert runtime.metadata["local_model"] is True  # Adapter simulation, not measured performance.


@pytest.mark.parametrize("headers", [
    {"Host": "attacker.invalid:8765"},
    {"Host": "localhost:8765"},
    {"Origin": "https://attacker.invalid"},
    {"Origin": "null"},
    {"Sec-Fetch-Site": "cross-site"},
])
def test_cross_origin_reads_and_writes_rejected(rig, headers):
    server, session, _, backend = rig
    assert request(server, headers=headers)[0] == 403
    assert request(server, "/api/chat", {"revision": session.snapshot()["revision"],
                                        "message": "hello"}, headers=headers)[0] == 403
    assert backend.calls == []


@pytest.mark.parametrize("headers", [{"X-ARK-Token": "wrong"}, {"Origin": ""}])
def test_write_requires_process_token_and_origin(rig, headers):
    server, session, _, _ = rig
    assert request(server, "/api/reset", {"revision": session.snapshot()["revision"]},
                   headers=headers)[0] == 403


@pytest.mark.parametrize("payload,status", [
    ({"message": "", "revision": 1}, 400),
    ({"message": "  ", "revision": 1}, 400),
    ({"message": ["hello"], "revision": 1}, 400),
    ({"message": "x" * 16001, "revision": 1}, 413),
    ({"message": "hello", "revision": 1, "messages": []}, 400),
    ({"message": "hello", "revision": True}, 409),
    ({"message": "hello", "revision": 0}, 409),
    (["hello"], 400),
])
def test_untrusted_request_validation(rig, payload, status):
    server, _, _, backend = rig
    assert request(server, "/api/chat", payload)[0] == status
    assert backend.calls == []


def test_malformed_and_oversized_http_body(rig):
    server, _, _, _ = rig
    assert request(server, "/api/chat", raw=b"not json")[0] == 400
    assert request(server, "/api/chat", raw=b"x" * 65537)[0] == 413
    assert request(server, "/api/chat", raw=b"{}",
                   headers={"Content-Type": "text/plain"})[0] == 415


def test_only_bundled_assets_can_be_read(rig):
    server, _, _, _ = rig
    for route, (filename, mime) in ASSETS.items():
        status, headers, body = request(server, route)
        assert status == 200 and headers["Content-Type"] == mime
        assert body == files("ark.ui").joinpath("static", filename).read_bytes()
    for route in ("/config.toml", "/logs", "/../config.toml", "/%2e%2e/config.toml"):
        assert request(server, route)[0] == 404


def test_assistant_log_failure_does_not_hide_committed_answer(rig, monkeypatch):
    server, session, runtime, _ = rig

    def write(**kwargs):
        if kwargs["role"] == "assistant":
            raise OSError("disk full")

    monkeypatch.setattr(runtime.logger, "write", write)
    assert request(server, "/api/chat", {"message": "hello", "revision": 1})[0] == 202
    result = until(session, "error")
    assert result["messages"][-1]["content"] == "こんにちは。hello"
    assert len(runtime.engine.history) == 2 and result["warning"]
    with pytest.raises(SessionError):
        session.chat("next", result["revision"])


def test_user_log_failure_does_not_advance_context(rig, monkeypatch):
    server, session, runtime, backend = rig

    def write(**kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(runtime.logger, "write", write)
    assert request(server, "/api/chat", {"message": "hello", "revision": 1})[0] == 202
    result = until(session, "error")
    assert result["messages"] == [] and result["warning"]
    assert runtime.engine.history == () and backend.calls == []


@pytest.mark.parametrize("argv", [[], ["--host", "0.0.0.0"], ["--mock", "--config", "x"],
                                  ["--mock", "--port", "0"]])
def test_cli_refuses_ambiguous_or_public_modes(argv):
    with pytest.raises(SystemExit):
        main(argv)
