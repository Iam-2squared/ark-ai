"""Run963: finite recurrence quarantine remains terminal after cold restarts.

Only deterministic fixture occurrences are used: a quarantined occurrence
never authorizes notification, execution, replay, or a trusted clock.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


@pytest.mark.parametrize("length", (1, 2, 3))
@pytest.mark.parametrize("checkpoint", ("PASSIVE", "TRUNCATE"))
def test_finite_schedule_exhaustion_persists_without_cursor_rewind(
    tmp_path, length: int, checkpoint: str,
) -> None:
    path = tmp_path / "synthetic-finite-schedule.sqlite"
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, length, 500)
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    retained = genesis_quarantine_witness(policy)
    original = retained

    for index in range(length):
        occurrence = derive_quarantined_occurrence(policy, index)
        observed = 10_501 + 5_000 * index
        # An out-of-order observation never skips an earlier occurrence,
        # even if the named later slot is well past its synthetic deadline.
        if index + 1 < length:
            with pytest.raises(ScheduleQuarantineRejected):
                ledger.quarantine_expired(
                    index=index + 1,
                    occurrence_id=derive_quarantined_occurrence(policy, index + 1),
                    observed_ms=observed + 5_000,
                    retained=retained,
                )
        receipt = ledger.quarantine_expired(
            index=index,
            occurrence_id=occurrence,
            observed_ms=observed,
            retained=retained,
        )
        assert receipt.quarantined_index == index
        assert receipt.execution_authorized is False
        assert receipt.notification_authorized is False
        assert receipt.automatic_replay_authorized is False
        assert receipt.consent_verified is False
        assert receipt.trusted_clock_verified is False
        next_witness = receipt.witness
        assert next_witness.count == index + 1
        with pytest.raises(ScheduleQuarantineRejected):
            ledger.inspect(retained=retained)
        retained = next_witness
        # A reopened, read-only inspection preserves exactly the committed
        # prefix and never advances or re-dispatches a schedule cursor.
        cold = DisconnectedScheduleQuarantineLedger(path, policy=policy)
        assert cold.inspect(retained=retained) == retained

    with pytest.raises(ScheduleQuarantineRejected):
        ledger.quarantine_expired(
            index=length - 1,
            occurrence_id=derive_quarantined_occurrence(policy, length - 1),
            observed_ms=20_000 + 5_000 * length,
            retained=retained,
        )
    with pytest.raises(ScheduleQuarantineRejected):
        ledger.inspect(retained=original)

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"PRAGMA wal_checkpoint({checkpoint})"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT seq FROM quarantines ORDER BY seq"
        ).fetchall() == [(index,) for index in range(1, length + 1)]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    final = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert final.inspect(retained=retained) == retained
    assert retained.independently_authenticated is False
