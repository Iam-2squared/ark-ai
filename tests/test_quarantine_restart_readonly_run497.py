"""Existing synthetic quarantine startup must never take a SQLite writer slot."""

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


def test_existing_restart_is_readonly_even_during_another_writer_reservation(tmp_path):
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "schedule.sqlite"
    DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    witness = genesis_quarantine_witness(policy)
    writer = sqlite3.connect(path, timeout=0.5, isolation_level=None)
    writer.execute("BEGIN IMMEDIATE")
    try:
        # An existing-ledger constructor must not request BEGIN IMMEDIATE.
        # A RESERVED writer and an ordinary SQLite read transaction can coexist.
        restarted = DisconnectedScheduleQuarantineLedger(path, policy=policy)
        assert restarted.inspect(retained=witness) == witness
        assert writer.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (0,)
    finally:
        writer.rollback()
        writer.close()

    # A later explicit, bounded append retains its separate write transaction.
    receipt = restarted.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=witness,
    )
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.automatic_replay_authorized is False


def test_restart_of_missing_quarantine_ledger_never_creates_database(tmp_path):
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "not-created.sqlite"
    with pytest.raises(ScheduleQuarantineRejected, match="missing"):
        DisconnectedScheduleQuarantineLedger(path, policy=policy, create=False)
    assert not path.exists()
