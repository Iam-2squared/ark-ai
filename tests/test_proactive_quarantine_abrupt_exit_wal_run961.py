"""Run961: cold proactive quarantine cannot infer a safe retry after child exit.

All schedules and clocks are synthetic. A local reconstructed SQLite digest is
not independent provenance, consent, a trusted clock, or notification authority.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineWitness,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


@pytest.mark.parametrize("commit_before_exit", (False, True))
@pytest.mark.parametrize("checkpoint", ("PASSIVE", "TRUNCATE"))
def test_abrupt_exit_quarantine_prefix_never_authorizes_replay(
    tmp_path, commit_before_exit: bool, checkpoint: str,
) -> None:
    path = tmp_path / "synthetic-quarantine.sqlite3"
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)
    DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    original = genesis_quarantine_witness(policy)

    child = """
import os
import sys
from pathlib import Path
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger, QuarantinePolicy,
    derive_quarantined_occurrence, genesis_quarantine_witness,
)
policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)
ledger = DisconnectedScheduleQuarantineLedger(Path(sys.argv[1]), policy=policy)
if sys.argv[2] == "yes":
    ledger.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=genesis_quarantine_witness(policy),
    )
os._exit(37)
"""
    completed = subprocess.run(
        [
            sys.executable, "-c", child, str(path),
            "yes" if commit_before_exit else "no",
        ],
        text=True, capture_output=True, timeout=30, check=False,
    )
    assert completed.returncode == 37, completed.stderr

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT seq,occurrence_id,chain_sha256 FROM quarantines ORDER BY seq"
        ).fetchall()
        assert len(rows) == int(commit_before_exit)
        assert conn.execute(
            f"PRAGMA wal_checkpoint({checkpoint})"
        ).fetchone()[0] == 0
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)

    cold = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    if commit_before_exit:
        assert rows[0][0] == 1
        assert rows[0][1] == derive_quarantined_occurrence(policy, 0)
        with pytest.raises(ScheduleQuarantineRejected, match="stale"):
            cold.inspect(retained=original)
        with pytest.raises(ScheduleQuarantineRejected, match="stale"):
            cold.quarantine_expired(
                index=0, occurrence_id=rows[0][1],
                observed_ms=10_502, retained=original,
            )
        # This witness is deliberately reconstructed from the SAME database
        # for a read-only diagnostic. It proves neither independent retention
        # nor permission to reconstruct an external side effect.
        local_only = QuarantineWitness(1, rows[0][2])
        assert cold.inspect(retained=local_only) == local_only
        assert local_only.independently_authenticated is False
    else:
        assert cold.inspect(retained=original) == original

    # Cold inspection must not introduce an event or silently retry a slot.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT seq,occurrence_id,chain_sha256 FROM quarantines ORDER BY seq"
        ).fetchall() == rows
