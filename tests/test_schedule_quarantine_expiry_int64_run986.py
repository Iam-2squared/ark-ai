"""Synthetic overdue quarantine cannot accept an unrepresentable int64 expiry.

No trusted-clock, real scheduling, consent, replay or execution authority.
"""

from __future__ import annotations

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)

_MAX = 2**63 - 1


@pytest.mark.parametrize(
    ("first", "interval", "count", "grace"),
    (
        (_MAX, 1_000, 1, 0),
        (_MAX - 1_000, 1_000, 2, 0),
        (_MAX - 1_001, 1_000, 2, 1),
        (_MAX - 500, 1_000, 1, 500),
    ),
)
def test_unrepresentable_expiry_denied_before_sqlite_create(
    tmp_path, first: int, interval: int, count: int, grace: int,
) -> None:
    path = tmp_path / "unrepresentable-quarantine.sqlite"
    policy = QuarantinePolicy("a" * 64, first, interval, count, grace)
    with pytest.raises(ScheduleQuarantineRejected, match="invalid bounded synthetic"):
        DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    assert not path.exists()


def test_last_representable_expiry_remains_inert_and_durable(tmp_path) -> None:
    policy = QuarantinePolicy("a" * 64, _MAX - 2, 1_000, 1, 1)
    path = tmp_path / "last-representable-quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    prior = genesis_quarantine_witness(policy)
    receipt = ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=_MAX, retained=prior,
    )
    assert receipt.quarantined_index == 0
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert reopened.inspect(retained=receipt.witness) == receipt.witness
