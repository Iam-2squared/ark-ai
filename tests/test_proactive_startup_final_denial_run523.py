"""Last authority boundary on disconnected proactive startup probes.

Prepared trigger and READY fixtures grant no notification, execution or replay.
"""

from __future__ import annotations

import pytest

from ark import proactive_startup_fence_review as mod
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def scenario(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    policy = SyntheticTriggerPolicy(
        "synthetic", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent(
            "scheduler", ("memory",), schema_revision="scheduler-1",
        ),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, receipt, policy, snapshot, requirements


def invoke(case):
    return mod.review_synthetic_proactive_startup(
        *case, source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100, max_startup_age_ms=5,
        max_observation_age_ms=10,
    )


def test_unchanged_local_result_is_diagnostic_only(tmp_path):
    outcome = invoke(scenario(tmp_path))
    assert outcome.startup_authorized is False
    assert outcome.notification_authorized is False
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False


@pytest.mark.parametrize("field", [
    "startup_authorized",
    "notification_authorized",
    "dispatch_authorized",
    "automatic_replay_authorized",
])
@pytest.mark.parametrize("forged", [True, 1])
def test_non_false_authority_is_never_accepted(
    tmp_path, monkeypatch, field, forged,
):
    case = scenario(tmp_path)
    monkeypatch.setattr(
        mod.SyntheticProactiveStartupReview,
        field, property(lambda self: forged),
    )
    with pytest.raises(mod.SyntheticProactiveStartupRejected, match="authority"):
        invoke(case)


@pytest.mark.parametrize("target,field,replacement", [
    ("result", "trigger_id", "trigger_" + "f" * 64),
    ("result", "readiness_digest", "f" * 64),
    ("result", "trigger_history_digest", "synthetic_triggers_" + "f" * 64),
    ("result", "checked_at_ms", 999),
    ("receipt", "trigger_id", "trigger_" + "f" * 64),
    ("policy", "policy_revision", "mutated"),
    ("snapshot", "digest", "forged"),
])
def test_false_last_getter_cannot_mutate_witness_or_source(
    tmp_path, monkeypatch, target, field, replacement,
):
    case = scenario(tmp_path)

    def late_false(self):
        obj = self if target == "result" else {
            "receipt": case[1], "policy": case[2], "snapshot": case[3],
        }[target]
        object.__setattr__(obj, field, replacement)
        return False

    monkeypatch.setattr(
        mod.SyntheticProactiveStartupReview,
        "automatic_replay_authorized",
        property(late_false),
    )
    with pytest.raises(
        mod.SyntheticProactiveStartupRejected,
        match="changed|input|witness|authority",
    ):
        invoke(case)
