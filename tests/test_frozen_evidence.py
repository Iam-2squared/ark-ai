"""Preserve original V1 evidence; this does not re-run the target PC."""

import hashlib
import json
from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[1] / "evidence" / "v1" / "raw"
HASHES = {
    "v1-offline-1.json": "721648a10fd3fbe80fffa0c8f8f2c40819197f02620dadd0d2b292fde28d6a82",
    "v1-offline-2.json": "6eb9828a71839beb1ac5c015ae57a981a4b1148da2025c10ea6a18043df3a96a",
    "online-session.jsonl": "71adcf024de0d06324f0773de9aea82635ba72aa59cc78dd1d37b0252772f588",
    "offline-session.jsonl": "512e823a11621f9f6b6378f43a57300f06e6853322680c25af3a59aa2e934b60",
}


@pytest.mark.parametrize("name,digest", HASHES.items())
def test_original_bytes(name, digest):
    assert hashlib.sha256((RAW / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name", ["v1-offline-1.json", "v1-offline-2.json"])
def test_reviewed_benchmark(name):
    data = json.loads((RAW / name).read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["startup_success"] is True
    assert data["test_backend"] is False
    assert data["failure_count"] == 0
    assert data["network_disconnected_user_attested"] is True
    assert data["offline_verified_automatically"] is False
    assert data["v1_final_gate"] == "pending_human_review"
    assert len(data["cases"]) == 6
    assert all(case["success"] and not case["error"] for case in data["cases"])
    recall = next(case for case in data["cases"] if case["category"] == "memory_recall")
    assert "青いりんご" in recall["response"]


@pytest.mark.parametrize("name", ["online-session.jsonl", "offline-session.jsonl"])
def test_test_only_session(name):
    rows = [json.loads(line) for line in (RAW / name).read_text(encoding="utf-8").splitlines()]
    assert [row["role"] for row in rows] == ["user", "assistant"] * 4
    assert "青いりんご" in rows[5]["content"]
    assert rows[7]["content"] == "新しい会話です。"
