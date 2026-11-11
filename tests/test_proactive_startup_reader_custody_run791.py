"""Run791: deny substituted startup/trigger readers before private access.

A synthetic READY lease is never verified consent, delivery authorization,
trusted time, or permission for real ToolBackend dispatch.
"""

from __future__ import annotations

import pytest

import ark.proactive_startup_fence_review as proactive
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
)
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import (
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize(
    "reader",
    ("review_synthetic_startup_lease", "review_prepared_trigger_freshness"),
)
def test_startup_review_denies_replaced_reader_before_private_fields(
    reader: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[str] = []

    def untrusted(*_args: object, **_kwargs: object) -> object:
        invoked.append(reader)
        raise AssertionError("unreviewed private startup callback invoked")

    with monkeypatch.context() as patch:
        patch.setattr(proactive, reader, untrusted)
        ledger = object.__new__(SyntheticProactiveLedger)
        receipt = object.__new__(SyntheticTriggerReceipt)
        policy = object.__new__(SyntheticTriggerPolicy)
        snapshot = object.__new__(StartupSnapshot)
        with pytest.raises(
            proactive.SyntheticProactiveStartupRejected,
            match="authority descriptor epoch changed",
        ):
            proactive.review_synthetic_proactive_startup(
                ledger, receipt, policy, snapshot, (),
                source_digest="a" * 64,
                observation_digest="b" * 64,
                captured_at_ms=98,
                now_ms=100,
                max_startup_age_ms=5,
                max_observation_age_ms=10,
            )
    assert not invoked


def test_original_local_proactive_readers_still_deny_external_effects(tmp_path) -> None:
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
    report = proactive.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64,
        observation_digest="b" * 64,
        captured_at_ms=98,
        now_ms=100,
        max_startup_age_ms=5,
        max_observation_age_ms=10,
    )
    assert report.checked_at_ms == 100
    assert report.startup_authorized is False
    assert report.notification_authorized is False
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
