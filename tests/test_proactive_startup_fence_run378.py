"""Synthetic readiness and prepared proactive state jointly deny all dispatch."""

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.proactive_startup_fence_review import (
    SyntheticProactiveStartupRejected,
    review_synthetic_proactive_startup,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)
from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
)
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger #1 %.sqlite")
    policy = SyntheticTriggerPolicy(
        "PRIVATE-OWNER", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent("scheduler", ("memory",), schema_revision="scheduler-1"),
        StartupComponent("camera", local_state=ReadinessState.BLOCKED),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, policy, receipt, snapshot, requirements


def _review(state, **overrides):
    ledger, policy, receipt, snapshot, requirements = state
    values = {
        "source_digest": "a" * 64,
        "observation_digest": "b" * 64,
        "captured_at_ms": 98,
        "now_ms": 100,
        "max_startup_age_ms": 5,
        "max_observation_age_ms": 10,
    }
    values.update(overrides)
    return review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements, **values,
    )


def test_local_readiness_does_not_enable_notification_or_dispatch(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert result.trigger_id == state[2].trigger_id
    assert result.readiness_digest == state[3].digest
    assert result.trigger_history_digest.startswith("synthetic_triggers_")
    assert result.checked_at_ms == 100
    assert result.startup_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert "PRIVATE-OWNER" not in repr(result)


def test_blocked_unrelated_camera_does_not_poison_scheduler_fixture(tmp_path: Path):
    state = _fixture(tmp_path)
    assert state[3].state("camera") is ReadinessState.BLOCKED
    assert _review(state).dispatch_authorized is False


@pytest.mark.parametrize("block", [ReadinessState.BLOCKED, ReadinessState.DEGRADED])
def test_required_memory_not_ready_denies_prepared_trigger(tmp_path: Path, block):
    state = list(_fixture(tmp_path))
    state[3] = evaluate_startup_readiness((
        StartupComponent("memory", local_state=block, schema_revision="memory-1"),
        StartupComponent("scheduler", ("memory",), schema_revision="scheduler-1"),
    ))
    with pytest.raises(SyntheticStartupLeaseRejected, match="blocked, degraded"):
        _review(state)


def test_wrong_startup_schema_denies(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[4] = (SyntheticReadinessRequirement("memory", "memory-2"),)
    with pytest.raises(SyntheticStartupLeaseRejected, match="schema-stale"):
        _review(state)


def test_changed_trigger_policy_revision_denies(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[1] = replace(state[1], policy_revision="policy-v2")
    with pytest.raises(SyntheticTriggerRejected, match="mismatched"):
        _review(state)


def test_stale_observation_denies(tmp_path: Path):
    with pytest.raises(SyntheticTriggerRejected, match="stale"):
        _review(_fixture(tmp_path), now_ms=101)


def test_expired_startup_lease_denies(tmp_path: Path):
    with pytest.raises(SyntheticStartupLeaseRejected, match="expired"):
        _review(_fixture(tmp_path), now_ms=104, max_startup_age_ms=5)


@pytest.mark.parametrize("bad", [True, -1, 2**63, "100"])
def test_wrong_now_type_or_clock_denies(tmp_path: Path, bad):
    with pytest.raises((SyntheticStartupLeaseRejected, SyntheticTriggerRejected)):
        _review(_fixture(tmp_path), now_ms=bad)


def test_late_unrelated_trigger_append_is_detected(tmp_path: Path, monkeypatch):
    import ark.proactive_startup_fence_review as module

    state = _fixture(tmp_path)
    original = module.review_prepared_trigger_freshness
    count = 0

    def injected(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 1:
            other = replace(state[1], definition_id="other")
            state[0].prepare(
                other, source_digest="c" * 64, observation_digest="d" * 64,
                observed_at_ms=90, now_ms=100,
            )
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", injected)
    with pytest.raises(SyntheticProactiveStartupRejected, match="changed"):
        _review(state)


def test_snapshot_reflectively_changed_mid_read_is_denied(tmp_path: Path, monkeypatch):
    import ark.proactive_startup_fence_review as module

    state = _fixture(tmp_path)
    original = module.review_prepared_trigger_freshness

    def injected(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(state[3].components[0], "schema_revision", "tampered")
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", injected)
    with pytest.raises(SyntheticStartupLeaseRejected, match="integrity"):
        _review(state)


def test_missing_trigger_store_is_not_recreated(tmp_path: Path):
    state = _fixture(tmp_path)
    missing = tmp_path / "missing-trigger.sqlite"
    state[0].path = missing
    with pytest.raises(sqlite3.OperationalError):
        _review(state)
    assert not missing.exists()


def test_invalid_policy_and_requirement_carriers_fail_closed(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[4] = list(state[4])
    with pytest.raises(SyntheticProactiveStartupRejected, match="exact"):
        _review(state)
    state[4] = ("memory",)
    with pytest.raises(SyntheticProactiveStartupRejected, match="exact"):
        _review(state)
