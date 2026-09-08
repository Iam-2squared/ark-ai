import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from ark.benchmark import main, run
from ark.core import ArkCore
from ark.measurement import peak_ram_mib
from ark.models import GenerationConfig, LlamaCppBackend


def test_native_peak_memory():
    # Runs on actual Windows and Linux CI hosts (no mocked platform API).
    assert peak_ram_mib() > 0


def test_startup_failure_writes_evidence(tmp_path):
    output = tmp_path / "failure.json"
    assert main(["--config", str(tmp_path / "missing.toml"), "--output", str(output)]) == 1
    result = json.loads(output.read_text())
    assert result["startup_success"] is False
    assert result["failure_count"] == 1
    assert result["startup_error"].startswith("FileNotFoundError")


def test_mock_cannot_certify_final_gate(tmp_path):
    result = run("tests/fixtures/echo.toml", tmp_path / "mock.json", offline_attested=True)
    assert result["test_backend"] is True
    assert result["v1_final_gate"] == "pending_human_review"
    assert result["offline_verified_automatically"] is False
    assert result["semantic_review"]["multi_turn"] == "pending"


def test_cli_entrypoint_reset_and_exit():
    result = subprocess.run(
        [sys.executable, "-m", "ark.cli", "--backend", "echo"],
        input="hello\n/reset\n/exit\n", text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0
    assert "ECHO: hello" in result.stdout
    assert "Conversation reset." in result.stdout


def test_stream_adapter_and_failure_do_not_commit_history(tmp_path, monkeypatch):
    captured = {}

    class FakeLlama:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def create_chat_completion(self, **kwargs):
            captured.update(kwargs)
            if len(kwargs["messages"]) > 2:
                raise ValueError("context full")
            return iter([
                {"choices": [{"delta": {"role": "assistant"}}]},
                {"choices": [{"delta": {"content": "こんにちは"}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}]},
            ])

        def tokenize(self, text, add_bos):
            assert text == "こんにちは".encode()
            assert add_bos is False
            return [1, 2]

    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=FakeLlama))
    path = tmp_path / "stub.gguf"
    path.write_bytes(b"test stub")
    backend = LlamaCppBackend(path, threads=4)
    core = ArkCore(backend, generation=GenerationConfig(seed=42))
    assert core.chat("hello") == "こんにちは"
    assert captured["n_gpu_layers"] == 0
    assert captured["seed"] == 42
    assert backend.last_metrics.completion_tokens == 2
    assert backend.last_metrics.first_token_seconds <= backend.last_metrics.elapsed_seconds
    with pytest.raises(ValueError, match="context full"):
        core.chat("again")
    assert len(core.history) == 2
    assert backend.last_metrics is None


def test_benchmark_passes_history_to_recall(tmp_path, monkeypatch):
    seen = []

    class RecordingBackend:
        name = "recording"
        last_metrics = None

        def generate(self, messages, config):
            seen.append(messages)
            return "ok"

    monkeypatch.setattr("ark.benchmark.build_backend", lambda config: RecordingBackend())
    result = run("tests/fixtures/echo.toml", tmp_path / "result.json")
    assert result["success_rate"] == 1
    assert len(seen[-1]) == 4
    assert "青いりんご" in seen[-1][1]["content"]
