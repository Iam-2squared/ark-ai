"""Quarantine persisted IDs use byte lengths, not Unicode codepoint counts."""

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


def _seed(tmp_path):
    path = tmp_path / "quarantine.sqlite"
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)
    ledger = DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    initial = genesis_quarantine_witness(policy)
    first = ledger.quarantine_expired(
        index=0, occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501, retained=initial,
    )
    return path, policy, first.witness


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("occurrence_id", "é" * 69),
        ("chain_sha256", "é" * 64),
        ("occurrence_id", sqlite3.Binary(b"x" * 69)),
        ("chain_sha256", sqlite3.Binary(b"x" * 64)),
    ),
)
def test_quarantined_identifiers_refuse_bad_byte_width_before_row_read(
    tmp_path, column, replacement,
):
    path, policy, retained = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            f"UPDATE quarantines SET {column}=? WHERE seq=1",
            (replacement,),
        ).rowcount == 1
    with pytest.raises(ScheduleQuarantineRejected, match="storage type or width"):
        DisconnectedScheduleQuarantineLedger(path, policy=policy)
    with pytest.raises(ScheduleQuarantineRejected, match="storage type or width"):
        DisconnectedScheduleQuarantineLedger(
            path, policy=policy, create=False,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


def test_valid_ascii_quarantine_prefix_keeps_restart_and_denial(tmp_path):
    path, policy, retained = _seed(tmp_path)
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert reopened.inspect(retained=retained) == retained
    assert retained.independently_authenticated is False
