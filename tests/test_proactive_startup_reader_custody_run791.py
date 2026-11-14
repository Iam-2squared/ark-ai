"""Run791: proactive callback fault injection cannot evade source epoch.

These synthetic reviewers intentionally retain injectable callback seams for
independent read-race tests. A matching local result never grants notification,
trusted time, replay, external effects or real ToolBackend dispatch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.proactive_startup_fence_review as proactive
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def _fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "run791-startup.sqlite")
    policy = SyntheticTriggerPolicy(
        "PRIVATE-OWNER", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64,
        observation_digest="b" * 64, observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent("scheduler", ("memory",), schema_revision="scheduler-1"),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, receipt, policy, snapshot, requirements


def _review(state):
    ledger, receipt, policy, snapshot, requirements = state
    return proactive.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64,
        observation_digest="b" * 64,
        captured_at_ms=98,
        now_ms=100,
        max_startup_age_ms=5,
        max_observation_age_ms=10,
    )


@pytest.mark.parametrize(
    "reader",
    ("review_synthetic_startup_lease", "review_prepared_trigger_freshness"),
)
def test_fault_injected_reader_cannot_swap_equal_local_source(
    tmp_path: Path, reader: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _fixture(tmp_path)
    original = getattr(proactive, reader)
    callbacks: list[str] = []

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        callbacks.append(reader)
        state[0].path = Path(str(state[0].path))
        return result

    with monkeypatch.context() as patch:
        patch.setattr(proactive, reader, changed)
        with pytest.raises(
            proactive.SyntheticProactiveStartupRejected,
            match="input, source or retained evidence changed",
        ):
            _review(state)
    assert callbacks == [reader]


def test_original_local_proactive_readers_remain_denial_only(tmp_path: Path) -> None:
    report = _review(_fixture(tmp_path))
    assert report.checked_at_ms == 100
    assert report.startup_authorized is False
    assert report.notification_authorized is False
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
