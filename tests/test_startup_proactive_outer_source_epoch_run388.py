"""Startup/readiness cross-pass review must not adopt a redirected trigger DB.

Synthetic local triggers cannot grant notifications or Tool execution.
"""

from pathlib import Path

import pytest

import ark.proactive_startup_fence_review as module
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def _fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger # %.sqlite")
    policy = SyntheticTriggerPolicy(
        "PRIVATE-OWNER", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
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


def _review(state, retained=None):
    ledger, policy, receipt, snapshot, requirements = state
    return module.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100,
        max_startup_age_ms=5, max_observation_age_ms=10, retained=retained,
    )


@pytest.mark.parametrize(
    ("hook", "after_call"),
    [
        ("review_synthetic_startup_lease", 1),
        ("review_prepared_trigger_freshness", 1),
        ("review_synthetic_startup_lease", 2),
        ("review_prepared_trigger_freshness", 2),
    ],
)
def test_equal_string_path_swap_after_each_independent_pass_is_denied(
    tmp_path: Path, monkeypatch, hook: str, after_call: int,
):
    state = _fixture(tmp_path)
    original = getattr(module, hook)
    calls = 0

    def redirected(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == after_call:
            state[0].path = Path(str(state[0].path))
        return result

    monkeypatch.setattr(module, hook, redirected)
    with pytest.raises(module.SyntheticProactiveStartupRejected, match="source"):
        _review(state)
    assert calls == after_call


def test_reflected_retained_trigger_history_swap_is_denied(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    witness = read_proactive_witness(state[0])
    original = module.review_prepared_trigger_freshness
    calls = 0

    def mutate_retained(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 2:
            object.__setattr__(witness, "digest", "synthetic_triggers_" + "f" * 64)
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", mutate_retained)
    with pytest.raises(module.SyntheticProactiveStartupRejected, match="retained"):
        _review(state, retained=witness)
    assert calls == 2


def test_stable_retained_history_never_grants_dispatch(tmp_path: Path):
    state = _fixture(tmp_path)
    review = _review(state, retained=read_proactive_witness(state[0]))
    assert review.startup_authorized is False
    assert review.notification_authorized is False
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert "PRIVATE-OWNER" not in repr(review)
