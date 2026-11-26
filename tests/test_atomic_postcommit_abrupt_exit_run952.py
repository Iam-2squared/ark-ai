"""Run952: abrupt child-process exit after COMMIT must not permit replay.

The child writes only a disposable disconnected intent+audit SQLite fixture.
A parent reconstruction of its local hash is NOT independent custody, an
authenticated receipt, a trusted clock or a real exactly-once outcome.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


@pytest.mark.parametrize("committed_count", (1, 2, 3))
def test_cold_child_exit_after_audited_commit_cannot_automatically_replay(
    tmp_path, committed_count: int,
) -> None:
    path = tmp_path / "synthetic-child-abrupt-exit.sqlite3"
    script = """
import os
import sys
from pathlib import Path
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim, DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
ledger = DisconnectedAtomicPreactionLedger.create(Path(sys.argv[1]))
witness = genesis_atomic_preaction_witness()
for letter in "abc"[:int(sys.argv[2])]:
    claim = AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )
    witness = ledger.reserve(claim, retained=witness)
os._exit(29)
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(path), str(committed_count)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert process.returncode == 29, process.stderr

    with sqlite3.connect(path) as conn:
        intent_rows = conn.execute(
            "SELECT * FROM intents ORDER BY seq"
        ).fetchall()
        audit_rows = conn.execute(
            "SELECT * FROM preaction_audit ORDER BY seq"
        ).fetchall()
    assert len(intent_rows) == len(audit_rows) == committed_count
    assert [row[0] for row in intent_rows] == list(
        range(1, committed_count + 1)
    )
    assert [row[1] for row in intent_rows] == [
        _claim(letter).occurrence_id for letter in "abc"[:committed_count]
    ]

    cold = DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        cold.reserve(
            _claim("d"), retained=genesis_atomic_preaction_witness(),
        )
    # Derived from the *same local DB*: useful for synthetic consistency
    # checking but explicitly insufficient as an independent replay witness.
    local_only = AtomicPreactionWitness(
        committed_count, intent_rows[-1][4],
    )
    snapshot = cold.inspect(local_only)
    assert snapshot.occurrence_ids == tuple(
        _claim(letter).occurrence_id for letter in "abc"[:committed_count]
    )
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False
    with pytest.raises(AtomicPreactionRejected):
        cold.reserve(_claim("a"), retained=local_only)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM intents ORDER BY seq"
        ).fetchall() == intent_rows
        assert conn.execute(
            "SELECT * FROM preaction_audit ORDER BY seq"
        ).fetchall() == audit_rows
