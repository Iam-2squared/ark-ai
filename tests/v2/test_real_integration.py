"""Adapter simulations only. No model weights or real capability results in CI."""

import copy
import hashlib
import json

import pytest

from ark.config import ArkConfig
from ark.evaluation.compare import compare
from ark.evaluation.mock import FixtureBackend
from ark.evaluation.real import run_real
from ark.evaluation.runner import main, run_mock
from ark.intelligence.cli import main as chat_main
from ark.intelligence.runtime import local_engine


@pytest.fixture
def simulated_local(tmp_path, monkeypatch):
    weights = tmp_path / "simulated.gguf"
    weights.write_bytes(b"unit-test placeholder, not actual weights")
    config = tmp_path / "test.toml"
    config.write_text(
        '[model]\nbackend="llama-cpp"\npath=' + json.dumps(str(weights))
        + '\ncontext_size=4096\nthreads=4\n[logging]\ndirectory='
        + json.dumps(str(tmp_path / "logs"))
        + '\n[generation]\nmax_tokens=256\ntemperature=0\n', encoding="utf-8",
    )
    monkeypatch.setattr("ark.intelligence.runtime.build_backend", lambda config: FixtureBackend())
    return str(config), weights


def test_simulated_real_adapter_contract(simulated_local, tmp_path):
    config, weights = simulated_local
    result = run_real(config, tmp_path / "simulation.json")
    assert result["startup_success"]
    assert result["model_failures"] == result["runtime_failure_count"] == 0
    assert result["model_identity"]["weights_sha256"] == hashlib.sha256(
        weights.read_bytes()
    ).hexdigest()
    assert result["v2_gate"] == "PENDING_REVIEW"
    assert len(result["cases"]) == 12
    assert result["offline_verified_automatically"] is False
    assert all(row["fixture_passed"] is None for row in result["cases"])
    assert all(row["model_metrics"]["prompt_tokens"] is None for row in result["cases"])
    context = next(row for row in result["cases"] if row["task_id"] == "context-02")
    assert len(context["turns"][-1]["request"]["context"]["messages"]) == 6
    assert not compare(result, result)["regression_detected"]


def test_real_startup_failure_is_saved(tmp_path):
    output = tmp_path / "failure.json"
    assert main(["--backend", "llama-cpp", "--config", str(tmp_path / "absent.toml"),
                 "--output", str(output)]) == 1
    result = json.loads(output.read_text())
    assert not result["startup_success"]
    assert result["runtime_failure_count"] == 1
    assert result["model_performance_status"] == "NOT_MEASURED"
    assert result["cases"] == []
    with pytest.raises(ValueError, match="startup failure"):
        compare(result, result)


def test_generation_failure_saved_and_suite_continues(simulated_local, tmp_path, monkeypatch):
    def broken(*args):
        raise RuntimeError("simulated generation error")

    monkeypatch.setattr(FixtureBackend, "generate", broken)
    result = run_real(simulated_local[0], tmp_path / "broken.json")
    assert result["runtime_failure_count"] == 12
    assert result["model_failures"] == 12
    assert all(row["runtime_error"] for row in result["cases"])


def test_low_score_is_not_runtime_failure(simulated_local, tmp_path, monkeypatch):
    monkeypatch.setattr(FixtureBackend, "generate", lambda *args: "incorrect")
    output = tmp_path / "low.json"
    assert main(["--backend", "llama-cpp", "--config", simulated_local[0],
                 "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["model_failures"] == 12
    assert result["v2_gate"] == "PENDING_REVIEW"
    assert not compare(result, result)["regression_detected"]


def test_real_scoring_regression_and_mixed_rejection(simulated_local, tmp_path, monkeypatch):
    baseline = run_real(simulated_local[0], tmp_path / "baseline.json")
    monkeypatch.setattr(FixtureBackend, "generate", lambda *args: "incorrect")
    candidate = run_real(simulated_local[0], tmp_path / "candidate.json")
    assert len(compare(baseline, candidate)["regressions"]) == 12
    with pytest.raises(ValueError):
        compare(baseline, run_mock(tmp_path / "mock.json"))


@pytest.mark.parametrize("mutation", [
    lambda r: r["cases"].pop(),
    lambda r: r["cases"].append(r["cases"][0]),
    lambda r: r["cases"][0].update(model_passed=False),
    lambda r: r["cases"][0].update(prompt="modified"),
    lambda r: r["cases"][0].update(response="forged"),
    lambda r: r["domains"]["math"].update(model_pass_rate=0),
    lambda r: r.update(runtime_failure_count=99),
    lambda r: r["model_identity"].update(weights_sha256="bad"),
])
def test_corrupt_real_report_rejected(simulated_local, tmp_path, mutation):
    baseline = run_real(simulated_local[0], tmp_path / "baseline.json")
    changed = copy.deepcopy(baseline)
    mutation(changed)
    with pytest.raises(ValueError):
        compare(baseline, changed)


def test_real_cli_logs_reset_and_exit(simulated_local, tmp_path, monkeypatch):
    inputs = iter(["hello", "/reset", "hello", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert chat_main(["--backend", "llama-cpp", "--config", simulated_local[0]]) == 0
    rows = [json.loads(line) for path in (tmp_path / "logs").glob("*.jsonl")
            for line in path.read_text().splitlines()]
    assert any(row["content"] == "Conversation reset; history empty" for row in rows)
    assert rows[-1]["content"] == "Session exited"


def test_real_backend_refuses_echo():
    with pytest.raises(ValueError, match="not a mock"):
        local_engine(ArkConfig(backend="echo"))


def test_mock_cli_cannot_silently_ignore_config():
    with pytest.raises(SystemExit):
        main(["--config", "config.toml"])
    with pytest.raises(SystemExit):
        chat_main(["--config", "config.toml"])
