import copy
import json
import subprocess
import sys

import pytest

from ark.evaluation.compare import compare
from ark.evaluation.compare import main as compare_main
from ark.evaluation.runner import main as eval_main
from ark.evaluation.runner import run_mock
from ark.evaluation.suite import SUITE_SHA256, load_suite


@pytest.fixture
def report(tmp_path):
    return run_mock(tmp_path / "mock.json")


def test_mock_metrics_are_not_model_evidence(report):
    assert report["infrastructure_failure_count"] == 0
    assert report["v1_gate"] == "OFFICIAL_PASS"
    assert report["v2_gate"] == "NOT_PASSED"
    assert report["real_model_evaluation"] == "NOT_MEASURED_BY_MOCK"
    assert all(v is None for v in report["model_metrics"].values())
    assert all(d["model_pass_rate"] is None for d in report["domains"].values())
    assert all(c["model_passed"] is None for c in report["cases"])
    assert report["suite_sha256"] == SUITE_SHA256
    assert len(load_suite()["cases"]) == 12


def test_context_evidence_contains_prior_turns_but_not_scoring_answers(report):
    context = next(c for c in report["cases"] if c["task_id"] == "context-02")
    messages = context["infrastructure_turns"][-1]["request"]["context"]["messages"]
    assert [m["role"] for m in messages] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
    ]
    math = next(c for c in report["cases"] if c["task_id"] == "math-01")
    payload = math["infrastructure_turns"][0]["request"]["context"]["messages"]
    assert "102" not in json.dumps(payload)
    assert "expected" not in json.dumps(payload)


def test_broken_generation_records_failure_and_continues(tmp_path, monkeypatch):
    def broken(self, messages, config):
        raise RuntimeError("simulated runtime failure")

    monkeypatch.setattr("ark.evaluation.runner.FixtureBackend.generate", broken)
    result = run_mock(tmp_path / "broken.json")
    assert result["infrastructure_failure_count"] == 12
    assert all("RuntimeError" in c["failure_reason"] for c in result["cases"])
    assert all(c["response"] is None for c in result["cases"])
    assert (tmp_path / "broken.json").exists()


def test_suite_tamper_is_rejected(monkeypatch):
    monkeypatch.setattr("ark.evaluation.suite.SUITE_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="hash mismatch"):
        load_suite()


def test_repeat_runs_and_regression_detect_real_fixture_drop(report, tmp_path, monkeypatch):
    from ark.evaluation.mock import FixtureBackend

    unchanged = run_mock(tmp_path / "repeat.json")
    assert not compare(report, unchanged)["regression_detected"]
    original = FixtureBackend.generate

    def wrong_square(self, messages, config):
        if messages[-1]["content"].startswith("Write Python function square(n)"):
            return "def square(n):\n    return n+n"
        return original(self, messages, config)

    monkeypatch.setattr(FixtureBackend, "generate", wrong_square)
    degraded = run_mock(tmp_path / "bad.json")
    result = compare(report, degraded)
    assert result["regressions"] == ["coding-01"]
    assert result["model_quality_delta"] is None
    assert result["main_merge"] == "BLOCKED_PENDING_V2_REAL_REVIEW"
    assert compare(degraded, report)["improvements"] == ["coding-01"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(suite_sha256="bad"),
        lambda r: r.update(scorer_version="other"),
        lambda r: r.update(measurement_kind="real"),
        lambda r: r["cases"].pop(),
        lambda r: r["cases"].append(r["cases"][0]),
        lambda r: r["domains"]["math"].update(fixture_pass_rate=0),
        lambda r: r["model_metrics"].update(tokens_per_second=15),
        lambda r: r["cases"][0].update(model_passed=True),
        lambda r: r.update(infrastructure_failure_count=5),
    ],
)
def test_invalid_or_incompatible_evidence_fails(report, mutation):
    changed = copy.deepcopy(report)
    mutation(changed)
    with pytest.raises(ValueError):
        compare(report, changed)


def test_compare_cli_writes_evidence(tmp_path):
    left, right = tmp_path / "left.json", tmp_path / "right.json"
    assert eval_main(["--output", str(left)]) == 0
    assert eval_main(["--output", str(right)]) == 0
    output = tmp_path / "comparison.json"
    assert compare_main([str(left), str(right), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["comparison_kind"] == "fixture_regression_only"


def test_real_model_cli_requires_explicit_config(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "ark.evaluation.runner", "--backend", "llama-cpp"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert "--config is required" in result.stderr
    assert not list(tmp_path.iterdir())


def test_v2_mock_cli_reset_and_mode():
    result = subprocess.run(
        [sys.executable, "-m", "ark.intelligence.cli", "--mode", "coding"],
        input="hello\n/reset\n/exit\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "MOCK ONLY" in result.stdout
    assert "Conversation reset." in result.stdout
