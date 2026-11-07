"""A policy callback must never redirect offline proactive writes."""

import sqlite3
from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy():
    return SyntheticTriggerPolicy(
        "synthetic-owner", "offline", "observe", 1, "v1", 1, 100, 3,
    )


def _prepared(store, policy, *, at_ms=10):
    return store.prepare(
        policy,
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=at_ms,
        now_ms=at_ms,
    )


def _rows(path: Path) -> int:
    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone()[0]


@pytest.mark.parametrize("identity_call", [1, 2, 3])
def test_reflective_policy_callback_cannot_redirect_proactive_write(
    tmp_path, monkeypatch, identity_call,
):
    source_path = tmp_path / "prepared # percent %.sqlite"
    alternate_path = tmp_path / "other.sqlite"
    store = SyntheticProactiveLedger(source_path)
    SyntheticProactiveLedger(alternate_path)
    policy = _policy()
    original = SyntheticTriggerPolicy.identity
    calls = []

    def redirected(self):
        result = original(self)
        calls.append(True)
        if len(calls) == identity_call:
            store.path = alternate_path
        return result

    monkeypatch.setattr(SyntheticTriggerPolicy, "identity", redirected)
    with pytest.raises(SyntheticTriggerRejected, match="path"):
        _prepared(store, policy)
    assert len(calls) == identity_call
    assert _rows(source_path) == 0
    assert _rows(alternate_path) == 0


def test_stable_proactive_path_keeps_inert_durable_dedup(tmp_path):
    path = tmp_path / "prepared # percent %.sqlite"
    store = SyntheticProactiveLedger(path)
    receipt = _prepared(store, _policy())
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert _rows(path) == 1
    with pytest.raises(SyntheticTriggerRejected, match="duplicate"):
        _prepared(SyntheticProactiveLedger(path), _policy(), at_ms=11)


@pytest.mark.parametrize("bad_path", ["not-a-path", None])
def test_proactive_rejects_mutated_nonpath_before_opening_storage(
    tmp_path, bad_path,
):
    path = tmp_path / "prepared # percent %.sqlite"
    store = SyntheticProactiveLedger(path)
    store.path = bad_path
    with pytest.raises(SyntheticTriggerRejected, match="path"):
        _prepared(store, _policy())
    assert _rows(path) == 0
