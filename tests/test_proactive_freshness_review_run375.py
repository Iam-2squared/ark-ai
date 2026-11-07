"""Restart-safe, read-only proactive trigger freshness never grants dispatch."""

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_freshness_review import (
    review_prepared_trigger_freshness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _setup(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger #1 %.sqlite")
    policy = SyntheticTriggerPolicy(
        "owner", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _check(state, **changes):
    ledger, policy, receipt = state
    options = dict(
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10,
    )
    options.update(changes)
    return review_prepared_trigger_freshness(
        ledger, receipt, policy, **options,
    )


def test_fresh_markers_revalidate_without_notification_authority(tmp_path: Path):
    state = _setup(tmp_path)
    result = _check(state)
    assert result.trigger_id == state[2].trigger_id
    assert result.prepared_at_ms == 100
    assert result.history.digest.startswith("synthetic_triggers_")
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_age_boundary_passes_but_stale_observation_fails(tmp_path: Path):
    state = _setup(tmp_path)
    assert _check(state, now_ms=100).checked_at_ms == 100
    with pytest.raises(SyntheticTriggerRejected, match="stale"):
        _check(state, now_ms=101)


def test_clock_before_prepare_fails_closed(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticTriggerRejected, match="clock regressed"):
        _check(state, now_ms=99, max_observation_age_ms=100)


@pytest.mark.parametrize("bad", [True, "100", -1, 2**63])
def test_invalid_time_type_or_range_rejected(tmp_path: Path, bad):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticTriggerRejected, match="exact synthetic freshness"):
        _check(state, now_ms=bad)


def test_changed_policy_revision_cannot_reuse_trigger(tmp_path: Path):
    state = _setup(tmp_path)
    changed = replace(state[1], policy_revision="policy-v2")
    with pytest.raises(SyntheticTriggerRejected, match="mismatched"):
        _check((state[0], changed, state[2]))


def test_other_observation_digest_is_not_same_trigger(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticTriggerRejected, match="mismatched"):
        _check(state, observation_digest="c" * 64)


def test_receipt_time_forgery_refused(tmp_path: Path):
    state = _setup(tmp_path)
    forged = replace(state[2], prepared_at_ms=99)
    with pytest.raises(SyntheticTriggerRejected, match="persisted prepared marker"):
        _check((state[0], state[1], forged))


def test_mutated_persisted_preparation_time_refused(tmp_path: Path):
    state = _setup(tmp_path)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("UPDATE synthetic_prepared_triggers SET prepared_at_ms=101")
    with pytest.raises(SyntheticTriggerRejected, match="persisted prepared marker"):
        _check(state)


def test_independently_retained_history_detects_row_removal(tmp_path: Path):
    state = _setup(tmp_path)
    older = read_proactive_witness(state[0])
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("DELETE FROM synthetic_prepared_triggers")
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive"):
        _check(state, retained=older)


def test_unrelated_append_does_not_invalidate_retained_prefix(tmp_path: Path):
    state = _setup(tmp_path)
    witness = read_proactive_witness(state[0])
    state[0].prepare(
        state[1], source_digest="c" * 64, observation_digest="d" * 64,
        observed_at_ms=190, now_ms=200,
    )
    result = _check(
        state, now_ms=200, max_observation_age_ms=110, retained=witness,
    )
    assert len(result.history.row_hashes) == 2
    assert result.notification_authorized is False


def test_missing_store_is_read_only_and_never_recreated(tmp_path: Path):
    state = _setup(tmp_path)
    missing = tmp_path / "missing.sqlite"
    state[0].path = missing
    with pytest.raises(sqlite3.OperationalError):
        _check(state)
    assert not missing.exists()


def test_schema_drift_is_denied(tmp_path: Path):
    state = _setup(tmp_path)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("PRAGMA user_version=3")
    with pytest.raises(SyntheticTriggerRejected, match="schema version"):
        _check(state)


def test_invalid_retained_witness_type_is_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticTriggerRejected, match="exact retained"):
        _check(state, retained=object())
