"""Independent synthetic trigger/readiness checks must not hide input drift.

The fixtures neither emit notifications nor authorize actual Tool execution.
"""

from pathlib import Path

import pytest

import ark.proactive_startup_fence_review as module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
)
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def _fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline-owner", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent(
            "scheduler", dependencies=("memory",), schema_revision="scheduler-1",
        ),
    ))
    required = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, policy, receipt, snapshot, required


def _review(state):
    ledger, policy, receipt, snapshot, required = state
    return module.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, required,
        source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100,
        max_startup_age_ms=5, max_observation_age_ms=10,
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "policy-value",
        "policy-equal-carrier",
        "receipt-value",
        "receipt-equal-carrier",
        "requirement-value",
        "requirement-equal-carrier",
    ),
)
def test_first_ready_callback_drift_is_rejected_before_trigger_restores_it(
    tmp_path: Path, monkeypatch, mutation,
):
    state = _fixture(tmp_path)
    policy, receipt, required = state[1], state[2], state[4]
    if mutation.startswith("policy"):
        target, attr = policy, "policy_revision"
        new_value = (
            "retargeted-policy" if mutation == "policy-value"
            else policy.policy_revision.encode("ascii").decode("ascii")
        )
    elif mutation.startswith("receipt"):
        target, attr = receipt, "trigger_id"
        new_value = (
            "trigger_" + "c" * 64 if mutation == "receipt-value"
            else receipt.trigger_id.encode("ascii").decode("ascii")
        )
    else:
        target, attr = required[0], "schema_revision"
        new_value = (
            "retargeted-schema" if mutation == "requirement-value"
            else required[0].schema_revision.encode("ascii").decode("ascii")
        )
    original_value = getattr(target, attr)
    if "equal-carrier" in mutation:
        assert new_value == original_value and new_value is not original_value

    ready = module.review_synthetic_startup_lease
    freshness = module.review_prepared_trigger_freshness
    calls = []

    def alter_after_readiness(*args, **kwargs):
        result = ready(*args, **kwargs)
        if not calls:
            object.__setattr__(target, attr, new_value)
            calls.append("mutated")
        return result

    def later_restoration(*args, **kwargs):
        calls.append("restored")
        object.__setattr__(target, attr, original_value)
        return freshness(*args, **kwargs)

    monkeypatch.setattr(module, "review_synthetic_startup_lease", alter_after_readiness)
    monkeypatch.setattr(module, "review_prepared_trigger_freshness", later_restoration)
    with pytest.raises(module.SyntheticProactiveStartupRejected, match="input"):
        _review(state)
    assert calls == ["mutated"]


def test_unmodified_proactive_startup_remains_diagnostic_only(tmp_path: Path):
    result = _review(_fixture(tmp_path))
    assert result.trigger_history_digest.startswith("synthetic_triggers_")
    assert result.startup_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
