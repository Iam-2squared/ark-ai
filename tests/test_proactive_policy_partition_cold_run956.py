"""Run956: disconnected trigger scope and policy partitions survive restart.

The fixture stores only synthetic local digests/preparation markers. Neither
successful persistence nor timing admission implies consent, trusted time,
notifications, external tools or automatic replay authority.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "fixture-owner", "private", "daily-summary", 1,
        "policy-v1", 100, 1_000, 5,
    )


def _prepare(
    ledger: SyntheticProactiveLedger, policy: SyntheticTriggerPolicy, *,
    source: str = "a" * 64, now: int = 1_000,
):
    return ledger.prepare(
        policy, source_digest=source, observation_digest="f" * 64,
        observed_at_ms=900, now_ms=now,
    )


@pytest.mark.parametrize(("field", "replacement"), (
    ("owner", "other-owner"),
    ("namespace", "other-private"),
    ("definition_id", "weekly-summary"),
    ("revision", 2),
    ("policy_revision", "policy-v2"),
))
def test_policy_identity_partitions_local_rate_limit_without_grants(
    tmp_path, field: str, replacement: object,
) -> None:
    path = tmp_path / "synthetic-partitioned-trigger.sqlite"
    ledger = SyntheticProactiveLedger(path)
    primary = _policy()
    separate = replace(primary, **{field: replacement})
    original = _prepare(ledger, primary)
    partitioned = _prepare(ledger, separate)
    assert original.trigger_id != partitioned.trigger_id
    assert original.prepared_at_ms == partitioned.prepared_at_ms == 1_000
    assert ledger.count() == 2

    cold = SyntheticProactiveLedger(path)
    with pytest.raises(SyntheticTriggerRejected):
        _prepare(cold, primary)
    with pytest.raises(SyntheticTriggerRejected):
        _prepare(cold, separate)
    assert cold.count() == 2
    # Distinct source creates another local marker only after the interval;
    # it never sends a notification or executes a task.
    advanced = _prepare(cold, primary, source="b" * 64, now=1_100)
    assert advanced.trigger_id not in {original.trigger_id, partitioned.trigger_id}
    assert cold.count() == 3
    for receipt in (original, partitioned, advanced):
        assert receipt.notification_authorized is False
        assert receipt.dispatch_authorized is False
        assert receipt.automatic_replay_authorized is False


def test_later_cold_process_cannot_reuse_identical_trigger_identity(
    tmp_path,
) -> None:
    ledger = SyntheticProactiveLedger(tmp_path / "synthetic-repeat.sqlite")
    original = _prepare(ledger, _policy())
    assert original.notification_authorized is False
    reopened = SyntheticProactiveLedger(ledger.path)
    with pytest.raises(SyntheticTriggerRejected):
        _prepare(reopened, _policy(), now=1_100)
    assert reopened.count() == 1
