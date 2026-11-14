"""Policy prehydration budget for synthetic expired-slot quarantine."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.disconnected_schedule_quarantine_ledger as quarantine


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("policy_sha256", "x" * 200_000),
        ("policy_sha256", sqlite3.Binary(b"synthetic-blob")),
        ("first_ms", sqlite3.Binary(b"synthetic-blob")),
        ("interval_ms", sqlite3.Binary(b"synthetic-blob")),
        ("count", sqlite3.Binary(b"synthetic-blob")),
        ("grace_ms", sqlite3.Binary(b"synthetic-blob")),
    ),
)
def test_quarantine_policy_malformed_storage_rejected_before_hydration(
    tmp_path, column, value,
):
    policy = quarantine.QuarantinePolicy(
        policy_sha256="a" * 64,
        first_ms=10_000,
        interval_ms=5000,
        count=3,
        grace_ms=500,
    )
    db = tmp_path / "quarantine.sqlite"
    store = quarantine.DisconnectedScheduleQuarantineLedger(
        db, policy=policy, create=True,
    )
    with sqlite3.connect(db) as conn:
        conn.execute(f"UPDATE policy SET {column}=?", (value,))

    with closing(sqlite3.connect(db)) as conn:
        conn.execute("BEGIN")

        class NoPolicyHydration:
            def execute(self, sql, *parameters):
                if sql == "SELECT * FROM policy":
                    raise AssertionError("oversized persisted policy hydrated")
                return conn.execute(sql, *parameters)

        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="policy hydration admission",
        ):
            quarantine._validate(NoPolicyHydration(), store._epoch)
        conn.rollback()
    assert db.exists()


def test_original_quarantine_genesis_remains_recoverable(tmp_path):
    policy = quarantine.QuarantinePolicy(
        policy_sha256="a" * 64,
        first_ms=10_000,
        interval_ms=5000,
        count=3,
        grace_ms=500,
    )
    db = tmp_path / "quarantine.sqlite"
    store = quarantine.DisconnectedScheduleQuarantineLedger(
        db, policy=policy, create=True,
    )
    genesis = quarantine.genesis_quarantine_witness(policy)
    assert store.inspect(retained=genesis) == genesis
    reopened = quarantine.DisconnectedScheduleQuarantineLedger(db, policy=policy)
    assert reopened.inspect(retained=genesis) == genesis
