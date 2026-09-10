"""Protect reviewed Local UI originals without re-running a target model."""

import hashlib
import json
from pathlib import Path

from ark.evaluation.compare import compare

ROOT = Path(__file__).resolve().parents[2] / "evidence" / "local-ui"


def _json(name):
    return json.loads((ROOT / "raw" / name).read_text(encoding="utf-8"))


def test_original_hashes_and_private_screenshot_policy():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["tested_code_sha"] == "1f4b197605fae6f9a1be8d47072122c6f3154e94"
    for item in manifest["raw_files"]:
        digest = hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
        assert digest == item["sha256"]
    assert manifest["screenshots_stored_in_public_repo"] is False
    assert len(manifest["reviewed_external_screenshots"]) == 3
    assert all(len(item["sha256"]) == 64 for item in manifest["reviewed_external_screenshots"])


def test_ui_sessions_and_reset_isolation():
    raw = (ROOT / "raw/offline-reset-session.jsonl").read_text(encoding="utf-8")
    reset_rows = [json.loads(line) for line in raw.splitlines()]
    assert [r["role"] for r in reset_rows] == [
        "event", "user", "assistant", "user", "assistant", "event", "user", "assistant"
    ]
    assert reset_rows[5]["content"] == "Conversation reset; history empty"
    assert "青いりんご" in reset_rows[4]["content"]
    assert reset_rows[-1]["content"] == "未指定"
    behavior = (ROOT / "raw/browser-behavior-session.jsonl").read_text(encoding="utf-8")
    assert "いま\\nテスト中" in behavior


def test_v1_v2_regression_and_fixed_failure():
    v1, v2 = _json("v1-regression.json"), _json("v2-regression.json")
    assert v1["startup_success"] and not v1["test_backend"] and v1["failure_count"] == 0
    assert v1["model_file"]["sha256"] == v2["model_identity"]["weights_sha256"]
    assert v2["runtime_failure_count"] == 0
    assert [c["task_id"] for c in v2["cases"] if not c["model_passed"]] == ["math-02"]
    baseline = json.loads(
        (ROOT.parent / "v2/raw/v2-real-1.json").read_text(encoding="utf-8")
    )
    assert compare(baseline, v2) == _json("v2-comparison.json")
