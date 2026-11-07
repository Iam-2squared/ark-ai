"""Final proactive callback cannot rewrite an already-reviewed readiness graph."""

from pathlib import Path

import pytest

from ark.proactive_startup_fence_review import (
    SyntheticProactiveStartupRejected,
    review_synthetic_proactive_startup,
)
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger # %.sqlite")
    policy = SyntheticTriggerPolicy(
        "OWNER-PRIVATE", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent(
            "scheduler", ("memory",), schema_revision="scheduler-v1",
        ),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-v1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-v1"),
    )
    return ledger, policy, receipt, snapshot, requirements


def review(state):
    ledger, policy, receipt, snapshot, requirements = state
    return review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100,
        max_startup_age_ms=5, max_observation_age_ms=10,
    )


def test_normal_startup_state_never_grants_action(tmp_path: Path):
    receipt = review(fixture(tmp_path))
    assert receipt.startup_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert "OWNER-PRIVATE" not in repr(receipt)


@pytest.mark.parametrize(("field", "replacement"), [
    ("schema_revision", "injected-schema"),
    ("effective_state", ReadinessState.BLOCKED),
    ("failure_code", "new-failure"),
    ("dependencies", ("scheduler",)),
])
def test_reflective_change_after_last_readiness_check_is_denied(
    tmp_path: Path, monkeypatch, field: str, replacement,
):
    import ark.proactive_startup_fence_review as module

    state = fixture(tmp_path)
    original = module.review_prepared_trigger_freshness
    calls = 0

    def injected(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 2:
            object.__setattr__(state[3].components[0], field, replacement)
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", injected)
    with pytest.raises(SyntheticProactiveStartupRejected, match="changed"):
        review(state)


def test_late_reflection_of_requirement_is_detected(tmp_path: Path, monkeypatch):
    import ark.proactive_startup_fence_review as module

    state = fixture(tmp_path)
    original = module.review_prepared_trigger_freshness
    calls = 0

    def injected(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 2:
            object.__setattr__(state[4][0], "schema_revision", "forged")
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", injected)
    with pytest.raises(SyntheticProactiveStartupRejected, match="changed"):
        review(state)
