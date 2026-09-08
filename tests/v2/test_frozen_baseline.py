"""Audit original evidence without executing a model or changing frozen scoring."""
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from ark.evaluation.compare import compare
from ark.evaluation.scoring import score
from ark.evaluation.suite import load_suite
from ark.intelligence.context import ContextManager
from ark.intelligence.contracts import Message, TaskMode
from ark.intelligence.policy import system_instruction

ROOT = Path(__file__).resolve().parents[2] / "evidence" / "v2"


def read(name):
    return json.loads((ROOT / "raw" / name).read_text(encoding="utf-8"))


def test_original_hashes():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for item in manifest["files"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]


def test_distinct_runs_and_frozen_scores():
    left, right = read("v2-real-1.json"), read("v2-real-2.json")
    end = datetime.fromisoformat(left["timestamp"]) + timedelta(seconds=left["elapsed_seconds"])
    assert end < datetime.fromisoformat(right["timestamp"])
    ids = []
    for report in (left, right):
        ids.append({t["request"]["request_id"] for c in report["cases"] for t in c["turns"]})
        assert report["runtime_failure_count"] == 0
        assert [c["task_id"] for c in report["cases"] if not c["model_passed"]] == ["math-02"]
        for case, row in zip(load_suite()["cases"], report["cases"], strict=True):
            verdict = score(row["response"], case)
            assert verdict.passed == row["model_passed"]
            assert verdict.details == row["scoring_details"]
            assert row["failure_reason"] == (None if verdict.passed else verdict.reason)
            history = ()
            for prompt, turn in zip([*case.get("setup", []), case["prompt"]],
                                    row["turns"], strict=True):
                prepared = ContextManager(4096).prepare(
                    system_instruction(TaskMode(case["mode"])), history, prompt, 256
                )
                assert json.loads(json.dumps(asdict(prepared))) == turn["request"]["context"]
                history = (*prepared.retained_history, Message("user", prompt),
                           Message("assistant", turn["text"]))
    assert len(ids[0]) == len(ids[1]) == 15
    assert ids[0].isdisjoint(ids[1])
    assert compare(left, right) == read("comparison.json")


def test_regression_and_reset_evidence():
    v1 = read("v1-regression.json")
    assert v1["startup_success"] and not v1["test_backend"]
    assert v1["failure_count"] == 0 and len(v1["cases"]) == 6
    assert "青いりんご" in v1["cases"][-1]["response"]
    rows = [json.loads(line) for line in
            (ROOT / "raw/v2-session.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert rows[-1]["content"] == "Session exited"
    assert rows[-2]["content"] == "未指定"
    assert any(row["content"] == "Conversation reset; history empty" for row in rows)
